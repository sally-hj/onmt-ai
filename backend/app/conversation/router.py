from fastapi import APIRouter, Request
from pydantic import Field

from app.core.errors import forbidden
from app.reports.router import Access
from app.schemas.common import Contract, Language
from app.core.errors import AppError

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


class JobMessage(Message):
    idempotency_key: str = Field(min_length=8,max_length=100)


@router.post('/jobs',status_code=202)
def submit(body: JobMessage,request: Request,access: Access):
    def work():
        # Réévaluer les droits du compte au moment de sortir de la file.
        with request.app.state.application_state.connect() as db:
            row=db.execute('SELECT access FROM users WHERE username=?',(access.user_id,)).fetchone()
        if not row: raise forbidden()
        from app.schemas.common import AccessContext
        current=AccessContext.model_validate_json(row[0])
        return request.app.state.conversations.send(body.message,current,body.conversation_id,body.base_version,body.language)
    return request.app.state.jobs.submit(access.user_id,body.idempotency_key,body.model_dump(mode='json'),work)


@router.get('/jobs/{job_id}')
def job(job_id: str,request: Request,access: Access):
    payload=request.app.state.jobs.get(job_id,access.user_id)
    result=payload.get('result') or {}
    request.app.state.conversations.authorize_response(result,access)
    return payload


@router.post('/jobs/{job_id}/cancel')
def cancel(job_id: str,request: Request,access: Access):
    return request.app.state.jobs.cancel(job_id,access.user_id)


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
        request.app.state.conversations.authorize_response(message,access)
    return result
