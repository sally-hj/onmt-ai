"""QVD natifs ; attendus littéraux établis à la main, sans LLM dans ces tests."""
import hashlib
import json
from pathlib import Path

import pytest

from app.analytics.custom import KpiDefinition
from app.analytics.diagnostics import Diagnostics, bcg_point, butler
from app.analytics.metrics import METRICS
from app.analytics.service import AnalyticsService
from app.core.config import ROOT
from app.core.errors import AppError
from app.core.state import AppState
from app.data_access.catalog import Catalog
from app.data_access.supplement import prepare
from app.data_access.synthetic import generate, write_qvd
from app.schemas.analysis import AnalysisRequest, SeriesPoint
from app.schemas.common import AccessContext

REFERENCE=json.loads((ROOT/'examples/synthetic-reference.json').read_text(encoding='utf-8'))['calculation_oracle']
EXPECTED={
 'receipts_per_arrival':800,'receipts_per_night':200,'spend_per_arrival':40,
 'commitment_rate':75,'budget_remaining':1000,'commitments_unpaid':500,
 'impressions':2000,'clicks':100,'cost_per_click':10,'cost_per_thousand':500,
 'rooms_available':100,'rooms_sold':40,'international_arrivals':25,
 'market_concentration':5200,'market_diversification':.48,'tourism_gini':0,
 'conversions':5,'campaign_conversion':5,'event_attendance':30,'event_fill':50,
 'tourism_gdp_share':10,'employment_share':20,'web_conversion':5,
 'marketing_visibility':10,'campaign_roi':20,
 'seasonality':None,'annual_growth':None,'annual_cagr':None,
 'regional_performance':61.6987,'ttci2019_pedagogical':4.2,
}


def access():
    return AccessContext(user_id='direction',roles=['report_editor','document_editor'],
        allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'])


def request(metric='arrivals'):
    return AnalysisRequest(request_id='independent',operation='value',metric_id=metric,
        period=REFERENCE['period'],filters=REFERENCE['filters'],language='fr')


@pytest.fixture()
def service(tmp_path):
    for name,rows in REFERENCE['sources'].items(): write_qvd(tmp_path/f'{name}.qvd',rows)
    extension=[]
    for r, values in zip(REFERENCE['sources']['commercial'],[(2,10,20,8,100,2,10,50,12,700),(3,20,40,12,100,3,15,50,8,500)]):
        fields=['conversions','event_attendance','event_capacity','tourism_gva_mad','gdp_mad','tourism_jobs','total_jobs','web_visits','engagements','attributed_margin_mad']
        extension.append({k:r[k] for k in ['record_key','period','destination','market']}|dict(zip(fields,values)))
    (tmp_path/'supplement').mkdir()
    write_qvd(tmp_path/'supplement/extension.qvd',extension)
    pillars=[f for group in json.loads((ROOT/'config/ttci2019.json').read_text(encoding='utf-8'))['groups'] for f in group]
    scores=[[1,2,3,4,5,2,2,2,2,3,3,3,4,4],[5,5,5,5,5,5,5,5,5,5,5,5,5,5]]
    write_qvd(tmp_path/'supplement/competitiveness.qvd',[
        {k:row[k] for k in ['record_key','period','destination','market']}|dict(zip(pillars,values))
        for row,values in zip(REFERENCE['sources']['commercial'],scores)])
    return AnalyticsService(Catalog(ROOT/'config/sources.extended.json',tmp_path),AppState(tmp_path/'state'))


@pytest.mark.parametrize('metric,expected',EXPECTED.items())
def test_new_metrics_independent_native_oracle(service,metric,expected):
    result=service.run(request(metric),access())
    assert result.values['value']==expected
    assert result.status==('unavailable' if expected is None else 'ok')
    assert result.sources and result.is_synthetic


def test_every_catalog_metric_has_an_independent_oracle():
    assert set(METRICS)==set(REFERENCE['expected'])|set(EXPECTED)
    assert len(METRICS)>=31


def test_temporal_metrics_manual_flat_series(tmp_path):
    rows=[]
    for year,arrivals in [(2023,10),(2024,12),(2025,14.4)]:
        for month in range(1,13):
            rows.append({'record_key':f'{year}-{month:02}|Agadir|France','period':f'{year}-{month:02}-01','destination':'Agadir','market':'France',
                'arrivals':arrivals,'nights':100,'seats':30,'bookings':5})
    write_qvd(tmp_path/'commercial.qvd',rows)
    svc=AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',tmp_path),AppState(tmp_path/'state'))
    for metric,expected in [('annual_growth',20),('annual_cagr',20),('seasonality',0)]:
        r=request(metric).model_copy(update={'period':request().period.model_copy(update={'start':__import__('datetime').date(2023,1,1),'end':__import__('datetime').date(2025,12,31)})})
        assert svc.run(r,access()).values['value']==expected


def test_custom_kpi_confirmation_versions_rights_and_no_code(service):
    spec=KpiDefinition(id='custom_france_share',label='Part France',operation='percent',
        numerator={'source':'commercial','field':'arrivals','market':'France'},denominator={'source':'commercial','field':'arrivals'},
        interpretation='Part des arrivées du marché France dans le périmètre autorisé.')
    proposal=service.custom.propose(spec,access())
    assert not service.custom.list(access())
    with pytest.raises(AppError): service.custom.confirm(proposal['proposal_id'],access())
    metric=service.custom.metric(proposal)
    data,_=service._read(metric,request().filters,access())
    value,_,_=service._aggregate(metric,data,request().period)
    assert value==40  # 10/25, calcul manuel
    service.custom.attach_example(proposal,{'value':value,'unit':'%'})
    service.custom.confirm(proposal['proposal_id'],access())
    actual=service.run(request(spec.id),access())
    assert actual.values['value']==40
    fresh=AnalyticsService(service.catalog,AppState(service.state.path.parent))
    assert fresh.run(request(spec.id),access()).values['value']==40
    new=service.custom.propose(spec,access()); service.custom.attach_example(new,{'value':40}); service.custom.confirm(new['proposal_id'],access())
    with pytest.raises(AppError,match='recalcul'): service.get_analysis(actual.analysis_id,access())
    bad=spec.model_copy(update={'operation':'percent','numerator':spec.numerator.model_copy(update={'source':'finance','field':'spent'})})
    with pytest.raises(AppError): service.custom.propose(bad,access())
    restricted=access().model_copy(update={'allowed_modules':['reports','commercial']})
    with pytest.raises(AppError): service.custom.propose(bad,restricted)
    with pytest.raises(ValueError): KpiDefinition.model_validate({**spec.model_dump(),'python':'__import__("os")'})


def test_supplement_preserves_reference_and_is_idempotent(tmp_path):
    generate(tmp_path)
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.glob('*.qvd')}
    first=prepare(tmp_path); second=prepare(tmp_path)
    assert first==second
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.glob('*.qvd')}
    catalog=Catalog(ROOT/'config/sources.extended.json',tmp_path).describe(access())
    assert all(not s['quality_errors'] for s in catalog['sources'])
    assert all(r['valid'] for r in catalog['relations'])


def test_bcg_uses_market_growth_and_competitor():
    assert bcg_point(200,100,1200,1000,100)=={'quadrant':'vedette','market_growth_pct':20,'relative_share':2}
    assert bcg_point(200,100,1000,1000,400)['quadrant']=='poids_mort'
    assert bcg_point(200,100,1000,0,400)['quadrant']=='indetermine'
    assert bcg_point(50,50,1200,1000,100)['quadrant']=='dilemme'
    assert bcg_point(200,100,1000,1000,100)['quadrant']=='vache_a_lait'


def test_butler_needs_more_than_a_single_change():
    assert butler([SeriesPoint(date='2025-02-01',value=80000,kind='observed')])['stage']=='indetermine'
    points=[SeriesPoint(date=f'{year}-{month:02}-01',value=100,kind='observed') for year in range(2021,2026) for month in range(1,13)]
    assert butler(points)['stage']=='stabilite_possible'
    assert butler(points[:-1])['stage']=='indetermine'


def test_value_volume_manual_oracle(service):
    result=Diagnostics(service).value_volume(request(),access(),value_threshold=1000,volume_threshold=12)
    assert [(r['market'],r['volume'],r['value']) for r in result['points']]==[('Espagne',15,1066.6667),('France',10,400)]
    assert result['points'][0]['quadrant']=='valeur_forte_volume_fort'


def test_international_13_metrics_and_comparable_periods(service):
    from app.data_access.supplement import COMPARATORS
    rows=[]
    for name in COMPARATORS:
        for year,arrivals,market_total in [(2024,100,1000),(2025,200,1200)]:
            rows.append({'record_key':f'{year}|{name}','period':f'{year}-01-01','destination':name,'market':'Total',
                'arrivals':arrivals,'nights':800,'seats':500,'bookings':100,'receipts_mad':8000,'room_revenue_mad':40000,
                'rooms_sold':400,'rooms_available':800,'gdp_mad':1000000,'tourism_gva_mad':100000,'market_total_arrivals':market_total,'competitor_arrivals':100})
    write_qvd(service.catalog.reader.root/'supplement/international.qvd',rows)
    from app.schemas.common import Period
    period=Period(start='2025-01-01',end='2025-01-31'); previous=Period(start='2024-01-01',end='2024-01-31')
    result=Diagnostics(service).international(period,previous,access())
    expected={'arrivals':200,'overnight_stays':800,'seats':500,'bookings':100,'travel_receipts':8000,'room_revenue':40000,
        'average_stay':4,'occupancy':50,'revpar':50,'average_room_price':100,'receipts_per_arrival':40,'receipts_per_night':10,'tourism_gdp_share':10}
    assert len(result['rows'])==6
    for row in result['rows']:
        assert row['indicators']==expected and row['market_growth_pct']==20 and row['relative_share']==2 and row['quadrant']=='vedette'
    with pytest.raises(AppError): Diagnostics(service).international(period,Period(start='2024-02-01',end='2024-02-29'),access())


def test_diagnostic_snapshot_persistence_and_revoked_rights(service):
    diagnostic=service.products.save(Diagnostics(service).value_volume(request(),access()),access())
    assert service.products.get(diagnostic['diagnostic_id'],access())==diagnostic
    with pytest.raises(AppError): service.products.get(diagnostic['diagnostic_id'],access().model_copy(update={'user_id':'other'}))
    with pytest.raises(AppError): service.products.get(diagnostic['diagnostic_id'],access().model_copy(update={'allowed_modules':['reports','commercial']}))


def test_long_horizon_is_a_mechanical_scenario_with_periodic_manual_answer():
    from app.analytics.forecasting import forecast
    points=[SeriesPoint(date=f'{year}-{month:02}-01',value=month*100,kind='observed') for year in range(2022,2026) for month in range(1,13)]
    projected,warnings=forecast(points,60)
    assert [p.value for p in projected[:14]]==[100,200,300,400,500,600,700,800,900,1000,1100,1200,100,200]
    assert str(projected[-1].date)=='2030-12-01' and projected[-1].value==1200
    assert 'long_horizon_mechanical_scenario_not_calibrated_for_2030' in warnings


def test_scenario_is_not_an_observation_and_rejects_ratio(service):
    result=Diagnostics(service).scenario(request('overnight_stays'),access(),-10)
    assert result['baseline']==100 and result['scenario_value']==90 and result['shock_pct']==-10
    assert result['kind']=='scenario' and 'pas une observation' in result['warning']
    with pytest.raises(AppError): Diagnostics(service).scenario(request('occupancy'),access(),5)


def test_nonadditive_scores_and_financial_view_cannot_bypass_rights(service):
    regional=access().model_copy(update={'allowed_modules':['reports','commercial','performance']})
    spec=KpiDefinition(id='custom_unsafe_margin',label='Marge',operation='ratio',
        numerator={'source':'extension_finance','field':'attributed_margin'},denominator={'source':'commercial','field':'arrivals'},
        interpretation='Test de refus des sources financières non autorisées.')
    with pytest.raises(AppError): service.custom.propose(spec,regional)
    bad=spec.model_copy(update={'numerator':spec.numerator.model_copy(update={'source':'extension','field':'attributed_margin'})})
    with pytest.raises(AppError): service.custom.propose(bad,regional)
    score=spec.model_copy(update={'numerator':spec.numerator.model_copy(update={'source':'competitiveness','field':'safety'})})
    with pytest.raises(AppError,match='additifs'): service.custom.propose(score,access())
