import io
from concurrent.futures import ThreadPoolExecutor

import pdfplumber
import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT, Settings
from app.core.errors import AppError
from app.core.security import ResourcePolicy, can_read, demo_access
from app.main import create_app
from app.reports.adapters import SyntheticAnalysisProvider
from app.reports.generation import facts
from app.reports.validation import verify_report
from app.schemas.report import ReportRevisionRequest


def revision(report, **kwargs):
    raw = dict(request_id='revision-test', report_id=report.report_id, base_version=report.version,
               section_id='diagnostic', instruction='résumer')
    raw.update(kwargs)
    return ReportRevisionRequest(**raw)


def test_pdf_inline_preview_retains_authorization(application,request_body,access):
    report=application.state.reports.create_report(request_body,access)
    application.state.store.save_pdf(report.report_id,report.version,b'%PDF-1.4 preview fixture')
    with TestClient(application) as client:
        path=f'/api/reports/{report.report_id}/pdf?version=1'
        assert client.get(path).headers['content-disposition'].startswith('attachment;')
        inline=client.get(path+'&inline=true')
        assert inline.status_code==200 and inline.headers['content-disposition'].startswith('inline;')
        assert inline.headers['cache-control']=='no-store'
        application.state.access_resolver=lambda request: access.model_copy(update={'user_id':'other'})
        assert client.get(path+'&inline=true').status_code==403


def test_values_units_forecast_missing_and_synthetic(application, request_body, access):
    service = application.state.reports
    result = service.create_report(request_body, access)
    combined = '\n'.join(s.content for s in result.sections)
    assert '80000 nuitees' in combined and '-20 %' in combined
    assert '100000 %' not in combined
    forecast = next(s.content for s in result.sections if s.section_id == 'forecast')
    assert 'Prévision' in forecast and '85000 nuitees' in forecast and 'indisponible' in forecast
    assert result.is_synthetic and 'synthetic_data' in result.warnings
    assert '"destination": "Agadir"' in combined
    assert result.download_path is None
    rows = facts(service._analyses(request_body.analysis_ids, access))
    assert next(r for r in rows if r['key']=='previous')['date'] == '2024-02-01/2024-02-29'


@pytest.mark.parametrize('language', ['fr','en','es','ar','ary'])
@pytest.mark.parametrize('audience', ['direction','ministere','regional'])
def test_languages_and_audiences(application, request_body, access, language, audience):
    from app.reports.generation import TEXT
    result = application.state.reports.create_report(request_body.model_copy(update={'language':language,'audience':audience}), access)
    assert TEXT[language]['audiences'][audience] in result.sections[0].content


def test_sources_absent_do_not_create_numeric_claims(application, request_body, access):
    provider = application.state.reports.provider
    provider.results['ana_demo_compare'].sources = []
    body = request_body.model_copy(update={'analysis_ids':['ana_demo_compare']})
    result = application.state.reports.create_report(body, access)
    assert 'analysis_sources_absent:ana_demo_compare' in result.warnings
    assert '80000' not in '\n'.join(s.content for s in result.sections)


def test_missing_forecast_and_unavailable(application, request_body, access):
    provider = application.state.reports.provider
    a = provider.results['ana_demo_compare']; a.status = 'unavailable'; a.values = {'value':None}
    result = application.state.reports.create_report(request_body.model_copy(update={'analysis_ids':[a.analysis_id]}), access)
    assert all('80000' not in s.content for s in result.sections)
    assert 'Données insuffisantes' in next(s.content for s in result.sections if s.section_id == 'forecast')


def test_no_real_error_fallback(application, request_body, access):
    class Failing:
        def get_analysis(self, analysis_id, access_context):
            raise AppError('tool_failed', 'Échec réel.', 503)
    application.state.reports.provider = Failing()
    with pytest.raises(AppError, match='Échec réel'):
        application.state.reports.create_report(request_body, access)
    assert application.state.store.report_ids() == []


def test_large_integer_and_null_not_coerced_to_zero(application, request_body, access):
    a = application.state.reports.provider.results['ana_demo_compare']
    a.values={'current':9007199254740993,'previous':None,'change_pct':None}
    a.series=[]
    report=application.state.reports.create_report(request_body.model_copy(update={'analysis_ids':[a.analysis_id]}),access)
    text=report.sections[0].content
    assert '9007199254740993 nuitees' in text
    assert 'indisponible nuitees' in text and 'indisponible %' in text
    assert '9007199254740992' not in text


def test_ambiguous_source_versions_are_rejected(application,request_body,access):
    provider=application.state.reports.provider
    a=provider.results['ana_demo_forecast']
    a.sources[0].source_id='src_demo_commercial'
    with pytest.raises(AppError,match='Référence ambiguë'):
        application.state.reports.create_report(request_body,access)


def test_verifier_blocks_changed_value_or_unit(application, request_body, access):
    result = application.state.reports.create_report(request_body, access)
    result.sections[0].content = result.sections[0].content.replace('80000 nuitees','42 EUR')
    with pytest.raises(AppError, match='vérification'):
        verify_report(result, request_body, application.state.reports._analyses(request_body.analysis_ids, access), [], {})


def test_five_revisions_history_dependencies_and_stale(application, request_body, access):
    service = application.state.reports
    result = service.create_report(request_body, access)
    first_forecast = next(s for s in result.sections if s.section_id == 'forecast')
    first = result.model_copy(deep=True)
    for i in range(5):
        result = service.revise_report(revision(result,instruction='résumer' if i%2 == 0 else 'détailler'),access)
    assert result.version == 6 and result.is_synthetic
    assert first_forecast == next(s for s in result.sections if s.section_id == 'forecast')
    assert service.get_report(result.report_id,access,1) == first
    raw = application.state.store.report(result.report_id)
    assert raw['section_versions']['summary'] == 6
    assert raw['section_versions']['forecast'] == 1
    with pytest.raises(AppError) as caught: service.revise_report(revision(first),access)
    assert caught.value.code == 'version_conflict'
    with pytest.raises(AppError): service.revise_report(revision(result,instruction='Ajoute le marché chinois'),access)


def test_concurrent_revision_compare_and_swap(application, request_body, access):
    service = application.state.reports
    result = service.create_report(request_body, access)
    def edit():
        try: return service.revise_report(revision(result),access).version
        except AppError as exc: return exc.code
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _:edit(), range(2)))
    assert sorted(map(str,results)) == ['2','version_conflict']


def test_persistence_on_restart(application, request_body, access):
    result = application.state.reports.create_report(request_body,access)
    other = create_app(application.state.settings)
    assert other.state.reports.get_report(result.report_id,access) == result


def test_authorization_on_read_edit_pdf_and_listing(application, request_body, access):
    service = application.state.reports
    result = service.create_report(request_body, access)
    for bad in [access.model_copy(update={'user_id':'other'}), access.model_copy(update={'allowed_territories':['Marrakech']}),
                access.model_copy(update={'roles':[]}), access.model_copy(update={'allowed_modules':[]})]:
        for action in [lambda:service.get_report(result.report_id,bad),
                       lambda:service.revise_report(revision(result),bad),
                       lambda:service.download_pdf(result.report_id,bad),
                       lambda:service.export_pdf(result.report_id,bad,application.state.exporter)]:
            with pytest.raises(AppError): action()
    assert service.list_reports(access.model_copy(update={'user_id':'other'})) == []


def test_acl_empty_and_subset():
    policy = ResourcePolicy(owner_id='a',roles=['analyst'],modules=['reports','finance'],territories=['Agadir'])
    access = demo_access()
    assert not can_read(policy,access)
    policy.roles=['report_editor']; policy.modules=['reports']
    assert can_read(policy,access)
    assert not can_read(policy,access.model_copy(update={'allowed_territories':[]}))


def test_api_errors_context_never_trusted_and_paths(client, request_body):
    raw = request_body.model_dump(mode='json')
    raw['access_context'] = {'user_id':'admin'}
    assert client.post('/api/reports',json=raw).status_code == 422
    result = client.post('/api/reports',json=request_body.model_dump(mode='json'))
    assert result.status_code == 201, result.text
    report = result.json()
    assert client.get('/api/reports/'+report['report_id']).status_code == 200
    assert client.get('/api/reports/'+report['report_id']+'/pdf').status_code == 404
    body = revision(type('R',(),report)).model_dump(mode='json')
    body['report_id'] = 'wrong'
    assert client.patch(f"/api/reports/{report['report_id']}/sections/diagnostic",json=body).status_code == 422
    missing = client.get('/api/reports/secret')
    assert missing.status_code == 403 and set(missing.json()) == {'request_id','code','message'}
    bad = client.post('/api/reports',json={})
    assert bad.status_code == 422 and 'traceback' not in bad.text.lower()


def test_production_no_auth_and_no_implicit_demo(tmp_path, request_body):
    app = create_app(Settings(data_dir=tmp_path,demo=False,demo_embeddings=False))
    with TestClient(app) as client:
        response = client.post('/api/reports',json=request_body.model_dump(mode='json'),headers={'X-User-ID':'salma-demo','X-Roles':'admin'})
    assert response.status_code == 401
    with pytest.raises(ValueError): Settings(demo=False,demo_embeddings=True)


@pytest.mark.parametrize('language',['fr','ar'])
def test_real_pdf_text_readability_tables_and_history(application, request_body, access, language):
    service = application.state.reports
    request_body = request_body.model_copy(update={'language':language})
    result = service.create_report(request_body,access)
    result = service.export_pdf(result.report_id,access,application.state.exporter)
    assert result.download_path is not None
    pdf = service.download_pdf(result.report_id,access)
    assert pdf.startswith(b'%PDF')
    with pdfplumber.open(io.BytesIO(pdf)) as document:
        texts = [p.extract_text() or '' for p in document.pages]
        assert len(texts) >= 8 and all(t.strip() for t in texts)
        text = '\n'.join(texts)
        assert '80000' in text and 'nuitees' in text and 'DEMO_Commercial.qvd' in text
        assert 'Agadir' in text
        assert '85000' in text
        if language == 'ar': assert sum('\u0600' <= c <= '\u06ff' for c in text) > 100
    revised = service.revise_report(revision(result),access)
    assert revised.download_path is None
    assert service.get_report(result.report_id,access,version=1).download_path is not None


def test_pdf_api(client, request_body):
    report = client.post('/api/reports',json=request_body.model_dump(mode='json')).json()
    exported = client.post(f"/api/reports/{report['report_id']}/export")
    assert exported.status_code == 200, exported.text
    pdf = client.get(exported.json()['download_path'])
    assert pdf.status_code == 200 and pdf.headers['content-type']=='application/pdf'
    assert pdf.headers['cache-control'] == 'no-store'


def test_long_table_pdf_and_html_escaping(application,request_body,access):
    from datetime import date,timedelta
    from app.schemas.analysis import SeriesPoint
    provider=application.state.reports.provider
    a=provider.results['ana_demo_compare']
    a.series=[SeriesPoint(date=date(2025,1,1)+timedelta(days=i),value=1234+i,kind='observed') for i in range(100)]
    request_body=request_body.model_copy(update={'title':'<script>throw 42</script> — Synthetic',
                                                'analysis_ids':[a.analysis_id], 'sections':['summary','limitations']})
    service=application.state.reports
    result=service.create_report(request_body,access)
    result=service.export_pdf(result.report_id,access,application.state.exporter)
    with pdfplumber.open(io.BytesIO(service.download_pdf(result.report_id,access))) as pdf:
        text='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert '<script>throw 42</script>' in text
        assert '1333' in text and '2025-04-10' in text
        assert len(pdf.pages)>5
