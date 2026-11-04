"""python -m app.reports.demo : exemple local synthétique reproductible."""
from app.core.config import ROOT, Settings
from app.core.security import demo_access
from app.main import create_app
from app.schemas.report import ReportRequest, ReportRevisionRequest


def main():
    output = ROOT / 'local_data' / 'demo-reporting'
    app = create_app(Settings(data_dir=output, demo=True, demo_embeddings=True, ollama_model=''))
    request = ReportRequest.model_validate_json((ROOT / 'examples/contracts/report_request.json').read_text(encoding='utf-8'))
    service = app.state.reports
    report = service.create_report(request, demo_access())
    for i in range(5):
        report = service.revise_report(ReportRevisionRequest(request_id=f'demo_revision_{i}',report_id=report.report_id,
                                                           base_version=report.version, section_id='diagnostic',
                                                           instruction='résumer' if i%2==0 else 'détailler'),demo_access())
    report = service.export_pdf(report.report_id, demo_access(), app.state.exporter)
    (output/'rapport-synthetique.pdf').write_bytes(service.download_pdf(report.report_id,demo_access()))
    (output/'rapport-synthetique.json').write_text(report.model_dump_json(indent=2),encoding='utf-8')
    print(f'Rapport SYNTHETIQUE v{report.version} : {output}')


if __name__ == '__main__':
    main()
