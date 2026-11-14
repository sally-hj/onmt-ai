"""QVD et calculs réels ; modèles IA explicitement simulés dans ce fichier."""
import json
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pyqvd import QvdTable

from app.analytics.forecasting import forecast
from app.analytics.service import AnalyticsService
from app.conversation.intent import Intent
from app.core.config import ROOT, Settings
from app.core.errors import AppError
from app.core.state import AppState
from app.data_access.catalog import Catalog
from app.data_access.qvd_reader import normalize_month
from app.data_access.synthetic import DESTINATIONS, generate
from app.main import create_app
from app.schemas.analysis import AnalysisRequest, SeriesPoint
from app.schemas.common import AccessContext


@pytest.fixture(scope='module')
def qvd_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp('native-qvd')
    generate(path)
    return path


@pytest.fixture
def scope():
    return AccessContext(user_id='direction',roles=['report_editor','document_editor'],
        allowed_modules=['reports','commercial','finance','performance'],allowed_territories=DESTINATIONS)


@pytest.fixture
def analytics(qvd_dir,tmp_path):
    return AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',qvd_dir),AppState(tmp_path))


def comparison(destination='Agadir',**updates):
    payload = dict(request_id='test',operation='compare',metric_id='overnight_stays',
        period={'start':'2025-02-01','end':'2025-02-28'},comparison_period={'start':'2024-02-01','end':'2024-02-29'},
        filters={'destination':destination},language='fr')
    payload.update(updates)
    return AnalysisRequest(**payload)


def test_binary_qvd_roundtrip_and_known_answers(qvd_dir,analytics,scope):
    for path in qvd_dir.glob('*.qvd'):
        raw = path.read_bytes()
        assert b'<QvdTableHeader>' in raw and b'\x00' in raw
        assert len(QvdTable.from_qvd(path).to_dict()['data']) == 2100
    expected = json.loads((qvd_dir/'expected.json').read_text())
    agadir = analytics.run(comparison(),scope)
    marrakech = analytics.run(comparison('Marrakech'),scope)
    assert agadir.values == {'current':expected['agadir_feb_2025'],'previous':100000,'change_pct':-20}
    assert marrakech.values == {'current':165000,'previous':150000,'change_pct':10}
    assert agadir.sources[0].fields[-1] == 'nights'
    assert agadir.is_synthetic and len(agadir.sources[0].version)==64
    assert analytics.run(comparison(filters={'destination':'Agadir','market':'France'}),scope).values['current']==25600


def test_access_filter_unknown_metric_and_no_partial_month(analytics,scope):
    regional = scope.model_copy(update={'allowed_modules':['reports','commercial'],'allowed_territories':['Marrakech']})
    for request in [comparison(),comparison('Marrakech',metric_id='budget')]:
        with pytest.raises(AppError) as error:
            analytics.run(request,regional)
        assert error.value.code=='forbidden'
    with pytest.raises(AppError):
        analytics.run(comparison(metric_id='imaginary_roi'),scope)
    with pytest.raises(AppError):
        analytics.run(comparison(period={'start':'2025-02-02','end':'2025-02-28'}),scope)


def test_ratios_aggregate_numerators_and_cross_module_grain(analytics,scope):
    dms = analytics.run(comparison(metric_id='average_stay'),scope)
    rows = QvdTable.from_qvd(analytics.catalog.reader.root/'commercial.qvd').to_dict()
    native = [dict(zip(rows['columns'],r)) for r in rows['data']]
    total_arrivals = sum(r['arrivals'] for r in native if r['destination']=='Agadir' and r['period']=='2025-02-01')
    assert dms.values['current'] == round(80000/total_arrivals,4)
    cross = analytics.run(comparison(metric_id='spend_per_night'),scope)
    assert {s.source_id for s in cross.sources}=={'finance','commercial'}
    assert 'pas un ROI causal' in ' '.join(cross.warnings)
    catalog = analytics.catalog.describe(scope)
    assert all(r['valid'] for r in catalog['relations'])


def test_defective_rows_are_blocked_and_missing_is_not_zero(qvd_dir,tmp_path,scope):
    config = json.loads((ROOT/'config/sources.synthetic.json').read_text(encoding='utf-8'))
    config['sources'][0]['file']='invalid/commercial-invalid.qvd'
    path = tmp_path/'bad.json'; path.write_text(json.dumps(config),encoding='utf-8')
    svc = AnalyticsService(Catalog(path,qvd_dir),AppState(tmp_path/'db'))
    with pytest.raises(AppError) as error:
        svc.run(comparison(),scope)
    assert error.value.code=='data_quality' and 'duplicate' in error.value.message and 'missing_value' in error.value.message
    healthy = AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',qvd_dir),AppState(tmp_path/'healthy'))
    absent = healthy.run(comparison(period={'start':'2030-01-01','end':'2030-01-31'}),scope)
    assert absent.status=='unavailable' and absent.values['current'] is None


def test_source_update_invalidates_saved_analysis(qvd_dir,tmp_path,scope):
    import shutil
    local = tmp_path/'qvd'; shutil.copytree(qvd_dir,local)
    service = AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',local),AppState(tmp_path/'state'))
    result = service.run(comparison(),scope)
    table = QvdTable.from_qvd(local/'commercial.qvd').to_dict()
    table['data'][0][-1] += 1
    QvdTable.from_dict(table).to_qvd(local/'commercial.qvd')
    with pytest.raises(AppError) as error:
        service.get_analysis(result.analysis_id,scope)
    assert error.value.code=='stale_analysis'


def test_forecast_chronology_and_seasonal_baseline(analytics,scope):
    request = comparison(operation='forecast',comparison_period=None,period={'start':'2021-01-01','end':'2025-12-31'},
                         forecast_horizon=3,forecast_frequency='month')
    result = analytics.run(request,scope)
    predicted = [p for p in result.series if p.kind=='forecast']
    assert len(predicted)==3 and str(predicted[0].date)=='2026-01-01'
    assert all(p.lower <= p.value <= p.upper for p in predicted)
    assert any('holdout_12_months_mae' in w for w in result.warnings)
    # Signal saisonnier parfait : erreur attendue nulle, calculée sans appeler le moteur métier.
    points = [SeriesPoint(date=f'{2020+i//12}-{i%12+1:02}-01',value=(i%12+1)*100,kind='observed') for i in range(48)]
    future,warnings = forecast(points,2)
    assert [p.value for p in future]==[100,200] and 'holdout_rmse:0.0000' in warnings
    assert normalize_month(45689)=='2025-02-01'


class ScriptedParser:
    """Double de test annoncé ; jamais branché dans le démarrage réel."""
    def parse(self,message,context,catalog,language):
        if message=='Marrakech':
            return Intent(action='analyse',destination='Marrakech')
        if message=='report':
            return Intent(action='report')
        if message=='ar':
            return Intent(action='revise',instruction='langue:ar')
        if message=='budget':
            return Intent(action='update_report',metric_id='budget')
        if message=='clarify':
            return Intent(action='clarify',clarification='Quelle période ?')
        return Intent(action='analyse',**{k:v for k,v in comparison().model_dump().items() if k in ['metric_id','operation','period','comparison_period']},destination='Agadir')


@pytest.fixture
def full_app(qvd_dir,tmp_path):
    app = create_app(Settings(full_app=True,data_dir=tmp_path,demo=True,demo_embeddings=True,generation_mode='template',
                              ollama_model='',ocr_enabled=False,qvd_root=qvd_dir))
    app.state.conversations.parser = ScriptedParser()
    return app


def login(client,user='direction'):
    response = client.post('/api/auth/login',json={'username':user,'password':'OnmtLocal!2026'})
    assert response.status_code==200


def test_session_ownership_conversation_revision_and_recalculation(full_app):
    with TestClient(full_app) as client:
        assert client.get('/api/sources').status_code==401
        login(client)
        def send(text,previous=None):
            body = {'message':text}
            if previous:
                body.update(conversation_id=previous['conversation_id'],base_version=previous['version'])
            response = client.post('/api/conversations/messages',json=body)
            assert response.status_code==200,response.text
            return response.json()
        first = send('Agadir'); assert first['analysis']['values']['change_pct']==-20
        second = send('Marrakech',first); assert second['analysis']['values']['change_pct']==10
        report = send('report',second); rid = report['report']['report_id']
        revised = send('ar',report); assert revised['report']['version']==2
        updated = send('budget',revised); assert updated['report']['report_id']==rid and updated['report']['version']==3
        assert updated['analysis']['metric_id']=='budget'
        assert full_app.state.store.report(rid)['request']['title'].startswith('Budget prévu')
        assert client.post('/api/conversations/messages',json={'message':'x','conversation_id':first['conversation_id'],'base_version':1}).status_code==409
        client.post('/api/auth/logout'); login(client,'regional')
        assert client.get('/api/conversations/'+first['conversation_id']).status_code==403
        assert client.get('/api/analyses/'+first['analysis']['analysis_id']).status_code==403
        assert client.post('/api/analyses',json=comparison(metric_id='budget').model_dump(mode='json')).status_code==403
        assert all(s['id']!='finance' for s in client.get('/api/sources').json()['sources'])
        assert client.post('/api/analyses',json=comparison('Fès').model_dump(mode='json')).status_code==403


def test_alert_is_detected_deduplicated_and_cross_origin_rejected(full_app):
    with TestClient(full_app) as client:
        login(client)
        first = client.post('/api/sources/refresh').json()['alerts']
        second = client.post('/api/sources/refresh').json()['alerts']
        assert {a['id'] for a in first}=={a['id'] for a in second}
        assert any(a['destination']=='Agadir' and a['month']=='2025-02-01' and a['change_pct']==-20 for a in first)
        assert client.post('/api/sources/refresh',headers={'origin':'https://hostile.invalid'}).status_code==403


def test_context_link_and_explicit_slots(full_app):
    from app.conversation.slots import ground_intent
    intent=ground_intent(Intent(action='analyse',operation='compare'),'Compare les nuitées février 2025 et février 2024')
    assert str(intent.period.start)=='2025-02-01' and str(intent.comparison_period.end)=='2024-02-29'
    for text in ['Compare February 2025 and February 2024','Compara febrero 2025 y febrero 2024','قارن فبراير ٢٠٢٥ و فبراير ٢٠٢٤']:
        assert str(ground_intent(Intent(action='analyse',operation='compare'),text).period.start)=='2025-02-01'
    translated=ground_intent(Intent(action='revise',instruction='texte invalide'),'Traduis la synthèse en arabe.')
    assert translated.instruction=='langue:ar' and translated.language=='ar'
    grounded=ground_intent(Intent(action='analyse',operation='compare',destination='Agadir',market='France'),
            'قارن ليا الليالي السياحية فأكادير ففبراير 2025 وففبراير 2024.',{'destinations':['Agadir'],'markets':['France']})
    assert grounded.destination=='Agadir' and grounded.market is None and str(grounded.period.start)=='2025-02-01'
    with TestClient(full_app) as client:
        login(client)
        analysis=client.post('/api/analyses',json=comparison().model_dump(mode='json')).json()
        linked=client.post('/api/conversations/context',json={'base_version':0,'analysis_id':analysis['analysis_id']})
        assert linked.status_code==200
        saved=linked.json()
        response=client.post('/api/conversations/messages',json={'message':'Marrakech','conversation_id':saved['conversation_id'],'base_version':saved['version']})
        assert response.status_code==200 and response.json()['analysis']['values']['current']==165000


def test_performance_ratios_zero_denominator_and_units(tmp_path,scope):
    from app.data_access.synthetic import write_qvd
    rows=[]
    for market,sold,revenue in [('France',30,1500),('Espagne',70,3500)]:
        rows.append({'record_key':market,'period':'2025-02-01','destination':'Agadir','market':market,
            'room_revenue_mad':revenue,'room_nights_sold':sold,'room_nights_available':100,
            'travel_receipts_mad':10000,'impressions':1000,'clicks':50})
    write_qvd(tmp_path/'performance.qvd',rows)
    svc=AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',tmp_path),AppState(tmp_path/'state'))
    def value(metric):
        return svc.run(comparison(operation='value',comparison_period=None,metric_id=metric),scope)
    assert value('occupancy').values['value']==50
    assert value('revpar').values['value']==25
    assert value('average_room_price').values['value']==50
    assert value('click_rate').values['value']==5
    for row in rows:
        row['room_nights_sold']=0
        row['room_nights_available']=0
    write_qvd(tmp_path/'performance.qvd',rows)
    unavailable=value('occupancy')
    assert unavailable.values['value'] is None and unavailable.status=='unavailable'
    assert 'zero_denominator' in unavailable.warnings
    svc.catalog.sources['performance']['units']['room_revenue']='EUR'
    with pytest.raises(AppError) as error:
        value('revpar')
    assert error.value.code=='data_quality'


def test_qlik_dual_value_roundtrip(tmp_path):
    from pyqvd.qvd.values import DualIntegerValue
    path=tmp_path/'dual.qvd'
    QvdTable([[DualIntegerValue(45689,'01/02/2025')]],['month']).to_qvd(path)
    value=QvdTable.from_qvd(path).to_dict()['data'][0][0]
    assert value==45689 and normalize_month(value)=='2025-02-01'


def test_territorial_and_market_benchmarks(analytics,scope):
    from app.conversation.slots import ground_intent
    territorial=analytics.benchmark(comparison(),scope,'destination',['Agadir','Marrakech'])
    assert [a.values['current'] for a in territorial]==[80000,165000]
    by_market=analytics.benchmark(comparison(),scope,'market',['France','Espagne'])
    assert [a.values['current'] for a in by_market]==[25600,16000]
    intent=ground_intent(Intent(action='analyse',operation='compare',metric_id='overnight_stays',market='Marrakech'),
        'Compare les nuitées à Agadir et Marrakech en février 2025.',{'destinations':scope.allowed_territories,'markets':['France','Espagne']})
    assert intent.action=='benchmark' and intent.dimensions==['Agadir','Marrakech'] and intent.operation=='value' and intent.market is None
    regional=scope.model_copy(update={'allowed_territories':['Agadir']})
    with pytest.raises(AppError):
        analytics.benchmark(comparison(),regional,'destination',['Agadir','Marrakech'])


def test_mapping_changes_calculation_and_displayed_source_fields(qvd_dir,tmp_path,scope):
    table=QvdTable.from_qvd(qvd_dir/'commercial.qvd').to_dict()
    table['columns'][table['columns'].index('nights')]='actual_overnight_total'
    QvdTable.from_dict(table).to_qvd(tmp_path/'commercial.qvd')
    config=json.loads((ROOT/'config/sources.synthetic.json').read_text(encoding='utf-8'))
    config['sources'][0]['fields']['overnight_stays']='actual_overnight_total'
    path=tmp_path/'mapping.json';path.write_text(json.dumps(config),encoding='utf-8')
    service=AnalyticsService(Catalog(path,tmp_path),AppState(tmp_path/'state'))
    result=service.run(comparison(),scope)
    assert result.values['current']==80000
    assert result.formula=='SUM(actual_overnight_total)'
    assert 'actual_overnight_total' in result.sources[0].fields
