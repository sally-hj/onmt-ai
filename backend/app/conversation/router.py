from fastapi import APIRouter, Request
from pydantic import Field

from app.core.errors import forbidden
from app.reports.router import Access
from app.schemas.common import Contract, Language

router = APIRouter(prefix='/api/conversations',tags=['Hayat — conversation'])


class Message(Contract):
    message: str = Field(min_length=1,max_length=4000)
    conversation_id: str | None = None
    base_version: int = Field(default=0,ge=0)
    language: Language = 'fr'


class ContextLink(Contract):
    conversation_id: str | None = None
    base_version: int = Field(ge=0)
    analysis_id: str | None = None
    report_id: str | None = None


@router.post('/context')
def link(body: ContextLink,request: Request,access: Access):
    return request.app.state.conversations.link_context(access,body.conversation_id,body.base_version,body.analysis_id,body.report_id)


@router.post('/messages')
def send(body: Message,request: Request,access: Access):
    return request.app.state.conversations.send(body.message,access,body.conversation_id,body.base_version,body.language)


@router.get('/{conversation_id}')
def read(conversation_id: str,request: Request,access: Access):
    result = request.app.state.application_state.conversation(conversation_id,access.user_id)
    if not result:
        raise forbidden()
    # Ne pas réexposer un ancien résultat après révocation d'un droit ou changement de source.
    for message in result['messages']:
        for analysis in message.get('benchmark',[]):
            request.app.state.analytics.get_analysis(analysis['analysis_id'],access)
        if message.get('analysis'):
            request.app.state.analytics.get_analysis(message['analysis']['analysis_id'],access)
        if message.get('report'):
            request.app.state.reports.get_report(message['report']['report_id'],access)
    return result
