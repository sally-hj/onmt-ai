"""Intégration réelle opt-in : PyQvd, Tesseract, E5, Ollama, LangGraph et PDF."""
import io
import json
import os
import re

import pdfplumber
import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT,Settings
from app.core.errors import AppError
from app.core.llm_client import OllamaPlanner
from app.main import create_app
from app.reports.demo_real import synthetic_mixed_pdf
from app.schemas.common import AccessContext
from app.schemas.analysis import AnalysisRequest
from app.schemas.report import ReportRequest


@pytest.mark.full_models
def test_qvd_conversation_report_ocr_revision_and_pdf_real(tmp_path):
    if os.getenv('ONMT_TEST_FULL_REAL')!='1':
        pytest.skip('ONMT_TEST_FULL_REAL=1 : nécessite outils et poids réellement installés.')
    app = create_app(Settings(full_app=True,data_dir=tmp_path,demo=False,demo_embeddings=False,
            generation_mode='ollama',ollama_model='onmt-qwen25:3b',ocr_enabled=True))
    artifacts = ROOT/'local_data/full-app-results';artifacts.mkdir(parents=True,exist_ok=True)
    editorial_trace=[]
    original=app.state.reports.writer.client.generate_json
    def capture(schema,system,payload):
        raw=original(schema,system,payload)
        editorial_trace.append({'language':payload['language'],'raw':raw})
        (artifacts/'editorial-synthetique.json').write_text(json.dumps(editorial_trace,ensure_ascii=False,indent=2),encoding='utf-8')
        return raw
    app.state.reports.writer.client.generate_json=capture
    with TestClient(app) as client:
        assert client.post('/api/auth/login',json={'username':'direction','password':'OnmtLocal!2026'}).status_code==200
        corpus = synthetic_mixed_pdf()
        (artifacts/'corpus-fictif.pdf').write_bytes(corpus)
        uploaded = client.post('/api/documents',files={'file':('corpus.pdf',corpus,'application/pdf')},
                               data={'metadata':json.dumps({'title':'Méthode fictive des nuitées','language':'fr'})})
        assert uploaded.status_code==201,uploaded.text
        assert any('ocr_requires_human_review' in w for w in uploaded.json()['document']['warnings'])
        turns = []
        def send(message):
            payload = {'message':message}
            if turns:
                payload.update(conversation_id=turns[-1]['conversation_id'],base_version=turns[-1]['version'])
            response = client.post('/api/conversations/messages',json=payload)
            assert response.status_code==200,response.text
            turn=response.json();turns.append(turn)
            (artifacts/'conversation-synthetique.json').write_text(json.dumps(turns,ensure_ascii=False,indent=2),encoding='utf-8')
            return turn
        first = send('Compare les nuitées à Agadir en février 2025 et février 2024.')
        assert first['analysis']['values']=={'current':80000,'previous':100000,'change_pct':-20}
        second = send('Et pour Marrakech ?')
        assert second['analysis']['values']=={'current':165000,'previous':150000,'change_pct':10}
        report = send('Prépare un rapport pour la direction.')
        assert report.get('report'),report
        assert not re.search(r'\b[xyz]\b',report['report']['sections'][0]['content'],re.I)
        rid = report['report']['report_id']
        exported = client.post(f'/api/reports/{rid}/export').json()
        pdf = client.get(exported['download_path']).content
        (artifacts/'rapport-qvd-fr.pdf').write_bytes(pdf)
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            assert '165000' in '\n'.join(p.extract_text() or '' for p in doc.pages)
        arabic = send('Traduis la synthèse en arabe.')
        assert arabic['report']['version']==2
        assert any('\u0600'<=c<='\u06ff' for c in arabic['report']['sections'][0]['content'])
        exported = client.post(f'/api/reports/{rid}/export').json()
        (artifacts/'rapport-qvd-ar.pdf').write_bytes(client.get(exported['download_path']).content)
        assert any(s['source_type']=='document' for s in arabic['report']['sources'])
        with pytest.raises(AppError) as error:
            OllamaPlanner('onmt-deliberately-missing-model').generate_json({'type':'object'},'Test local.',{})
        assert error.value.code=='missing_data'


@pytest.mark.full_models
def test_real_native_territorial_benchmark_from_chat(tmp_path):
    if os.getenv('ONMT_TEST_FULL_REAL')!='1':
        pytest.skip('ONMT_TEST_FULL_REAL=1 requis pour appeler réellement le modèle.')
    app=create_app(Settings(full_app=True,data_dir=tmp_path,demo=False,demo_embeddings=False,
        generation_mode='ollama',ollama_model='onmt-qwen25:3b',ocr_enabled=True))
    access=AccessContext(user_id='direction',roles=['report_editor','document_editor'],
        allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech'])
    output=ROOT/'local_data/full-app-results/benchmark-synthetique.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    original=app.state.conversations.parser.client.generate_json
    def capture(schema,system,payload):
        raw=original(schema,system,payload)
        (output.parent/'benchmark-intent.json').write_text(raw,encoding='utf-8')
        return raw
    app.state.conversations.parser.client.generate_json=capture
    result=app.state.conversations.send('Compare les nuitées à Agadir et Marrakech en février 2025.',access)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert [a['values']['value'] for a in result['benchmark']]==[80000,165000]
    assert [a['filters']['destination'] for a in result['benchmark']]==['Agadir','Marrakech']


@pytest.mark.full_models
def test_real_arabic_nights_cannot_claim_arrival_counts(tmp_path):
    if os.getenv('ONMT_TEST_FULL_REAL')!='1':
        pytest.skip('ONMT_TEST_FULL_REAL=1 requis pour le contrôle de rédaction réel.')
    app=create_app(Settings(full_app=True,data_dir=tmp_path,demo=False,demo_embeddings=False,
        generation_mode='ollama',ollama_model='onmt-qwen25:3b',ocr_enabled=True))
    access=AccessContext(user_id='direction',roles=['report_editor','document_editor'],
        allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech'])
    analysis=app.state.analytics.run(AnalysisRequest(request_id='ar-grounding',operation='compare',metric_id='overnight_stays',
        period={'start':'2025-02-01','end':'2025-02-28'},comparison_period={'start':'2024-02-01','end':'2024-02-29'},
        filters={'destination':'Marrakech'},language='ar'),access)
    result=app.state.reports.create_report(ReportRequest(request_id='ar-grounded-report',analysis_ids=[analysis.analysis_id],
        title='Nuitées à Marrakech — comparaison de périodes',language='ar',audience='direction',sections=['summary']),access)
    assert '165000 nuitees' in result.sections[0].content
    assert not re.search('عدد الزوار|عدد السياح',result.sections[0].content)
    result=app.state.reports.export_pdf(result.report_id,access,app.state.exporter)
    output=ROOT/'local_data/full-app-results'
    (output/'rapport-ar-controle-semantique.pdf').write_bytes(app.state.reports.download_pdf(result.report_id,access))
    (output/'rapport-ar-controle-semantique.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
