from pydantic import Field

from app.schemas.common import AccessContext, Contract
from .errors import forbidden


class ResourcePolicy(Contract):
    owner_id: str
    roles: list[str] = Field(min_length=1)
    modules: list[str] = Field(min_length=1)
    territories: list[str] = Field(min_length=1)
    classification: str = 'internal'


def require_module(access: AccessContext, edit: bool = False):
    if ('reports' not in access.allowed_modules or not access.roles or not access.allowed_territories
            or (edit and 'report_editor' not in access.roles)):
        raise forbidden()


def can_read(policy: ResourcePolicy, access: AccessContext) -> bool:
    return (bool(set(policy.roles) & set(access.roles))
            and set(policy.modules).issubset(access.allowed_modules)
            and set(policy.territories).issubset(access.allowed_territories))


def authorize(policy: ResourcePolicy, access: AccessContext, edit: bool = False):
    require_module(access, edit)
    if not can_read(policy, access) or (edit and policy.owner_id != access.user_id):
        raise forbidden()


def private_policy(access: AccessContext) -> ResourcePolicy:
    require_module(access, True)
    return ResourcePolicy(owner_id=access.user_id, roles=['report_editor'], modules=['reports'],
                          territories=access.allowed_territories)


def demo_access() -> AccessContext:
    return AccessContext(user_id='salma-demo', roles=['report_editor', 'document_editor'],
                         allowed_modules=['reports', 'commercial'], allowed_territories=['Agadir'])
