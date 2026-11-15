"""Vérifications périodiques locales, un thread lié au cycle de vie de l'API."""
import json
from datetime import datetime, timezone
from threading import Event, Thread

from app.schemas.common import AccessContext


class Monitor:
    def __init__(self, state, alerts, interval=0):
        self.state,self.alerts,self.interval=state,alerts,interval
        self.stop_event=Event(); self.thread=None
        with state.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS monitor_state(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')

    def status(self):
        with self.state.connect() as db:
            row=db.execute("SELECT payload FROM monitor_state WHERE id='local'").fetchone()
        return {**(json.loads(row[0]) if row else {}),'enabled':self.interval>0,'interval_seconds':self.interval,'running':bool(self.thread and self.thread.is_alive())}

    def check(self):
        previous=self.status()
        data={k:v for k,v in previous.items() if k not in ['enabled','running','interval_seconds']}
        data['last_attempt_at']=datetime.now(timezone.utc).isoformat()
        try:
            with self.state.connect() as db: users=[AccessContext.model_validate_json(r[0]) for r in db.execute('SELECT access FROM users')]
            # Couverture des comptes actuels ; chaque outil conserve les ACL. Aucun envoi externe.
            for access in users:
                if 'commercial' in access.allowed_modules and access.allowed_territories: self.alerts.refresh(access)
            data.update(last_success_at=datetime.now(timezone.utc).isoformat(),error=None)
        except Exception as exc:
            data['error']=getattr(exc,'code','tool_failed')
        with self.state.connect() as db:
            db.execute('INSERT OR REPLACE INTO monitor_state VALUES(?,?)',('local',json.dumps(data)))
        return self.status()

    def _run(self):
        while not self.stop_event.is_set():
            self.check()
            self.stop_event.wait(self.interval)

    def start(self):
        if self.interval>0 and not self.thread:
            self.thread=Thread(target=self._run,name='onmt-monitor',daemon=True); self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread: self.thread.join(timeout=5)
