from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from pydantic import Field

from app.core.errors import AppError, forbidden
from app.core.security import authorize, can_read, demo_access, require_module
from app.schemas.common import AccessContext, Contract
from app.schemas.report import ReportRequest, ReportResult, ReportRevisionRequest
from .documents import DocumentMetadata, DocumentRecord, EvidenceResult

router = APIRouter(prefix='/api', tags=['Salma — rapports et documents'])


def get_access_context(request: Request) -> AccessContext:
    """Point de branchement de l'authentification serveur de Hayat."""
    resolver = request.app.state.access_resolver
    if resolver is not None:
        access = AccessContext.model_validate(resolver(request))
    elif request.app.state.settings.demo:
        access = demo_access()
    else:
        raise AppError('forbidden', 'Authentification serveur non connectée. Accès refusé.', 401)
    require_module(access)
    return access


Access = Annotated[AccessContext, Depends(get_access_context)]


class SearchRequest(Contract):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


@router.get('/reports/config')
def config(request: Request, access: Access):
    settings = request.app.state.settings
    return {'demo': settings.demo, 'demo_embeddings': settings.demo_embeddings,
            'generation': 'synchronous', 'ollama_enabled': bool(settings.ollama_model)}


@router.post('/reports', response_model=ReportResult, status_code=201)
def create(body: ReportRequest, request: Request, access: Access):
    request.state.request_id = body.request_id
    return request.app.state.reports.create_report(body, access)


@router.get('/reports', response_model=list[ReportResult])
def listing(request: Request, access: Access):
    return request.app.state.reports.list_reports(access)


@router.get('/reports/{report_id}', response_model=ReportResult)
def read(report_id: str, request: Request, access: Access, version: int | None = Query(default=None, gt=0)):
    return request.app.state.reports.get_report(report_id, access, version)


@router.patch('/reports/{report_id}/sections/{section_id}', response_model=ReportResult)
def revise(report_id: str, section_id: str, body: ReportRevisionRequest, request: Request, access: Access):
    request.state.request_id = body.request_id
    if report_id != body.report_id or section_id != body.section_id:
        raise AppError('invalid_request', 'Identifiants du chemin et du corps incohérents.', 422)
    return request.app.state.reports.revise_report(body, access)


@router.post('/reports/{report_id}/export', response_model=ReportResult)
def export(report_id: str, request: Request, access: Access, version: int | None = Query(default=None, gt=0)):
    return request.app.state.reports.export_pdf(report_id, access, request.app.state.exporter, version)


@router.get('/reports/{report_id}/pdf')
def download(report_id: str, request: Request, access: Access, version: int | None = Query(default=None, gt=0)):
    pdf = request.app.state.reports.download_pdf(report_id, access, version)
    return Response(pdf, media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="rapport.pdf"',
                                                               'Cache-Control': 'no-store'})


@router.post('/documents/search', response_model=EvidenceResult)
def search(body: SearchRequest, request: Request, access: Access):
    return request.app.state.retriever.search_evidence(body.question, access, body.limit)


@router.post('/documents/reindex')
def reindex(request: Request, access: Access):
    return {'indexed_documents': request.app.state.documents.reindex(access)}


@router.get('/documents')
def documents(request: Request, access: Access):
    result = []
    for raw in request.app.state.store.documents():
        doc = DocumentRecord.model_validate(raw)
        if can_read(doc.policy, access):
            result.append(doc.model_dump(exclude={'passages', 'policy', 'sha256'}))
    return result


@router.get('/documents/passages/{chunk_id}')
def passage(chunk_id: str, request: Request, access: Access):
    for raw in request.app.state.store.documents(current=False):
        doc = DocumentRecord.model_validate(raw)
        found = next((p for p in doc.passages if p.chunk_id == chunk_id), None)
        if found:
            authorize(doc.policy, access)
            current = DocumentRecord.model_validate(request.app.state.store.document(doc.document_id))
            authorize(current.policy, access)
            return found
    raise forbidden()


@router.post('/documents', status_code=201)
def upload(request: Request, access: Access, file: Annotated[UploadFile, File()],
           metadata: Annotated[str, Form()], document_id: Annotated[str | None, Form()] = None):
    try:
        parsed = DocumentMetadata.model_validate_json(metadata)
    except ValueError as exc:
        raise AppError('invalid_request', 'Métadonnées documentaires invalides.', 422) from exc
    content = file.file.read(request.app.state.settings.max_pdf_bytes + 1)
    doc, duplicate = request.app.state.documents.ingest_pdf(content, parsed, access, document_id)
    return {'document': doc.model_dump(exclude={'passages', 'policy', 'sha256'}), 'duplicate': duplicate}


@router.get('/documents/{document_id}/pdf')
def original(document_id: str, request: Request, access: Access, version: int | None = Query(default=None, gt=0)):
    store = request.app.state.store
    raw, current = store.document(document_id, version), store.document(document_id)
    if not raw or not current:
        raise forbidden()
    doc = DocumentRecord.model_validate(raw)
    authorize(doc.policy, access)
    authorize(DocumentRecord.model_validate(current).policy, access)
    content = store.document_pdf(document_id, doc.version)
    if content is None:
        raise AppError('missing_data', 'Original PDF non disponible.', 404)
    return Response(content, media_type='application/pdf',
                    headers={'Content-Disposition':'attachment; filename="document.pdf"'})
