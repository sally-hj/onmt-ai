"""État applicatif local : résultats, conversations et alertes ; jamais une copie des QVD."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .errors import AppError


class AppState:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True,exist_ok=True)
        from .audit import AuditLog
        self.audit_log=AuditLog(directory)
        self.path = directory/'application.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS analyses(id TEXT PRIMARY KEY, owner TEXT, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, owner TEXT, version INTEGER, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, salt TEXT, password_hash TEXT, access TEXT);
                CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, username TEXT, expires REAL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path,timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def save_analysis(self, analysis, owner, request, scope):
        payload = {'result':analysis.model_dump(mode='json'),'request':request.model_dump(mode='json'),'request_scope':scope}
        with self.connect() as db:
            db.execute('INSERT INTO analyses VALUES(?,?,?)',(analysis.analysis_id,owner,json.dumps(payload,ensure_ascii=False)))

    def analysis(self, analysis_id, owner):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM analyses WHERE id=? AND owner=?',(analysis_id,owner)).fetchone()
        return json.loads(row[0]) if row else None

    def list_analyses(self, owner):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM analyses WHERE owner=? ORDER BY rowid DESC LIMIT 100',(owner,))]

    def conversation(self, cid, owner):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM conversations WHERE id=? AND owner=?',(cid,owner)).fetchone()
        return json.loads(row[0]) if row else None

    def save_conversation(self, cid, owner, payload, base):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT version FROM conversations WHERE id=? AND owner=?',(cid,owner)).fetchone()
            current = row[0] if row else 0
            if current != base:
                raise AppError('version_conflict','La conversation a changé ; rechargez-la.',409)
            if current:
                db.execute('UPDATE conversations SET version=?,payload=? WHERE id=? AND owner=?',
                           (base+1,json.dumps(payload,ensure_ascii=False),cid,owner))
            else:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(cid,owner,1,json.dumps(payload,ensure_ascii=False)))
