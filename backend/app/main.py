import logging
from contextlib import asynccontextmanager
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
    @asynccontextmanager
    async def lifespan(app):
        if hasattr(app.state,'monitor'): app.state.monitor.start()
        try:
            yield
        finally:
            if hasattr(app.state,'monitor'): app.state.monitor.stop()
            if hasattr(app.state,'jobs'): app.state.jobs.close()
    app = FastAPI(title='ONMT AI — Analyses conversationnelles', version='0.2.0',lifespan=lifespan)
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

    if settings.full_app:
        import os
        os.environ['LANGSMITH_TRACING'] = 'false'
        os.environ['LANGCHAIN_TRACING_V2'] = 'false'
        from app.analytics.service import AnalyticsService
        from app.analytics.anomalies import AlertService
        from app.analytics.router import router as analytics_router
        from app.conversation.intent import IntentParser
        from app.conversation.service import ConversationService
        from app.conversation.router import router as conversation_router
        from app.core.auth import LocalAuth, router as auth_router
        from app.core.state import AppState
        from app.data_access.catalog import Catalog
        state = AppState(settings.data_dir)
        auth = LocalAuth(state)
        auth.bootstrap()
        catalog = Catalog(settings.sources_config,settings.qvd_root)
        analytics = AnalyticsService(catalog,state)
        app.state.application_state,app.state.auth,app.state.catalog = state,auth,catalog
        app.state.analytics = analytics
        app.state.alerts = AlertService(catalog,state)
        from app.core.monitor import Monitor
        from app.core.jobs import Jobs
        app.state.monitor = Monitor(state,app.state.alerts,settings.monitor_interval)
        app.state.jobs = Jobs(state)
        app.state.access_resolver = access_resolver or auth.resolve
        app.state.reports.provider = analytics
        parser = IntentParser(OllamaPlanner(settings.ollama_model,settings.ollama_timeout,settings.ollama_context))
        app.state.conversations = ConversationService(state,analytics,app.state.reports,app.state.exporter,parser)
        app.include_router(auth_router)
        app.include_router(analytics_router)
        app.include_router(conversation_router)

    @app.middleware('http')
    async def request_context(request: Request, call_next):
        request.state.request_id = uuid4().hex
        if settings.full_app and request.method in ['POST','PATCH','PUT','DELETE']:
            origin = request.headers.get('origin')
            # Session locale : bloquer les écritures provenant d'un site tiers.
            if origin and origin != str(request.base_url).rstrip('/') and origin not in ['http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8000','http://localhost:8000']:
                return JSONResponse(status_code=403,content={'request_id':request.state.request_id,'code':'forbidden','message':'Origine non autorisée.'})
        response = await call_next(request)
        if settings.full_app:
            actor='anonymous'
            try: actor=app.state.access_resolver(request).user_id
            except AppError: pass
            route=request.scope.get('route')
            store.audit_log.append(actor,request.state.request_id,request.method,
                getattr(route,'path','unknown_route'),outcome=str(response.status_code))
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
