"""Rendu Chromium réel ; rédaction par gabarits explicitement configurée pour isoler l'export."""
import io
import os
import pdfplumber
import pytest

from app.core.config import ROOT,Settings
from app.data_access.synthetic import generate,DESTINATIONS
from app.main import create_app
from app.schemas.analysis import AnalysisRequest
from app.schemas.report import ReportRequest
from app.schemas.common import AccessContext
from app.reports.presentation import build_slides


@pytest.mark.browser
@pytest.mark.parametrize('language',['fr','ar'])
def test_native_qvd_report_deck_25_pages_access_and_synthetic_marker(tmp_path,language):
    if os.getenv('ONMT_TEST_PRESENTATION')!='1': pytest.skip('ONMT_TEST_PRESENTATION=1 pour le rendu Chromium réel.')
    generate(tmp_path/'qvd')
    app=create_app(Settings(full_app=True,data_dir=tmp_path/'state',qvd_root=tmp_path/'qvd',demo=True,demo_embeddings=True,generation_mode='template',ollama_model=''))
    access=AccessContext(user_id='direction',roles=['report_editor','document_editor'],allowed_modules=['reports','commercial','finance','performance'],allowed_territories=DESTINATIONS)
    analyses=[]
    for metric in ['overnight_stays','budget','spent','click_rate']:
        analyses.append(app.state.analytics.run(AnalysisRequest(request_id='deck',operation='compare',metric_id=metric,
            period={'start':'2025-02-01','end':'2025-02-28'},comparison_period={'start':'2024-02-01','end':'2024-02-29'},filters={'destination':'Agadir'},language=language),access))
    from app.data_access.supplement import prepare
    from app.analytics.diagnostics import Diagnostics
    prepare(tmp_path/'qvd')
    tool=Diagnostics(app.state.analytics)
    analysis_request=AnalysisRequest(request_id='diagnostic-deck',operation='value',metric_id='overnight_stays',period=analyses[0].period,
        comparison_period=analyses[0].comparison_period,filters={'destination':'Agadir'},language=language)
    matrix=tool.international(analysis_request.period,analysis_request.comparison_period,access,regional=language=='ar')
    diagnostics=[app.state.analytics.products.save(d,access) for d in [matrix,tool.value_volume(analysis_request,access),tool.map(analysis_request,access),tool.scenario(analysis_request,access,-10)]]
    report=app.state.reports.create_report(ReportRequest(request_id='deck',analysis_ids=[a.analysis_id for a in analyses],title='Agadir — corpus synthétique',language=language,
        diagnostic_ids=[d['diagnostic_id'] for d in diagnostics],audience='direction',layout='strategic_15',sections=['summary','diagnostic','comparison','forecast','recommendations','limitations']),access)
    payload=app.state.store.report(report.report_id)
    assert len(build_slides(payload))==25
    content=app.state.reports.export_deck(report.report_id,access)
    assert content==app.state.reports.export_deck(report.report_id,access)
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        assert len(pdf.pages)==25
        texts=[p.extract_text() or '' for p in pdf.pages]
        assert all(t.strip() for t in texts)
        assert '80000' in '\n'.join(texts)
        assert 'commercial.qvd' in '\n'.join(texts)
        if language=='fr': assert all('SYNTHÉTIQUES' in text for text in texts)
    from app.core.errors import AppError
    with pytest.raises(AppError): app.state.reports.export_deck(report.report_id,access.model_copy(update={'user_id':'other'}))
    directory=ROOT/'local_data/cps-completion-results';directory.mkdir(exist_ok=True,parents=True)
    (directory/f'deck-native-{language}.pdf').write_bytes(content)
    app.state.reports.export_pdf(report.report_id,access,app.state.exporter)
    note=app.state.reports.download_pdf(report.report_id,access)
    with pdfplumber.open(io.BytesIO(note)) as pdf:
        assert len(pdf.pages)==15
        assert '80000' in '\n'.join(p.extract_text() or '' for p in pdf.pages)
    (directory/f'note-15-native-{language}.pdf').write_bytes(note)
    app.state.jobs.close()
