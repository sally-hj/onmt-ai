"""Parcours local réel sur un PDF mixte et des analyses entièrement fictives."""
import argparse
import io
import json

from PIL import Image
import pypdfium2
from playwright.sync_api import sync_playwright

from app.core.config import ROOT, Settings
from app.core.security import demo_access
from app.main import create_app
from app.schemas.report import ReportRequest, ReportRevisionRequest
from .documents import DocumentMetadata


def synthetic_mixed_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={'width': 1400, 'height': 900})
            page.route('**/*', lambda route: route.abort())
            page.set_content('<meta charset="utf-8"><h1>Note de méthode entièrement fictive</h1>'
                             '<p>Les nuitées mesurent les nuits passées par les visiteurs dans les hébergements touristiques.</p>')
            textual = page.pdf()
            page.set_content('<meta charset="utf-8"><body style="font:38px Arial;padding:90px;line-height:1.8">'
                             'Exemple fictif scanné. Les séjours doivent être décrits selon leur période et leur territoire. '
                             'Une variation seule ne démontre pas la cause d’un résultat.</body>')
            image = Image.open(io.BytesIO(page.screenshot())).convert('RGB')
            scanned = io.BytesIO()
            image.save(scanned, format='PDF', resolution=150)
            image.close()
        finally:
            browser.close()
    merged = pypdfium2.PdfDocument.new()
    for content in [textual, scanned.getvalue()]:
        with pypdfium2.PdfDocument(content) as pdf:
            merged.import_pages(pdf)
    output = io.BytesIO()
    merged.save(output)
    merged.close()
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sections', nargs='+', default=['summary'],
                        choices=['summary', 'diagnostic', 'comparison', 'forecast', 'recommendations', 'limitations'])
    parser.add_argument('--revise', choices=['reformuler', 'langue:ar', 'adapter:ministere'])
    args = parser.parse_args()
    output = ROOT / 'local_data' / 'demo-real-ai'
    settings = Settings(data_dir=output, demo=True, demo_embeddings=False, ocr_enabled=True,
                        ollama_model='onmt-qwen25:3b', generation_mode='ollama')
    app = create_app(settings)
    access = demo_access()
    pdf = synthetic_mixed_pdf()
    (output / 'corpus-fictif-mixte.pdf').write_bytes(pdf)
    doc, duplicate = app.state.documents.ingest_pdf(pdf, DocumentMetadata(title='Méthode fictive — séjours', language='fr'), access)
    print(f'Document {doc.document_id}, v{doc.version}, OCR et extraction directe, doublon={duplicate}', flush=True)
    body = ReportRequest(request_id='demo-real-local', analysis_ids=['ana_demo_compare', 'ana_demo_forecast'],
                         title='Séjours touristiques et hébergement à Agadir', language='fr', audience='direction', sections=args.sections)
    report = app.state.reports.create_report(body, access)
    if args.revise:
        report = app.state.reports.revise_report(ReportRevisionRequest(request_id='demo-real-revision',report_id=report.report_id,
                        base_version=report.version,section_id=args.sections[0],instruction=args.revise), access)
    report = app.state.reports.export_pdf(report.report_id,access,app.state.exporter)
    (output / 'rapport-donnees-fictives-modeles-reels.pdf').write_bytes(app.state.reports.download_pdf(report.report_id,access))
    (output / 'rapport-donnees-fictives-modeles-reels.json').write_text(report.model_dump_json(indent=2),encoding='utf-8')
    print('Modèles réels ; données SYNTHÉTIQUES ; résultat :',output,flush=True)


if __name__ == '__main__':
    main()
