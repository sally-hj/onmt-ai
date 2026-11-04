"""SQLite local : instantanés immuables et remplacement atomique de la version courante."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.errors import AppError


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'reporting.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(id, version));
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
                    pdf BLOB, PRIMARY KEY(id, version));
                CREATE TABLE IF NOT EXISTS audit (
                    at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    user_id TEXT, request_id TEXT, action TEXT, resource_id TEXT);
            ''')
            if 'original_pdf' not in {r[1] for r in db.execute('PRAGMA table_info(documents)')}:
                db.execute('ALTER TABLE documents ADD COLUMN original_pdf BLOB')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def documents(self, current=True):
        with self.connect() as db:
            sql = ('SELECT payload FROM documents d WHERE version = '
                   '(SELECT MAX(version) FROM documents WHERE id=d.id)') if current else 'SELECT payload FROM documents'
            return [json.loads(r[0]) for r in db.execute(sql)]

    def document(self, doc_id, version=None):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM documents WHERE id=? AND (? IS NULL OR version=?) ORDER BY version DESC LIMIT 1',
                             (doc_id, version, version)).fetchone()
            return json.loads(row[0]) if row else None

    def save_document(self, payload, original_pdf):
        with self.connect() as db:
            db.execute('INSERT INTO documents(id,version,payload,original_pdf) VALUES (?,?,?,?)',
                       (payload['document_id'], payload['version'], json.dumps(payload, ensure_ascii=False), original_pdf))

    def document_pdf(self, doc_id, version):
        with self.connect() as db:
            row = db.execute('SELECT original_pdf FROM documents WHERE id=? AND version=?', (doc_id, version)).fetchone()
            return bytes(row[0]) if row and row[0] else None

    def report(self, report_id, version=None):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM reports WHERE id=? AND (? IS NULL OR version=?) ORDER BY version DESC LIMIT 1',
                             (report_id, version, version)).fetchone()
            return json.loads(row[0]) if row else None

    def report_ids(self):
        with self.connect() as db:
            return [r[0] for r in db.execute('SELECT DISTINCT id FROM reports')]

    def save_report(self, payload, base_version=None):
        result = payload['result']
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            latest = db.execute('SELECT MAX(version) FROM reports WHERE id=?', (result['report_id'],)).fetchone()[0]
            if latest != base_version:
                raise AppError('version_conflict', 'Le rapport a été modifié. Rechargez la dernière version.', 409)
            db.execute('INSERT INTO reports(id,version,payload) VALUES (?,?,?)',
                       (result['report_id'], result['version'], json.dumps(payload, ensure_ascii=False)))

    def save_pdf(self, report_id, version, content):
        with self.connect() as db:
            db.execute('UPDATE reports SET pdf=? WHERE id=? AND version=?', (content, report_id, version))

    def pdf(self, report_id, version):
        with self.connect() as db:
            row = db.execute('SELECT pdf FROM reports WHERE id=? AND version=?', (report_id, version)).fetchone()
            return bytes(row[0]) if row and row[0] else None

    def audit(self, user_id, request_id, action, resource_id):
        with self.connect() as db:
            db.execute('INSERT INTO audit(user_id,request_id,action,resource_id) VALUES (?,?,?,?)',
                       (user_id, request_id, action, resource_id))
