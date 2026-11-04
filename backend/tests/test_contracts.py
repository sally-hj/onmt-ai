import json

import pytest
from pydantic import ValidationError

from app.core.config import ROOT
from app.schemas.analysis import AnalysisRequest, AnalysisResult
from app.schemas.common import AccessContext, ErrorResponse, Period, SourceReference
from app.schemas.report import ReportRequest, ReportResult, ReportRevisionRequest

MODELS = {'analysis_request': AnalysisRequest, 'analysis_result': AnalysisResult,
          'analysis_result_forecast': AnalysisResult, 'report_request': ReportRequest,
          'report_result': ReportResult, 'report_revision_request': ReportRevisionRequest,
          'access_context': AccessContext, 'source_reference': SourceReference, 'error_response': ErrorResponse}


@pytest.mark.parametrize('name,model', MODELS.items())
def test_all_contract_examples(name, model):
    model.model_validate_json((ROOT / f'examples/contracts/{name}.json').read_text(encoding='utf-8'))


def test_no_unchecked_json_examples():
    assert {p.stem for p in (ROOT/'examples/contracts').glob('*.json')} == set(MODELS)


def test_period_order():
    with pytest.raises(ValidationError):
        Period(start='2025-02-02', end='2025-02-01')


def test_forecast_and_compare_fields():
    raw = json.loads((ROOT/'examples/contracts/analysis_request.json').read_text(encoding='utf-8'))
    raw['comparison_period'] = None
    with pytest.raises(ValidationError): AnalysisRequest.model_validate(raw)
    raw['operation'] = 'forecast'
    with pytest.raises(ValidationError): AnalysisRequest.model_validate(raw)
    raw.update(forecast_horizon=2, forecast_frequency='month')
    AnalysisRequest.model_validate(raw)
    raw['operation'] = 'value'
    with pytest.raises(ValidationError): AnalysisRequest.model_validate(raw)


def test_invalid_pages_and_citations():
    raw = json.loads((ROOT/'examples/contracts/source_reference.json').read_text(encoding='utf-8'))
    raw['pages'] = [0]
    with pytest.raises(ValidationError): SourceReference.model_validate(raw)
    raw = json.loads((ROOT/'examples/contracts/report_result.json').read_text(encoding='utf-8'))
    raw['sections'][0]['source_ids'] = ['invented']
    with pytest.raises(ValidationError): ReportResult.model_validate(raw)


def test_report_requires_analyses_and_no_browser_context(request_body):
    raw = request_body.model_dump()
    raw['analysis_ids'] = []
    with pytest.raises(ValidationError): ReportRequest.model_validate(raw)
    raw['analysis_ids'] = ['x']; raw['access_context'] = {'user_id': 'admin'}
    with pytest.raises(ValidationError): ReportRequest.model_validate(raw)
