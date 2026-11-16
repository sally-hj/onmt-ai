import hashlib
import io
import re
from collections import Counter
from threading import RLock
from uuid import uuid4

import pdfplumber

from app.core.errors import AppError, forbidden
from app.core.security import authorize, can_read, private_policy, require_module
from .documents import DocumentMetadata, DocumentRecord, Passage
from .ocr import LocalOCR


class DocumentService:
    def __init__(self, store, index, settings):
        self.store, self.index, self.settings = store, index, settings
        self.lock = RLock()
        self.ocr = LocalOCR(settings)

    def reindex(self, access_context):
        require_module(access_context, True)
        if 'document_editor' not in access_context.roles:
            raise forbidden()
        count=0
        with self.lock:
            for raw in self.store.documents():
                doc=DocumentRecord.model_validate(raw)
                if can_read(doc.policy,access_context) and doc.policy.owner_id==access_context.user_id:
                    try:
                        self.index.add(doc)
                        doc.index_identity=self.index.embedder.identity
                        with self.store.connect() as db:
                            db.execute('UPDATE documents SET payload=? WHERE id=? AND version=?',(doc.model_dump_json(),doc.document_id,doc.version))
                    except AppError:
                        raise
                    except Exception as exc:
                        raise AppError('tool_failed','Réindexation interrompue ; relancez après correction.',503) from exc
                    count+=1
        return count

    def ingest_pdf(self, content: bytes, metadata: DocumentMetadata, access_context, document_id=None):
        require_module(access_context, True)
        if 'document_editor' not in access_context.roles:
            raise forbidden()
        if len(content) > self.settings.max_pdf_bytes:
            raise AppError('invalid_request', 'PDF limité à 20 Mio.', 413)
        if not content.startswith(b'%PDF-'):
            raise AppError('invalid_request', 'Un PDF textuel est requis.', 422)
        with self.lock:
            return self._ingest(content, metadata, access_context, document_id)

    def _ingest(self, content, metadata, access, document_id):
        previous = self.store.document(document_id) if document_id else None
        if document_id and previous is None:
            raise forbidden()
        if previous:
            previous = DocumentRecord.model_validate(previous)
            authorize(previous.policy, access, True)
        digest = hashlib.sha256(content).hexdigest()
        signature = f'text-v2:ocr={self.settings.ocr_enabled}:langs={self.settings.ocr_languages}'
        for raw in self.store.documents():
            if raw['sha256'] == digest:
                doc = DocumentRecord.model_validate(raw)
                authorize(doc.policy, access, True)
                if document_id and doc.document_id != document_id:
                    raise AppError('invalid_request', 'Contenu déjà importé sous un autre identifiant.', 409)
                if doc.metadata != metadata:
                    raise AppError('invalid_request', 'Contenu identique : métadonnées différentes. Importez une nouvelle édition du PDF.', 409)
                if doc.processing_signature == signature or (not self.settings.ocr_enabled and doc.processing_signature == 'text-v1'):
                    return doc, True
                previous, document_id = doc, doc.document_id
                break
        origins, confidences, warnings = {}, {}, []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) > self.settings.max_pages:
                    raise AppError('invalid_request', 'PDF limité à 200 pages.', 422)
                pages = []
                for index, page in enumerate(pdf.pages):
                    text = (page.extract_text(layout=False) or '').replace('\x00', '')
                    scanned = not text.strip() or (bool(page.images) and len(re.sub(r'\W', '', text)) < 80)
                    method, confidence = 'text', None
                    if scanned and self.settings.ocr_enabled:
                        text, confidence, page_warnings = self.ocr.extract_page(content, index)
                        method = 'ocr'
                        warnings.extend(f'{w}:page={index+1}' for w in page_warnings)
                    origins[index+1], confidences[index+1] = method, confidence
                    pages.append((index+1, text))
        except AppError:
            raise
        except Exception as exc:
            raise AppError('invalid_request', 'PDF illisible, chiffré ou endommagé.', 422) from exc
        empty = [i for i,t in pages if not t.strip()]
        if not pages or len(empty) == len(pages):
            message = ('PDF sans texte exploitable après OCR ; contrôle manuel nécessaire.' if self.settings.ocr_enabled
                       else 'PDF sans texte exploitable, probablement scanné. OCR non implémenté dans ce mode désactivé.')
            raise AppError('missing_data', message, 422)
        if empty:
            warnings.append(f'{"ocr_empty" if self.settings.ocr_enabled else "ocr_not_available"}: pages sans texte {empty}')
        # Retrait des lignes de bord répétées ; les paragraphes restent dans leur page physique.
        borders = Counter(line.strip() for _,t in pages for line in (t.splitlines()[:1] + t.splitlines()[-1:]))
        repeated = {line for line,count in borders.items() if len(pages) >= 3 and count >= max(3, len(pages)*0.7)}
        doc_id = document_id or 'doc_' + uuid4().hex
        version = previous.version + 1 if previous else 1
        passages = []
        for page_no, text in pages:
            lines = [line.rstrip() for line in text.splitlines() if line.strip() not in repeated]
            cleaned = re.sub(r'[ \t]+', ' ', '\n'.join(lines)).strip()
            # 600 caractères + chevauchement, puis contrôle tokenizer avant l'indexation réelle.
            start = 0
            while start < len(cleaned):
                end = min(start + 600, len(cleaned))
                if end < len(cleaned):
                    split = cleaned.rfind(' ', start + 300, end)
                    if split > start:
                        end = split
                part = cleaned[start:end].strip()
                if part:
                    passages.append(Passage(chunk_id=f'{doc_id}:v{version}:p{page_no}:c{len(passages)+1}',
                                            document_id=doc_id, version=version, page_start=page_no, page_end=page_no,
                                            text=part, language=metadata.language, extraction_method=origins[page_no],
                                            ocr_confidence=confidences[page_no]))
                if end == len(cleaned):
                    break
                start = end - 60
        if not passages:
            raise AppError('missing_data', 'Aucun passage exploitable.', 422)
        doc = DocumentRecord(document_id=doc_id, version=version, sha256=digest, metadata=metadata,
                             policy=previous.policy if previous else private_policy(access), passages=passages,
                             warnings=warnings, processing_signature=signature)
        doc.index_identity=self.index.embedder.identity
        try:
            self.index.add(doc)
            self.store.save_document(doc.model_dump(mode='json'), content)
        except AppError:
            raise
        except Exception as exc:
            raise AppError('tool_failed', 'Import documentaire non enregistré ; vérifiez l’index local.', 503) from exc
        if previous:
            try:
                self.index.remove(previous)
            except Exception:
                # Vecteurs inaccessibles : les requêtes n'incluent que la version courante en SQLite.
                doc.warnings.append('stale_vectors_cleanup_required')
        self.store.audit(access.user_id, doc_id, 'document.import', doc_id)
        return doc, False
