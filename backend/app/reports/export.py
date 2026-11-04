from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.errors import AppError
from app.schemas.analysis import AnalysisResult
from .generation import TEXT, facts


class PDFExporter:
    def render(self, payload):
        from playwright.sync_api import sync_playwright
        request = payload['request']
        analyses = [AnalysisResult.model_validate(a) for a in payload['analyses']]
        rows = facts(analyses)
        plots = []
        for a in analyses:
            values = [p.value for p in a.series if p.value is not None]
            if not values or not a.sources or a.status == 'unavailable':
                continue
            low, high = min(0, min(values)), max(0, max(values))
            span = high-low or 1
            # Petits panneaux lisibles ; toutes les lignes restent disponibles dans le tableau.
            for start in range(0,len(a.series),10):
                panel=a.series[start:start+10]
                points = [{'x': 40 + i*620/max(1, len(panel)-1), 'y': 160 - (p.value-low)/span*125,
                           'date': str(p.date), 'value': p.value, 'kind': p.kind}
                          for i,p in enumerate(panel) if p.value is not None]
                if points:
                    plots.append({'title': a.metric_id, 'unit': a.unit, 'points': points})
        env = Environment(loader=FileSystemLoader(Path(__file__).parent / 'templates'),
                          autoescape=select_autoescape(['html']))
        html = env.get_template('report.html').render(payload=payload, report=payload['result'], request=request,
                                                    rows=rows, plots=plots, analyses=analyses, t=TEXT[request['language']],
                                                    rtl=request['language'] in ['ar', 'ary'])
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    context = browser.new_context(java_script_enabled=False, service_workers='block')
                    context.route('**/*', lambda route: route.abort())
                    page = context.new_page()
                    page.set_content(html, wait_until='load')
                    return page.pdf(format='A4', print_background=True, display_header_footer=True,
                                    header_template='<span></span>',
                                    footer_template='<div style="font-size:9px;width:100%;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                                    margin={'top': '16mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'})
                finally:
                    browser.close()
        except Exception as exc:
            raise AppError('tool_failed', 'Export PDF indisponible. Vérifiez Chromium : python -m playwright install chromium.', 503) from exc
