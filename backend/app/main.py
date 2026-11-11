import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import ROOT, Settings
from app.core.errors import AppError
from app.core.llm_client import OllamaPlanner
from app.reports.adapters import SyntheticAnalysisProvider, UnconnectedAnalysisProvider
from app.reports.export import PDFExporter
from app.reports.ingestion import DocumentService
from app.reports.narrative import NarrativeWriter
from app.reports.retrieval import ChromaIndex, DemoHashEmbedder, LocalSentenceEmbedder, Retriever
from app.reports.router import router
from app.reports.service import ReportService
from app.reports.storage import Store


def create_app(settings=None, provider=None, access_resolver=None, embedder=None, exporter=None):
    settings = settings or Settings()
    app = FastAPI(title='ONMT AI — Reporting et RAG', version='0.1.0')
    store = Store(settings.data_dir)
    provider = provider or (SyntheticAnalysisProvider(ROOT / 'examples' / 'contracts') if settings.demo else UnconnectedAnalysisProvider())
    embedder = embedder or (DemoHashEmbedder() if settings.demo_embeddings else
                            LocalSentenceEmbedder(settings.embedding_model, settings.embedding_revision))
    if isinstance(embedder, DemoHashEmbedder) and not settings.demo:
        raise ValueError('Embeddings simulés interdits hors démo')
    index = ChromaIndex(settings.data_dir / 'chroma', embedder)
    retriever = Retriever(store, index, settings.max_distance)
    app.state.settings, app.state.store = settings, store
    app.state.access_resolver = access_resolver
    app.state.retriever = retriever
    app.state.documents = DocumentService(store, index, settings)
    writer = NarrativeWriter(OllamaPlanner(settings.ollama_model, settings.ollama_timeout, settings.ollama_context)) if settings.uses_llm else None
    app.state.reports = ReportService(store, provider, retriever, writer=writer)
    app.state.exporter = exporter or PDFExporter()

    @app.middleware('http')
    async def request_context(request: Request, call_next):
        request.state.request_id = uuid4().hex
        response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    def error(request, status, code, message):
        return JSONResponse(status_code=status, content={'request_id': getattr(request.state, 'request_id', uuid4().hex),
                                                        'code': code, 'message': message})

    @app.exception_handler(AppError)
    async def known_error(request, exc):
        return error(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return error(request, 422, 'invalid_request', 'Paramètres invalides ; consultez le schéma de l’API.')

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(request, exc.status_code, 'invalid_request', 'Route ou méthode indisponible.')

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        logging.getLogger(__name__).error('reporting_failed request_id=%s type=%s', request.state.request_id, type(exc).__name__)
        return error(request, 500, 'tool_failed', 'Le traitement a échoué ; consultez le journal local avec request_id.')

    app.include_router(router)
    return app


app = create_app()
