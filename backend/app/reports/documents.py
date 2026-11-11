from typing import Literal

from pydantic import Field

from app.core.security import ResourcePolicy
from app.schemas.common import Contract, Language, SourceReference


class DocumentMetadata(Contract):
    title: str = Field(min_length=1, max_length=300)
    language: Language
    publisher: str = Field(default='', max_length=300)
    issued_on: str = Field(default='', max_length=40)


class Passage(Contract):
    chunk_id: str
    document_id: str
    version: int
    page_start: int
    page_end: int
    text: str
    language: Language
    extraction_method: Literal['text', 'ocr'] = 'text'
    ocr_confidence: float | None = None


class DocumentRecord(Contract):
    document_id: str
    version: int
    sha256: str
    metadata: DocumentMetadata
    policy: ResourcePolicy
    passages: list[Passage]
    warnings: list[str]
    processing_signature: str = 'text-v1'


class Evidence(Contract):
    passage: Passage
    source: SourceReference
    distance: float


class EvidenceResult(Contract):
    evidence: list[Evidence]
    warnings: list[str]


def reference(doc: DocumentRecord, passage: Passage) -> SourceReference:
    # source_id identifie le passage, donc le texte cité est retrouvable sans champ partagé supplémentaire.
    return SourceReference(source_id=passage.chunk_id, source_type='document',
                           name=doc.metadata.title, version=str(doc.version), fields=[],
                           pages=list(range(passage.page_start, passage.page_end + 1)))
