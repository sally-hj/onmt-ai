"""KPI persistants : deux sommes et une opération autorisée, confirmation séparée."""
import hashlib
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import Field
from typing import Literal

from app.core.errors import AppError, forbidden
from app.schemas.common import Contract
from .metrics import Metric, FIELD_UNITS


class Term(Contract):
    source: str = Field(pattern=r'^[a-z_]{1,40}$')
    field: str = Field(pattern=r'^[a-z_]{1,40}$')
    market: str | None = Field(default=None, max_length=80)


class KpiDefinition(Contract):
    id: str = Field(pattern=r'^custom_[a-z][a-z0-9_]{2,50}$')
    label: str = Field(min_length=3,max_length=100)
    numerator: Term
    denominator: Term
    operation: Literal['ratio','percent','difference']
    interpretation: str = Field(min_length=10,max_length=500)


def term_sum(term, data):
    return sum(row[term.field] for row in data[term.source] if term.market is None or row['market']==term.market)


class CustomKpis:
    def __init__(self, state, catalog):
        self.state,self.catalog=state,catalog
        with state.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS custom_kpis(id TEXT, version INTEGER, author TEXT, status TEXT, payload TEXT, PRIMARY KEY(id,version))')

    def validate(self, spec, access,write=False):
        if write and 'report_editor' not in access.roles:
            raise forbidden()
        units=[]
        for term in [spec.numerator,spec.denominator]:
            source=self.catalog.sources.get(term.source)
            if not source or source['module'] not in access.allowed_modules:
                raise forbidden()
            if term.field in ['key','month','destination','market'] or term.field not in source['units']:
                raise AppError('invalid_request','Champ numérique déclaré requis.',422)
            units.append(source['units'][term.field])
            if term.market:
                rows,_=self.catalog.read_authorized_data(term.source,['market'],{},access)
                if term.market not in {r['market'] for r in rows}:
                    raise AppError('invalid_request','Marché inconnu sur le périmètre autorisé.',422)
        if spec.operation in ['percent','difference'] and units[0]!=units[1]:
            raise AppError('invalid_request','Pourcentage ou différence : unités identiques requises.',422)
        if spec.operation=='difference' and spec.numerator.market != spec.denominator.market:
            raise AppError('invalid_request','Différence : périmètres des deux termes identiques requis.',422)
        return '%' if spec.operation=='percent' else units[0] if spec.operation=='difference' else f'{units[0]}/{units[1]}'

    def metric(self, payload):
        spec=KpiDefinition.model_validate(payload['definition'])
        fields={}
        for term in [spec.numerator,spec.denominator]:
            fields.setdefault(term.source,[])
            if term.field not in fields[term.source]: fields[term.source].append(term.field)
        def label(term):
            return f'SUM({term.source}.{term.field}'+(f' WHERE market = {term.market!r}' if term.market else '')+')'
        formula=f'{label(spec.numerator)} '+('-' if spec.operation=='difference' else '/')+f' {label(spec.denominator)}'
        if spec.operation=='percent': formula='100 * ('+formula+')'
        return Metric(spec.id,spec.label,payload['unit'],fields,formula,'custom',spec.interpretation,expression=spec.model_dump(),version=payload['version'])

    def list(self, access):
        with self.state.connect() as db:
            rows=db.execute("SELECT payload FROM custom_kpis c WHERE status='active' AND version=(SELECT MAX(version) FROM custom_kpis WHERE id=c.id AND status='active')").fetchall()
        result=[]
        for row in rows:
            payload=json.loads(row[0])
            try: self.validate(KpiDefinition.model_validate(payload['definition']),access)
            except AppError: continue
            result.append(payload)
        return result

    def propose(self, spec, access):
        unit=self.validate(spec,access,write=True)
        with self.state.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(DISTINCT id) FROM custom_kpis').fetchone()[0]>=64:
                raise AppError('invalid_request','Catalogue personnalisé limité à 64 indicateurs locaux.',422)
            row=db.execute('SELECT MAX(version) FROM custom_kpis WHERE id=?',(spec.id,)).fetchone()
            version=(row[0] or 0)+1
            if version>1:
                author=db.execute('SELECT author FROM custom_kpis WHERE id=? ORDER BY version DESC LIMIT 1',(spec.id,)).fetchone()[0]
                if author!=access.user_id: raise forbidden()
            payload={'proposal_id':uuid4().hex,'definition':spec.model_dump(),'unit':unit,'author':access.user_id,'version':version,
                     'created_at':datetime.now(timezone.utc).isoformat(),'status':'draft','scope':list(access.allowed_territories)}
            db.execute('INSERT INTO custom_kpis VALUES(?,?,?,?,?)',(spec.id,version,access.user_id,'draft',json.dumps(payload,ensure_ascii=False)))
        return payload

    def confirm(self, proposal_id, access):
        with self.state.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT payload FROM custom_kpis WHERE author=? AND status='draft'",(access.user_id,)).fetchall()
            payload=next((json.loads(r[0]) for r in rows if json.loads(r[0])['proposal_id']==proposal_id),None)
            if not payload: raise forbidden()
            self.validate(KpiDefinition.model_validate(payload['definition']),access,write=True)
            if not payload.get('example_validated'):
                raise AppError('invalid_request','Calculer et vérifier un exemple avant confirmation.',422)
            payload['status']='active'
            db.execute("UPDATE custom_kpis SET status='active',payload=? WHERE id=? AND version=?",(json.dumps(payload,ensure_ascii=False),payload['definition']['id'],payload['version']))
        return payload

    def attach_example(self, proposal, example):
        proposal.update(example=example,example_validated=True)
        with self.state.connect() as db:
            db.execute('UPDATE custom_kpis SET payload=? WHERE id=? AND version=? AND status=\'draft\'',
                       (json.dumps(proposal,ensure_ascii=False),proposal['definition']['id'],proposal['version']))
        return proposal
