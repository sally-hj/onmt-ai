"""Corpus de référence définitif : QVD natifs, reproductibilité et oracle manuel."""
import hashlib
import json
import math

import pytest
from pyqvd import QvdTable

from app.analytics.metrics import METRICS
from app.analytics.service import AnalyticsService
from app.core.config import ROOT
from app.core.state import AppState
from app.data_access.catalog import Catalog
from app.data_access.synthetic import generate, semantic_digest, write_qvd
from app.schemas.analysis import AnalysisRequest
from app.schemas.common import AccessContext

REFERENCE = json.loads((ROOT/'examples/synthetic-reference.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    root = tmp_path_factory.mktemp('pedagogical-reference')
    manifest = generate(root)
    return root, manifest


def read_rows(path):
    table = QvdTable.from_qvd(path).to_dict()
    return table, [dict(zip(table['columns'], values)) for values in table['data']]


def access():
    return AccessContext(user_id='reference-audit', roles=['report_editor'],
        allowed_modules=['reports','commercial','finance','performance'],
        allowed_territories=['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'])


def test_native_corpus_and_cross_domain_invariants(corpus):
    root, manifest = corpus
    assert manifest['reference_status']=='pedagogical_final' and manifest['synthetic'] is True
    tables = {}
    for entry in manifest['files']:
        path = root/entry['file']
        raw = path.read_bytes()
        assert b'<QvdTableHeader>' in raw and b'\x00' in raw
        table, rows = read_rows(path)
        assert len(rows)==2100 and len({r['record_key'] for r in rows})==2100
        assert entry['semantic_sha256']==semantic_digest(table)
        assert entry['sha256']==hashlib.sha256(raw).hexdigest()
        assert sorted({r['period'] for r in rows})[::69]==['2021-01-01','2026-10-01']
        assert len({r['period'] for r in rows})==70
        for row in rows:
            assert row['record_key']==f"{row['period'][:7]}|{row['destination']}|{row['market']}"
            measures=[v for k,v in row.items() if k not in ['record_key','period','destination','market']]
            assert all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in measures)
        tables[entry['id']]={r['record_key']:r for r in rows}
    assert set(tables)=={'commercial','finance','performance'}
    assert tables['commercial'].keys()==tables['finance'].keys()==tables['performance'].keys()
    for key, commercial in tables['commercial'].items():
        finance, performance = tables['finance'][key], tables['performance'][key]
        assert commercial['bookings']<=commercial['arrivals']<=commercial['nights']
        assert commercial['seats']>=commercial['arrivals']
        assert finance['spent_mad']<=finance['committed_mad']<=finance['budget_mad']
        assert 0<performance['room_nights_sold']<=performance['room_nights_available']
        assert performance['room_revenue_mad']>0 and performance['clicks']<=performance['impressions']
    expected=REFERENCE['anchors']
    agadir=[r for r in tables['commercial'].values() if r['destination']=='Agadir' and r['period']=='2025-02-01']
    assert sum(r['nights'] for r in agadir)==expected['agadir_feb_2025']
    finance=[r for r in tables['finance'].values() if r['destination']=='Agadir' and r['period']=='2025-02-01']
    assert sum(r['budget_mad'] for r in finance)==expected['agadir_budget_feb_2025']
    assert sum(r['committed_mad'] for r in finance)==expected['agadir_committed_feb_2025']
    catalog=Catalog(ROOT/'config/sources.synthetic.json',root).describe(access())
    assert all(not s['quality_errors'] for s in catalog['sources'])
    assert all(r['valid'] and r['unmatched_keys']==0 for r in catalog['relations'])


def test_reproducible_decoded_data_and_seed_effect(corpus,tmp_path):
    root, manifest = corpus
    repeated=generate(tmp_path/'same',seed=manifest['seed'])
    changed=generate(tmp_path/'changed',seed=manifest['seed']+1)
    assert repeated['reference_status']=='pedagogical_final' and changed['reference_status']=='pedagogical_variant'
    assert [e['semantic_sha256'] for e in repeated['files']]==[e['semantic_sha256'] for e in manifest['files']]
    for entry in manifest['files']:
        assert read_rows(root/entry['file'])[0]==read_rows(tmp_path/'same'/entry['file'])[0]
    original={e['id']:e['semantic_sha256'] for e in manifest['files']}
    modified={e['id']:e['semantic_sha256'] for e in changed['files']}
    assert original['commercial']==modified['commercial']
    assert original['finance']!=modified['finance'] and original['performance']!=modified['performance']
    assert json.loads((root/'expected.json').read_text())==json.loads((tmp_path/'changed'/'expected.json').read_text())


@pytest.fixture(scope='module')
def oracle_qvd(tmp_path_factory):
    root=tmp_path_factory.mktemp('independent-calculation-oracle')
    # Entrées écrites à la main : aucun appel à generate(), calculate() ou _aggregate().
    for source, rows in REFERENCE['calculation_oracle']['sources'].items():
        write_qvd(root/f'{source}.qvd',rows)
    return root


@pytest.mark.parametrize('metric_id,expected',list(REFERENCE['calculation_oracle']['expected'].items()))
def test_all_metrics_against_independent_hand_calculated_oracle(oracle_qvd,tmp_path,metric_id,expected):
    oracle=REFERENCE['calculation_oracle']
    service=AnalyticsService(Catalog(ROOT/'config/sources.synthetic.json',oracle_qvd),AppState(tmp_path))
    result=service.run(AnalysisRequest(request_id='oracle',operation='value',metric_id=metric_id,
        period=oracle['period'],filters=oracle['filters'],language='fr'),access())
    assert result.status=='ok' and result.is_synthetic is True
    assert result.values['value']==expected
    assert result.unit==oracle['expected_units'][metric_id]
    assert all(s.source_type=='qvd' and s.version for s in result.sources)


def test_oracle_covers_current_catalog():
    assert set(REFERENCE['calculation_oracle']['expected']).issubset(METRICS)
    assert set(REFERENCE['calculation_oracle']['expected_units'])==set(REFERENCE['calculation_oracle']['expected'])
    for row in REFERENCE['calculation_oracle']['sources']['commercial']:
        assert row['bookings']<=row['arrivals']<=row['nights'] and row['seats']>=row['arrivals']
    for row in REFERENCE['calculation_oracle']['sources']['finance']:
        assert row['spent_mad']<=row['committed_mad']<=row['budget_mad']


def test_cross_domain_missing_key_blocks_ratio(tmp_path):
    from app.core.errors import AppError
    oracle=REFERENCE['calculation_oracle']
    for source, rows in oracle['sources'].items():
        write_qvd(tmp_path/f'{source}.qvd',rows[:1] if source=='finance' else rows)
    catalog=Catalog(ROOT/'config/sources.synthetic.json',tmp_path)
    relation=next(r for r in catalog.describe(access())['relations'] if r['right']=='finance')
    assert relation['valid'] is False and relation['unmatched_keys']==1
    service=AnalyticsService(catalog,AppState(tmp_path/'state'))
    with pytest.raises(AppError) as error:
        service.run(AnalysisRequest(request_id='mismatched-grain',operation='value',metric_id='spend_per_night',
            period=oracle['period'],filters=oracle['filters'],language='fr'),access())
    assert error.value.code=='data_quality'
