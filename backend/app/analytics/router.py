from fastapi import APIRouter, Request
from pydantic import Field

from app.reports.router import Access
from app.schemas.analysis import AnalysisRequest
from app.schemas.common import Contract, Period
from app.core.errors import AppError
from .custom import KpiDefinition
from .diagnostics import Diagnostics

router = APIRouter(prefix='/api',tags=['Doha — analyses QVD'])


class Proposal(Contract):
    definition: KpiDefinition
    example: AnalysisRequest


class Confirm(Contract):
    proposal_id: str = Field(min_length=1,max_length=100)
    confirmed: bool


class DiagnosticRequest(Contract):
    kind: str = Field(pattern='^(international|bcg|bcg_regions|value_volume|butler|map|scenario)$')
    analysis: AnalysisRequest
    value_threshold: float = Field(default=2500,gt=0,le=10000000)
    volume_threshold: float = Field(default=10000,gt=0,le=1000000000)
    growth_threshold: float = Field(default=5,ge=-100,le=100)
    shock_pct: float | None = Field(default=None,ge=-90,le=100)


@router.post('/metrics/proposals',status_code=201)
def propose(body: Proposal,request: Request,access: Access):
    service=request.app.state.analytics
    proposal=service.custom.propose(body.definition,access)
    metric=service.custom.metric(proposal)
    data,refs=service._read(metric,body.example.filters,access)
    value,_,warnings=service._aggregate(metric,data,body.example.period)
    if value is None: raise AppError('missing_data','Exemple indisponible ; revoir période et dénominateur.',422)
    return service.custom.attach_example(proposal,{'value':value,'unit':metric.unit,'formula':metric.source_formula(service.catalog.sources),
        'period':body.example.period.model_dump(mode='json'),'filters':body.example.filters,'warnings':warnings,
        'sources':[r.model_dump(mode='json') for r in refs]})


@router.post('/metrics/confirm',status_code=201)
def confirm(body: Confirm,request: Request,access: Access):
    if not body.confirmed: raise AppError('invalid_request','Confirmation explicite requise.',422)
    return request.app.state.analytics.custom.confirm(body.proposal_id,access)


@router.post('/diagnostics')
def diagnostic(body: DiagnosticRequest,request: Request,access: Access):
    service=Diagnostics(request.app.state.analytics)
    if body.kind in ['international','bcg','bcg_regions']:
        if not body.analysis.comparison_period: raise AppError('invalid_request','Deux périodes explicites requises.',422)
        result=service.international(body.analysis.period,body.analysis.comparison_period,access,body.growth_threshold,regional=body.kind=='bcg_regions')
    elif body.kind=='butler': result=service.destination(body.analysis,access)
    elif body.kind=='map': result=service.map(body.analysis,access)
    elif body.kind=='scenario':
        if body.shock_pct is None: raise AppError('invalid_request','Préciser une hypothèse de variation en pourcentage.',422)
        result=service.scenario(body.analysis,access,body.shock_pct)
    else: result=service.value_volume(body.analysis,access,body.value_threshold,body.volume_threshold)
    return request.app.state.analytics.products.save(result,access)


@router.get('/diagnostics/{diagnostic_id}')
def read_diagnostic(diagnostic_id: str,request: Request,access: Access):
    return request.app.state.analytics.products.get(diagnostic_id,access)


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
            'continuous_monitoring':request.app.state.monitor.status()['running'],
            'monitor':request.app.state.monitor.status(),'streaming':False}


@router.get('/audit/verify')
def audit_verify(request: Request,access: Access):
    if 'finance' not in access.allowed_modules:
        from app.core.errors import forbidden
        raise forbidden()
    return request.app.state.store.audit_log.verify()


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
