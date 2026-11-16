"""Essais opt-in avec QVD, E5, Tesseract, Ollama et Chromium réels."""
import io
import json
import os
import platform
import subprocess
import time
from datetime import datetime,timezone

import pdfplumber
import pytest

from app.core.config import ROOT,Settings
from app.core.timing import trace
from app.main import create_app
from app.analytics.diagnostics import Diagnostics
from app.reports.demo_real import synthetic_mixed_pdf
from app.reports.documents import DocumentMetadata
from app.reports.library import prepare_library
from app.schemas.analysis import AnalysisRequest
from app.schemas.common import AccessContext
from app.schemas.report import ReportRequest,ReportRevisionRequest


def scope():
    return AccessContext(user_id='direction',roles=['report_editor','document_editor'],allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'])


@pytest.mark.full_models
def test_real_shared_library_survives_restart_and_does_not_publish_private_documents(tmp_path):
    if os.getenv('ONMT_TEST_COMPLETION_REAL')!='1': pytest.skip('ONMT_TEST_COMPLETION_REAL=1 requis.')
    settings=Settings(full_app=True,data_dir=tmp_path,ocr_enabled=True)
    app=create_app(settings)
    private,_=app.state.documents.ingest_pdf(synthetic_mixed_pdf(),DocumentMetadata(title='Méthode privée fictive',language='fr',synthetic=True),scope())
    first=prepare_library(app,scope()); second=prepare_library(app,scope())
    assert len(first)==len(second)==7 and all(row['status']=='unchanged' for row in second)
    assert {(r['document_id'],r['version']) for r in first}=={(r['document_id'],r['version']) for r in second}
    assert app.state.store.document(private.document_id)['policy']['private'] is True
    assert app.state.store.document(private.document_id)['policy']['shared_library'] is False
    regional=scope().model_copy(update={'user_id':'regional','allowed_modules':['reports','commercial','performance'],'allowed_territories':['Agadir','Marrakech']})
    found=app.state.retriever.search_evidence('Quelle différence entre les arrivées touristiques et le nombre de nuits passées ?',regional)
    assert found.evidence and all(e.passage.document_id!=private.document_id for e in found.evidence)
    # Nouveau processus Python : SQLite/Chroma sont relus, avec E5 local réel.
    code="from pathlib import Path; from app.core.config import Settings; from app.main import create_app; from app.schemas.common import AccessContext; import sys; a=create_app(Settings(full_app=True,data_dir=Path(sys.argv[1]))); s=AccessContext(user_id='regional',roles=['report_editor'],allowed_modules=['reports','commercial','performance'],allowed_territories=['Agadir','Marrakech']); r=a.state.retriever.search_evidence('difference entre arrivees touristiques et nuitees',s); print('PERSISTENT_EVIDENCE',len(r.evidence)); assert r.evidence; a.state.jobs.close()"
    env={**os.environ,'PYTHONPATH':str(ROOT/'backend')}
    completed=subprocess.run([os.sys.executable,'-c',code,str(tmp_path)],env=env,capture_output=True,text=True,timeout=180)
    assert completed.returncode==0,completed.stderr
    output=ROOT/'local_data/cps-completion-results';output.mkdir(exist_ok=True,parents=True)
    (output/'library-real.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'first':first,'second':second,
        'private_document_preserved':True,'fresh_process_result':completed.stdout,'regional_passages':len(found.evidence)},ensure_ascii=False,indent=2),encoding='utf-8')
    app.state.jobs.close()


@pytest.mark.full_models
def test_real_complete_note_deck_and_arabic_revision(tmp_path):
    if os.getenv('ONMT_TEST_COMPLETION_REAL')!='1': pytest.skip('ONMT_TEST_COMPLETION_REAL=1 requis.')
    app=create_app(Settings(full_app=True,data_dir=tmp_path,ocr_enabled=True,generation_mode='ollama',ollama_model='onmt-qwen25:3b',sources_config=ROOT/'config/sources.extended.json'))
    access=scope(); timings=[]; token=trace.set(timings); started=time.perf_counter()
    output=ROOT/'local_data/cps-completion-results';output.mkdir(exist_ok=True,parents=True)
    run={'at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
         'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),'python':platform.python_version(),'model':'onmt-qwen25:3b','mode':'real_models'}
    attempts=[]; original_generate=app.state.reports.writer.client.generate_json
    def capture(schema,system,payload):
        # Données exclusivement fictives de cet essai : conserver les refus et
        # sorties réelles pour diagnostiquer sans relancer tout le rapport.
        raw=original_generate(schema,system,payload)
        attempts.append({'section':payload['section'],'language':payload['language'],'raw':raw,
            'previous_error':payload.get('validation_feedback'),'metrics':app.state.reports.writer.client.last_metrics})
        (output/'pipeline-writer-attempts.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2),encoding='utf-8')
        return raw
    app.state.reports.writer.client.generate_json=capture
    try:
        document,_=app.state.documents.ingest_pdf(synthetic_mixed_pdf(),DocumentMetadata(title='Nuitées — méthodologie synthétique',language='fr',synthetic=True,kind='methodology'),access)
        assert any(p.extraction_method=='ocr' for p in document.passages)
        first=app.state.conversations.send('Compare les nuitées à Agadir en février 2025 et février 2024.',access)
        assert first['analysis']['values']=={'current':80000,'previous':100000,'change_pct':-20}
        request=AnalysisRequest(request_id='real-cps',operation='compare',metric_id='overnight_stays',period={'start':'2025-02-01','end':'2025-02-28'},
            comparison_period={'start':'2024-02-01','end':'2024-02-29'},filters={'destination':'Agadir'},language='fr')
        analyses=[app.state.analytics.get_analysis(first['analysis']['analysis_id'],access)]
        for metric in ['budget','spent','click_rate']:
            analyses.append(app.state.analytics.run(request.model_copy(update={'metric_id':metric}),access))
        tool=Diagnostics(app.state.analytics)
        diagnostics=[tool.international(request.period,request.comparison_period,access),tool.value_volume(request,access),tool.map(request,access),tool.scenario(request,access,-10)]
        diagnostics=[app.state.analytics.products.save(d,access) for d in diagnostics]
        assert diagnostics[-1]['scenario_value']==72000
        report=app.state.reports.create_report(ReportRequest(request_id='real-cps',analysis_ids=[a.analysis_id for a in analyses],
            diagnostic_ids=[d['diagnostic_id'] for d in diagnostics],title='Nuitées Agadir — méthode et comparaison synthétiques',
            question='Analyser les nuitées Agadir, leurs définitions, le budget et les limites.',language='fr',audience='direction',layout='strategic_15',
            sections=['summary','diagnostic','comparison','forecast','recommendations','limitations']),access)
        assert report.is_synthetic and any(s.source_type=='document' for s in report.sources)
        assert '80000 nuitees' in report.sections[0].content
        app.state.reports.export_pdf(report.report_id,access,app.state.exporter)
        note=app.state.reports.download_pdf(report.report_id,access)
        deck=app.state.reports.export_deck(report.report_id,access)
        for name,content,pages in [('note-real-fr.pdf',note,15),('deck-real-fr.pdf',deck,25)]:
            (output/name).write_bytes(content)
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                assert len(pdf.pages)==pages
                assert '80000' in '\n'.join(p.extract_text() or '' for p in pdf.pages)
        run.update(french_report_status='passed',report=report.model_dump(mode='json'))
        (output/'pipeline-real.json').write_text(json.dumps(run,ensure_ascii=False,indent=2),encoding='utf-8')
        revised=app.state.reports.revise_report(ReportRevisionRequest(request_id='real-ar',report_id=report.report_id,base_version=1,section_id='summary',instruction='langue:ar'),access)
        assert revised.version==2 and '80000 nuitees' in revised.sections[0].content
        assert any('\u0600'<=c<='\u06ff' for c in revised.sections[0].content)
        run.update(status='passed',report=report.model_dump(mode='json'),arabic_summary=revised.sections[0].model_dump(mode='json'))
    except Exception as exc:
        run.update(status='failed',error=str(exc));raise
    finally:
        run.update(seconds=time.perf_counter()-started,timings=timings)
        (output/'pipeline-real.json').write_text(json.dumps(run,ensure_ascii=False,indent=2),encoding='utf-8')
        trace.reset(token);app.state.jobs.close()
