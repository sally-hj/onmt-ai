from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Language = Literal['fr', 'ar', 'ary', 'en', 'es']


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Period(Contract):
    start: date
    end: date

    @model_validator(mode='after')
    def ordered(self):
        if self.start > self.end:
            raise ValueError('start doit précéder end')
        return self


class SourceReference(Contract):
    source_id: str = Field(min_length=1)
    source_type: Literal['qvd', 'document', 'external']
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    fields: list[str]
    pages: list[int] = Field(default_factory=list)

    @model_validator(mode='after')
    def pages_valid(self):
        if any(p < 1 for p in self.pages):
            raise ValueError('Les pages commencent à 1')
        return self


class AccessContext(Contract):
    user_id: str = Field(min_length=1)
    roles: list[str]
    allowed_modules: list[str]
    allowed_territories: list[str]


class ErrorResponse(Contract):
    request_id: str
    code: str
    message: str
