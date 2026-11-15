"""Orchestration avec interpréteur simulé ; calculs QVD, SQLite et threads réels."""
import json
import sqlite3
import time
from threading import Event

import pytest
from fastapi.testclient import TestClient

from app.core.audit import AuditLog
from app.core.config import ROOT, Settings
from app.core.errors import AppError
from app.core.jobs import Jobs
from app.core.state import AppState
from app.core.monitor import Monitor
from app.data_access.synthetic import generate, DESTINATIONS
from app.main import create_app
from app.conversation.intent import Intent
from app.conversation.service import ConversationService
from app.schemas.common import AccessContext
from app.reports.narrative import validate_arabic_script


def access(): return AccessContext(user_id='direction',roles=['report_editor','document_editor'],allowed_modules=['reports','commercial','finance','performance'],allowed_territories=DESTINATIONS)


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    path=tmp_path_factory.mktemp('ops-native'); generate(path); return path


@pytest.fixture()
def app(native,tmp_path):
    app=create_app(Settings(full_app=True,data_dir=tmp_path,qvd_root=native,demo=True,demo_embeddings=True,generation_mode='template',ollama_model=''))
    yield app
    app.state.jobs.close()


def test_audit_chain_tampering_anchor_and_no_secrets(tmp_path):
    log=AuditLog(tmp_path)
    first=log.append('analyst','req1','analysis','ana1',versions={'commercial':'v1'})
    assert log.verify()['valid']
    log.append('analyst','req2','download','rpt1',outcome='403')
    assert log.verify(first)['valid']  # Ajouter des événements respecte une ancienne ancre.
    with sqlite3.connect(log.path) as db:
        with pytest.raises(sqlite3.IntegrityError): db.execute("UPDATE events SET event='changed' WHERE seq=1")
        db.execute('DROP TRIGGER audit_no_update'); db.execute("UPDATE events SET event='changed' WHERE seq=1")
    assert log.verify()['valid'] is False


def wait_terminal(jobs,jid,owner='direction'):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        value=jobs.get(jid,owner)
        if value['status'] in ['completed','cancelled','failed']: return value
        time.sleep(.02)
    pytest.fail('La tâche ne se termine pas')


def test_jobs_idempotency_cancellation_errors_and_ownership(tmp_path):
    jobs=Jobs(AppState(tmp_path)); gate=Event(); started=Event(); calls=[]
    def blocking(): started.set(); gate.wait(3); calls.append(1); return {'message':'done'}
    a=jobs.submit('direction','same-key',{'x':1},blocking); started.wait(2)
    same=jobs.submit('direction','same-key',{'x':1},blocking)
    assert same['id']==a['id']
    with pytest.raises(AppError): jobs.submit('direction','same-key',{'x':2},blocking)
    b=jobs.submit('direction','cancel-key',{'x':3},lambda: calls.append(2))
    jobs.cancel(b['id'],'direction')
    with pytest.raises(AppError): jobs.get(a['id'],'regional')
    gate.set()
    assert wait_terminal(jobs,a['id'])['status']=='completed'
    assert wait_terminal(jobs,b['id'])['status']=='cancelled' and calls==[1]
    failure=jobs.submit('direction','error-key',{},lambda:(_ for _ in ()).throw(AppError('missing_data','Source absente.',422)))
    assert wait_terminal(jobs,failure['id'])['error']=={'code':'missing_data','message':'Source absente.'}
    jobs.close()


def test_monitor_runs_without_request_persists_and_handles_errors(app):
    monitor=Monitor(app.state.application_state,app.state.alerts,.05)
    monitor.start()
    deadline=time.monotonic()+4
    while time.monotonic()<deadline and not monitor.status().get('last_success_at'): time.sleep(.02)
    monitor.stop()
    assert monitor.status()['last_success_at']
    items=app.state.alerts.list(access())
    assert any(a['metric_id']=='overnight_stays' and a['change_pct']==-20 for a in items)
    assert any(a['metric_id']=='arrivals' and a['market']=='Allemagne' for a in items)
    assert len(items)==len({a['id'] for a in items})
    again=Monitor(app.state.application_state,app.state.alerts,0)
    assert again.status()['last_success_at']==monitor.status()['last_success_at']
    app.state.alerts.refresh=lambda access:(_ for _ in ()).throw(AppError('source_changed','Changed',409))
    previous=again.status()['last_success_at']; again.check()
    assert again.status()['error']=='source_changed' and again.status()['last_success_at']==previous


class ContextParser:
    """Entrées structurées prescrites par le test, aucun appel à Qwen."""
    def parse(self,message,context,catalog,language): return Intent.model_validate({**json.loads(message),'language':language})


def test_60_contextual_turns_corrections_languages_restart_and_five_revisions(app):
    service=app.state.conversations; service.parser=ContextParser(); previous=None
    period={'start':'2025-02-01','end':'2025-02-28'}; comparison={'start':'2024-02-01','end':'2024-02-29'}
    sequence=[
        ({'action':'analyse','metric_id':'overnight_stays','operation':'compare','destination':'Agadir','period':period,'comparison_period':comparison},80000,-20),
        ({'action':'analyse','market':'France'},25600,-20),
        ({'action':'analyse','destination':'Marrakech'},52800,10),
        ({'action':'analyse','clear_filters':['market']},165000,10),
        ({'action':'clarify','clarification':'Quelle définition ?'},None,None),
        ({'action':'analyse','destination':'Agadir'},80000,-20)]
    for i in range(60):
        intent,expected,change=sequence[i%6]
        previous=service.send(json.dumps(intent),access(),previous['conversation_id'] if previous else None,previous['version'] if previous else 0,['fr','en','es','ar','ary'][i%5])
        if expected is not None:
            assert previous['analysis']['values']['current']==expected
            assert previous['analysis']['values']['change_pct']==change
        else: assert previous['needs_clarification']
        if i==29: service=ConversationService(AppState(app.state.application_state.path.parent),app.state.analytics,app.state.reports,app.state.exporter,ContextParser())
    previous=service.send('{"action":"report"}',access(),previous['conversation_id'],previous['version'])
    rid=previous['report']['report_id']
    for version,instruction in enumerate(['résumer','détailler','langue:ar','adapter:ministere','langue:fr'],2):
        previous=service.send(json.dumps({'action':'revise','instruction':instruction}),access(),previous['conversation_id'],previous['version'])
        assert previous['report']['report_id']==rid and previous['report']['version']==version
        assert '80000' in previous['report']['sections'][0]['content']
    assert len(service.state.conversation(previous['conversation_id'],access().user_id)['messages'])==132


def test_agents_peak_budget_handoff_and_denied_finance(app):
    app.state.conversations.parser=ContextParser()
    message=json.dumps({'action':'briefing','metric_id':'overnight_stays','operation':'value','destination':'Agadir',
        'period':{'start':'2021-01-01','end':'2025-12-31'}})
    response=app.state.conversations.send(message,access())
    names=[t['agent'] for t in response['agent_trace']]
    assert names==['territorial','marches','saisonnalite','budget_performance','recherche','comex','verification']
    ids=app.state.reports.store.report(response['report']['report_id'])['request']['analysis_ids']
    assert {app.state.analytics.get_analysis(i,access()).metric_id for i in ids}=={'overnight_stays','budget','spent','spend_per_night','click_rate'}
    assert {s['source_id'] for s in response['report']['sources']}=={'commercial','finance','performance'}
    restricted=access().model_copy(update={'allowed_modules':['reports','commercial','performance']})
    with pytest.raises(AppError): app.state.conversations.send(message,restricted)


def test_arabic_names_allowed_but_wrong_alphabets_refused():
    validate_arabic_script('تستدعي نتائج Agadir وRevPAR المراجعة.')
    for bad in ['This is an English paragraph.','نتائج مراكشЖ تحتاج للمراجعة.','Agadir RevPAR']:
        with pytest.raises(ValueError): validate_arabic_script(bad)


@pytest.mark.parametrize('action',['clarify','benchmark','update_report'])
def test_short_market_followup_reuses_analysis_instead_of_changing_report(action):
    from app.conversation.slots import ground_intent
    context={'analysis_request':{'metric_id':'overnight_stays','operation':'compare','period':{'start':'2025-02-01','end':'2025-02-28'},'comparison_period':{'start':'2024-02-01','end':'2024-02-29'}}}
    for message in ['Et pour le marché espagnol ?','And for the Spanish source market?','¿Y para el mercado español?','وماذا عن السوق الإسبانية؟','ودابا السوق ديال إسبانيا؟']:
        intent=ground_intent(Intent(action=action,dimensions=['Espagne'] if action=='benchmark' else None),message,{'markets':['Espagne'],'destinations':['Agadir']},context)
        assert intent.action=='analyse' and intent.market=='Espagne'
    explicit=ground_intent(Intent(action='update_report'),'Et pour le rapport, ajoute le marché Espagne.',{'markets':['Espagne'],'destinations':['Agadir']},context)
    assert explicit.action=='update_report'
