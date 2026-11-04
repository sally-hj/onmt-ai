from datetime import date
from typing import Literal

from pydantic import Field, StrictFloat, StrictInt, model_validator

from .common import Contract, Language, Period, SourceReference

Number = StrictInt | StrictFloat


class AnalysisRequest(Contract):
    request_id: str = Field(min_length=1)
    operation: Literal['value', 'compare', 'forecast']
    metric_id: str = Field(min_length=1)
    period: Period
    comparison_period: Period | None = None
    filters: dict
    language: Language
    forecast_horizon: int | None = Field(default=None, gt=0)
    forecast_frequency: Literal['month', 'quarter', 'year'] | None = None

    @model_validator(mode='after')
    def operation_fields(self):
        if self.operation == 'compare' and self.comparison_period is None:
            raise ValueError('comparison_period obligatoire')
        if self.operation == 'forecast':
            if self.forecast_horizon is None or self.forecast_frequency is None:
                raise ValueError('Horizon et fréquence obligatoires')
        elif self.forecast_horizon is not None or self.forecast_frequency is not None:
            raise ValueError('Champs forecast réservés aux prévisions')
        return self


class SeriesPoint(Contract):
    date: date
    value: Number | None
    kind: Literal['observed', 'forecast']
    lower: Number | None = None
    upper: Number | None = None

    @model_validator(mode='after')
    def bounds(self):
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError('Intervalle inversé')
        return self


class AnalysisResult(Contract):
    request_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    status: Literal['ok', 'partial', 'unavailable']
    period: Period
    comparison_period: Period | None = None
    filters: dict
    unit: str = Field(min_length=1)
    values: dict[str, Number | None]
    series: list[SeriesPoint]
    formula: str
    sources: list[SourceReference]
    warnings: list[str]
    is_synthetic: bool

    @model_validator(mode='after')
    def unavailable_warning(self):
        if self.status == 'unavailable' and not self.warnings:
            raise ValueError('Une indisponibilité doit être expliquée')
        return self
