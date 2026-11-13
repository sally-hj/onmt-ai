"""Fusion contrôlée d'une relance avec les paramètres de la dernière analyse."""
from uuid import uuid4

from app.core.errors import AppError
from app.schemas.analysis import AnalysisRequest


def analysis_request(intent, context):
    previous = context.get('analysis_request',{})
    operation = intent.operation or previous.get('operation') or 'value'
    filters = dict(previous.get('filters',{}))
    if intent.destination is not None:
        filters['destination'] = intent.destination
    if intent.market is not None:
        filters['market'] = intent.market
    period = intent.period or previous.get('period')
    comparison = intent.comparison_period or previous.get('comparison_period')
    metric = intent.metric_id or previous.get('metric_id')
    if not metric or not period or (operation == 'compare' and not comparison):
        return None
    return AnalysisRequest(request_id=uuid4().hex,operation=operation,metric_id=metric,period=period,
            comparison_period=comparison if operation == 'compare' else None,filters=filters,language=intent.language,
            forecast_horizon=(intent.horizon or previous.get('forecast_horizon') or 6) if operation=='forecast' else None,
            forecast_frequency='month' if operation=='forecast' else None)
