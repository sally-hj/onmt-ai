"""File locale bornée, idempotence par utilisateur, annulation coopérative entre étapes."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event, Lock
from uuid import uuid4

from app.core.errors import AppError, forbidden
from .timing import trace, stage_callback


def now(): return datetime.now(timezone.utc).isoformat()


class Jobs:
    def __init__(self,state):
        self.state=state; self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='onmt-job')
        self.lock=Lock(); self.stopping=Event()
        with state.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,owner TEXT,idem TEXT,fingerprint TEXT,payload TEXT,UNIQUE(owner,idem))')
            for row in db.execute('SELECT id,payload FROM jobs'):
                payload=json.loads(row['payload'])
                if payload['status'] in ['queued','running','cancel_requested']:
                    payload.update(status='failed',error={'code':'interrupted','message':'Service redémarré ; vérifier les ressources avant de relancer.'},finished_at=now())
                    db.execute('UPDATE jobs SET payload=? WHERE id=?',(json.dumps(payload),row['id']))

    def _save(self, payload):
        with self.state.connect() as db: db.execute('UPDATE jobs SET payload=? WHERE id=?',(json.dumps(payload,ensure_ascii=False),payload['id']))

    def get(self,jid,owner):
        with self.state.connect() as db: row=db.execute('SELECT payload FROM jobs WHERE id=? AND owner=?',(jid,owner)).fetchone()
        if not row: raise forbidden()
        return json.loads(row[0])

    def submit(self,owner,key,body,function):
        digest=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            with self.state.connect() as db:
                row=db.execute('SELECT fingerprint,payload FROM jobs WHERE owner=? AND idem=?',(owner,key)).fetchone()
                if row:
                    if row['fingerprint']!=digest: raise AppError('version_conflict','Clé de tâche déjà utilisée avec une autre demande.',409)
                    return json.loads(row['payload'])
                active=sum(json.loads(r[0])['status'] in ['queued','running','cancel_requested'] for r in db.execute('SELECT payload FROM jobs'))
                if active>=8: raise AppError('busy','File locale pleine ; réessayer après une tâche.',429)
                payload={'id':'job_'+uuid4().hex,'status':'queued','stage':'queued','steps':[],'timings':[],
                         'created_at':now(),'result':None,'error':None,'cancel_requested':False}
                db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)',(payload['id'],owner,key,digest,json.dumps(payload)))
            self.pool.submit(self._run,payload['id'],owner,function)
            return payload

    def cancel(self,jid,owner):
        with self.lock:
            payload=self.get(jid,owner)
            if payload['status'] in ['queued','running','cancel_requested']:
                payload.update(cancel_requested=True,status='cancel_requested'); self._save(payload)
            return payload

    def _run(self,jid,owner,function):
        timings=[]
        def step(name):
            with self.lock:
                payload=self.get(jid,owner)
                if payload['cancel_requested'] or self.stopping.is_set(): raise AppError('cancelled','Traitement arrêté entre deux étapes. Les ressources déjà créées restent dans la bibliothèque.',409)
                payload.update(status='running',stage=name)
                if not payload['steps'] or payload['steps'][-1]['stage']!=name:
                    payload['steps'].append({'stage':name,'started_at':now()})
                self._save(payload)
        token=trace.set(timings); stage_token=stage_callback.set(step)
        try:
            step('preparation'); result=function()
            with self.lock:
                payload=self.get(jid,owner)
                payload.update(status='completed',stage='completed',result=result,finished_at=now(),timings=timings)
                # Une annulation trop tardive ne prétend pas annuler un résultat déjà créé.
                if payload['cancel_requested']: payload['warning']='Résultat terminé avant la prochaine frontière d’annulation.'
                self._save(payload)
        except Exception as exc:
            with self.lock:
                payload=self.get(jid,owner); code=getattr(exc,'code','tool_failed')
                payload.update(status='cancelled' if code=='cancelled' else 'failed',error={'code':code,'message':getattr(exc,'message','Le traitement a échoué ; consulter le journal local.')},finished_at=now(),timings=timings)
                self._save(payload)
        finally:
            trace.reset(token); stage_callback.reset(stage_token)

    def close(self):
        self.stopping.set(); self.pool.shutdown(wait=False,cancel_futures=True)
