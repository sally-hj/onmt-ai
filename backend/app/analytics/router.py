from fastapi import APIRouter, Request

from app.reports.router import Access
from app.schemas.analysis import AnalysisRequest

router = APIRouter(prefix='/api',tags=['Doha — analyses QVD'])


@router.get('/system/status')
def status(request: Request,access: Access):
    import httpx
    settings = request.app.state.settings
    ollama,model = False,False
    try:
        with httpx.Client(timeout=2,trust_env=False) as client:
            response = client.get('http://127.0.0.1:11434/api/tags')
            response.raise_for_status()
            ollama = True
            model = any(m.get('name') == settings.ollama_model for m in response.json().get('models',[]))
    except (httpx.HTTPError,ValueError):
        pass
    return {'ollama_available':ollama,'configured_model_available':model,'generation_mode':'ollama' if settings.uses_llm else 'template',
            'ocr_enabled':settings.ocr_enabled,'tesseract_available':__import__('pathlib').Path(settings.tesseract_path).is_file(),
            'synthetic':request.app.state.catalog.config['synthetic'],'authentication':'local_session',
            'continuous_monitoring':False,'streaming':False}


@router.get('/sources')
def sources(request: Request,access: Access):
    return request.app.state.catalog.describe(access)


@router.get('/metrics')
def metrics(request: Request,access: Access):
    return request.app.state.analytics.metrics(access)


@router.post('/analyses',status_code=201)
def analyse(body: AnalysisRequest,request: Request,access: Access):
    return request.app.state.analytics.run(body,access)


@router.get('/analyses')
def analyses(request: Request,access: Access):
    result = []
    from app.core.errors import AppError
    for payload in request.app.state.application_state.list_analyses(access.user_id):
        try:
            result.append(request.app.state.analytics.get_analysis(payload['result']['analysis_id'],access))
        except AppError:
            continue
    return result


@router.get('/analyses/{analysis_id}')
def read(analysis_id: str,request: Request,access: Access):
    return request.app.state.analytics.get_analysis(analysis_id,access)


@router.get('/alerts')
def alerts(request: Request,access: Access):
    return request.app.state.alerts.list(access)


@router.post('/sources/refresh')
def refresh(request: Request,access: Access):
    catalog = request.app.state.catalog.describe(access)
    alerts = request.app.state.alerts.refresh(access)
    return {'catalog':catalog,'alerts':alerts,'trigger':'manual_refresh','continuous_monitoring':False}
