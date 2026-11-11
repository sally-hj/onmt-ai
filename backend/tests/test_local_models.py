"""Essais réels opt-in ; aucune API IA payante, corpus et analyses exclusivement fictifs."""
import io
import json
import os
from dataclasses import replace

import pdfplumber
import pytest

from app.core.config import ROOT, Settings
from app.core.security import demo_access
from app.main import create_app
from app.reports.documents import DocumentMetadata
from app.reports.ocr import LocalOCR
from app.schemas.report import ReportRequest, ReportRevisionRequest
from conftest import text_pdf
from local_fixtures import scanned_pdf


@pytest.fixture
def real_settings(tmp_path):
    if os.getenv('ONMT_TEST_LOCAL_AI') != '1':
        pytest.skip('ONMT_TEST_LOCAL_AI=1 requis pour les essais réels E5/OCR/Ollama.')
    return Settings(data_dir=tmp_path, demo=True, demo_embeddings=False, ocr_enabled=True,
                    ollama_model=os.getenv('ONMT_REAL_OLLAMA_MODEL', 'onmt-qwen25:3b'), generation_mode='ollama')


@pytest.mark.local_ai
def test_real_ocr_french_english_arabic_and_mixed_pdf(real_settings):
    pages = [('Les voyageurs passent des nuits dans les hôtels. Total provisoire 12345.', 'fr'),
             ('Tourists spend the night in accommodation. Draft amount 12345.', 'en'),
             ('يقضي السياح عدة ليال في الفنادق خلال العطلة', 'ar')]
    scanned = scanned_pdf(pages)
    with pdfplumber.open(io.BytesIO(scanned)) as pdf:
        assert all(not p.extract_text().strip() for p in pdf.pages)
    texts = []
    for index, language in enumerate(['fra', 'eng', 'ara']):
        text, confidence, warnings = LocalOCR(replace(real_settings, ocr_languages=language)).extract_page(scanned, index)
        texts.append(text)
        assert text.strip() and confidence is not None
        assert 'ocr_requires_human_review' in warnings
    assert 'voyageurs' in texts[0].casefold() and '12345' in texts[0]
    assert 'tourists' in texts[1].casefold()
    assert any('\u0600' <= c <= '\u06ff' for c in texts[2])
    import pypdfium2
    mixed = pypdfium2.PdfDocument.new()
    for data in [text_pdf(['Synthetic hotel methodology.']), scanned]:
        with pypdfium2.PdfDocument(data) as source:
            mixed.import_pages(source)
    output = io.BytesIO(); mixed.save(output); mixed.close()
    app = create_app(replace(real_settings, generation_mode='template'))
    doc, _ = app.state.documents.ingest_pdf(output.getvalue(), DocumentMetadata(title='Corpus fictif mixte', language='fr'), demo_access())
    assert doc.passages[0].extraction_method == 'text'
    assert {p.page_start for p in doc.passages if p.extraction_method == 'ocr'} == {2, 3, 4}


@pytest.mark.local_ai
def test_real_semantic_paraphrases_and_forbidden_documents(real_settings):
    app = create_app(replace(real_settings, generation_mode='template'))
    access = demo_access()
    notes = [('stay', 'Les établissements hébergent les visiteurs pendant leur séjour. Les nuitées dénombrent les nuits passées dans ces hébergements.'),
             ('budget', 'Les dépenses publicitaires financent les annonces et les actions de communication touristique.'),
             ('flight', 'Les liaisons aériennes connectent les aéroports au moyen de lignes régulières et de sièges disponibles.')]
    # PDF Unicode construit par Chromium, avec texte sélectionnable.
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            for name, text in notes:
                page.set_content('<meta charset="utf-8"><p>'+text+'</p>')
                app.state.documents.ingest_pdf(page.pdf(), DocumentMetadata(title=name, language='fr'), access)
        finally:
            browser.close()
    questions = [('Où les vacanciers dorment-ils durant leurs vacances ?', 'stay'),
                 ('Quel moyen de transport permet de rejoindre une destination par avion ?', 'flight'),
                 ('Comment sont payées les campagnes de promotion ?', 'budget')]
    for question, expected in questions:
        found = app.state.retriever.search_evidence(question, access)
        assert found.evidence and found.evidence[0].source.name == expected
        assert all(e.passage.version == 1 for e in found.evidence)
    assert not app.state.retriever.search_evidence('What is the ionization energy of neon?', access).evidence
    forbidden = access.model_copy(update={'allowed_territories': ['Marrakech']})
    assert app.state.retriever.search_evidence(questions[0][0], forbidden).evidence == []


@pytest.mark.local_ai
def test_real_pipeline_ocr_e5_ollama_revision_and_pdf(real_settings):
    app = create_app(real_settings)
    access = demo_access()
    doc, _ = app.state.documents.ingest_pdf(scanned_pdf([
        ('Les nuitées mesurent les nuits passées dans un hébergement touristique. La saisonnalité nécessite une étude dédiée.', 'fr')]),
        DocumentMetadata(title='Définition fictive des nuitées', language='fr'), access)
    assert any(p.extraction_method == 'ocr' for p in doc.passages)
    body = ReportRequest(request_id='real-local-smoke', analysis_ids=['ana_demo_compare'],
                         title='Séjours touristiques et hébergement à Agadir', language='fr', audience='direction',
                         sections=['summary'])
    # Journaux de test exclusivement synthétiques, jamais activés dans le code applicatif.
    original_call = app.state.reports.writer.client.generate_json
    trace = []
    output = ROOT/'local_data/real-ai-results'; output.mkdir(parents=True, exist_ok=True)
    def capture(schema, system, payload):
        raw = original_call(schema, system, payload)
        trace.append({'language': payload['language'], 'style': payload['style'], 'raw': raw})
        (output/'synthetic-llm-trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
        return raw
    app.state.reports.writer.client.generate_json = capture
    result = app.state.reports.create_report(body, access)
    assert result.is_synthetic
    assert any(s.source_type == 'document' for s in result.sources)
    assert '80000 nuitees' in result.sections[0].content and '-20 %' in result.sections[0].content
    assert '{{' not in result.sections[0].content
    # Conserver une preuve indépendante du parcours français avant la traduction.
    result = app.state.reports.export_pdf(result.report_id, access, app.state.exporter)
    (output/'rapport-fr-modeles-reels.pdf').write_bytes(app.state.reports.download_pdf(result.report_id, access))
    (output/'rapport-fr-modeles-reels.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
    # Une révision réelle représentative ; toutes les opérations sont couvertes sans modèle dans test_narrative.py.
    for instruction in ['langue:ar']:
        result = app.state.reports.revise_report(ReportRevisionRequest(request_id='real-revise', report_id=result.report_id,
                    base_version=result.version, section_id='summary', instruction=instruction), access)
    assert result.version == 2
    assert any('\u0600' <= c <= '\u06ff' for c in result.sections[0].content)
    manifest = app.state.store.report(result.report_id)['narratives']['summary']
    generated = ' '.join(manifest['editorial_output']['introductions'].values())
    assert any('\u0600' <= c <= '\u06ff' for c in generated)
    assert '80000 nuitees' in result.sections[0].content
    with pytest.raises(Exception):
        app.state.reports.revise_report(ReportRevisionRequest(request_id='stale', report_id=result.report_id,
                    base_version=1, section_id='summary', instruction='résumer'), access)
    result = app.state.reports.export_pdf(result.report_id, access, app.state.exporter)
    pdf = app.state.reports.download_pdf(result.report_id, access)
    with pdfplumber.open(io.BytesIO(pdf)) as document:
        assert '80000' in '\n'.join(p.extract_text() or '' for p in document.pages)
    output = ROOT/'local_data/real-ai-results'; output.mkdir(parents=True, exist_ok=True)
    (output/'rapport-reel-modeles-donnees-fictives.pdf').write_bytes(pdf)
    (output/'rapport-reel-modeles-donnees-fictives.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
    (output/'generation-manifest.json').write_text(json.dumps(app.state.store.report(result.report_id)['narratives'],
                                                           ensure_ascii=False, indent=2), encoding='utf-8')
