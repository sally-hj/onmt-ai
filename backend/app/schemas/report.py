from typing import Literal

from pydantic import Field, model_validator

from .common import Contract, Language, SourceReference

SectionId = Literal['summary', 'diagnostic', 'comparison', 'forecast', 'recommendations', 'limitations']


class ReportRequest(Contract):
    request_id: str = Field(min_length=1, max_length=200)
    analysis_ids: list[str] = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=300)
    language: Language
    audience: Literal['direction', 'ministere', 'regional']
    sections: list[SectionId] = Field(min_length=1)

    @model_validator(mode='after')
    def unique(self):
        if len(set(self.sections)) != len(self.sections) or len(set(self.analysis_ids)) != len(self.analysis_ids):
            raise ValueError('Identifiants dupliqués')
        return self


class ReportSection(Contract):
    section_id: SectionId
    title: str
    content: str
    source_ids: list[str]


class ReportResult(Contract):
    request_id: str
    report_id: str
    version: int = Field(gt=0)
    status: Literal['pending', 'running', 'completed', 'failed']
    sections: list[ReportSection]
    sources: list[SourceReference]
    download_path: str | None
    warnings: list[str]
    is_synthetic: bool

    @model_validator(mode='after')
    def references(self):
        ids = {s.source_id for s in self.sources}
        if len(ids) != len(self.sources):
            raise ValueError('source_id ambigu')
        if any(set(s.source_ids) - ids for s in self.sections):
            raise ValueError('Référence de section inconnue')
        return self


class ReportRevisionRequest(Contract):
    request_id: str = Field(min_length=1, max_length=200)
    report_id: str = Field(min_length=1)
    base_version: int = Field(gt=0)
    section_id: SectionId
    instruction: str = Field(min_length=1, max_length=2000)
