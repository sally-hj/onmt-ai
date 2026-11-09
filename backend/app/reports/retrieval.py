import hashlib
import math
import re
from pathlib import Path
from typing import Protocol

from app.core.errors import AppError
from app.core.security import can_read, require_module
from .documents import DocumentRecord, Evidence, EvidenceResult, reference


class Embedder(Protocol):
    identity: str
    def encode(self, texts: list[str], query: bool = False) -> list[list[float]]: ...


class LocalSentenceEmbedder:
    def __init__(self, model_path: str, revision: str):
        self.path, self.revision = model_path, revision
        revision_file = Path(model_path) / 'ONMT_REVISION.txt'
        weights_revision = revision_file.read_text(encoding='ascii').strip() if revision_file.is_file() else 'operator-managed'
        self.identity = f'sentence-transformers:{model_path}:{revision}:{weights_revision}:e5-prefix-v1'
        self._model = None

    def encode(self, texts, query=False):
        try:
            if self._model is None:
                from app.core.runtime import prepare_torch_runtime
                prepare_torch_runtime()
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.path, local_files_only=True, trust_remote_code=False, device='cpu')
                import torch
                torch.set_num_threads(2)
            prefix = 'query: ' if query else 'passage: '
            inputs = [prefix + t for t in texts]
            # Aucun passage tronqué silencieusement : les références couvrent tout le texte indexé.
            if any(len(self._model.tokenizer.encode(t)) > self._model.max_seq_length for t in inputs):
                raise AppError('invalid_request', 'Passage trop long pour le modèle local ; réduisez le découpage.', 422)
            return self._model.encode(inputs, normalize_embeddings=True, show_progress_bar=False).tolist()
        except AppError:
            raise
        except Exception as exc:
            raise AppError('tool_failed', 'Modèle d’embeddings local indisponible. Configurez ONMT_EMBEDDING_MODEL.', 503) from exc


class DemoHashEmbedder:
    """Vecteurs lexicaux déterministes : tests/démo uniquement, aucune prétention sémantique."""
    identity = 'demo-hash-256-v1'

    def encode(self, texts, query=False):
        output = []
        for text in texts:
            vector = [0.0] * 256
            for word in re.findall(r'\w+', text.casefold()):
                bucket = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % len(vector)
                vector[bucket] += 1
            norm = math.sqrt(sum(v*v for v in vector)) or 1
            output.append([v/norm for v in vector])
        return output


class ChromaIndex:
    def __init__(self, directory, embedder):
        self.directory, self.embedder = directory, embedder
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(path=str(self.directory), settings=Settings(anonymized_telemetry=False))
            name = 'passages_' + hashlib.sha256(self.embedder.identity.encode()).hexdigest()[:20]
            self._collection = client.get_or_create_collection(name, embedding_function=None,
                                                               metadata={'hnsw:space': 'cosine'})
        return self._collection

    def add(self, doc: DocumentRecord):
        passages = doc.passages
        vectors = self.embedder.encode([p.text for p in passages])
        self.collection.upsert(ids=[p.chunk_id for p in passages], embeddings=vectors,
                               documents=[p.text for p in passages],
                               metadatas=[{'document_version': f'{doc.document_id}:{doc.version}'} for _ in passages])

    def remove(self, doc: DocumentRecord):
        self.collection.delete(where={'document_version': f'{doc.document_id}:{doc.version}'})

    def query(self, question, allowed_versions, limit):
        if not allowed_versions:
            return []
        result = self.collection.query(query_embeddings=self.embedder.encode([question], query=True),
                                        where={'document_version': {'$in': allowed_versions}},
                                        n_results=limit, include=['distances'])
        return list(zip(result['ids'][0], result['distances'][0]))


class Retriever:
    def __init__(self, store, index, max_distance=0.35):
        self.store, self.index, self.max_distance = store, index, max_distance

    def search_evidence(self, question, access_context, limit=5):
        require_module(access_context)
        docs = [DocumentRecord.model_validate(d) for d in self.store.documents()]
        docs = [d for d in docs if can_read(d.policy, access_context)]
        if not docs:
            return EvidenceResult(evidence=[], warnings=['documentary_evidence_absent'])
        lookup = {p.chunk_id: (d,p) for d in docs for p in d.passages}
        # Les documents interdits ne participent pas à la recherche, même au classement.
        try:
            matches = self.index.query(question, [f'{d.document_id}:{d.version}' for d in docs], limit)
        except AppError:
            raise
        except Exception as exc:
            raise AppError('tool_failed', 'La recherche documentaire locale a échoué.', 503) from exc
        evidence = []
        for chunk_id, distance in matches:
            if chunk_id in lookup and distance <= self.max_distance:
                doc, passage = lookup[chunk_id]
                evidence.append(Evidence(passage=passage, source=reference(doc, passage), distance=distance))
        warnings = [] if evidence else ['documentary_evidence_insufficient']
        if isinstance(self.index.embedder, DemoHashEmbedder):
            warnings.append('demo_embeddings_non_semantic')
        return EvidenceResult(evidence=evidence, warnings=warnings)
