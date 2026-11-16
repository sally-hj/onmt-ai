"""Préparation explicite/idempotente d'une bibliothèque partagée, sans toucher aux imports privés."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from app.core.config import ROOT, Settings
from app.core.errors import AppError, forbidden
from app.core.security import ResourcePolicy
from .documents import DocumentMetadata, DocumentRecord


def prepare_library(app, access):
    if access.user_id!='direction' or 'document_editor' not in access.roles: raise forbidden()
    store=app.state.store
    entries=json.loads((ROOT/'examples/library/corpus.json').read_text(encoding='utf-8'))
    from app.analytics.metrics import METRICS
    entries.append({'id':'indicateurs','title':'Dictionnaire des indicateurs — corpus synthétique','kind':'dictionary',
        'language':'fr','issued_on':'2026-11-15','edition':'1','context':'Définitions, unités et formules des KPI disponibles.',
        'paragraphs':['DOCUMENT FICTIF — dictionnaire pédagogique, aucune homologation OMT/WTTC/WEF.']+
            [f'{m.label} ({m.id}) : {m.formula}. Unité : {m.unit}. {m.limit}' for m in METRICS.values()]})
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS library_registry(id TEXT PRIMARY KEY,fingerprint TEXT,document_id TEXT)')
    output=[]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            context=browser.new_context(java_script_enabled=False,service_workers='block')
            context.route('**/*',lambda route:route.abort()); page=context.new_page()
            for entry in entries:
                fingerprint=hashlib.sha256(json.dumps(entry,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                with store.connect() as db: row=db.execute('SELECT * FROM library_registry WHERE id=?',(entry['id'],)).fetchone()
                if row and row['fingerprint']==fingerprint:
                    doc=DocumentRecord.model_validate(store.document(row['document_id']))
                    if not doc.policy.shared_library or doc.policy.owner_id!=access.user_id: raise forbidden()
                    if doc.index_identity!=app.state.retriever.index.embedder.identity:
                        app.state.retriever.index.add(doc)
                        doc.index_identity=app.state.retriever.index.embedder.identity
                        with store.connect() as db: db.execute('UPDATE documents SET payload=? WHERE id=? AND version=?',(doc.model_dump_json(),doc.document_id,doc.version))
                    output.append({'id':entry['id'],'document_id':doc.document_id,'version':doc.version,'status':'unchanged'}); continue
                markup='<html dir="'+('rtl' if entry['language'] in ['ar','ary'] else 'ltr')+'"><meta charset="utf-8"><style>body{font:12pt Arial;line-height:1.6;color:#18352e}p{break-inside:avoid}</style><h1>'+html.escape(entry['title'])+'</h1>'
                markup+=''.join('<p>'+html.escape(t)+'</p>' for t in entry['paragraphs'])+'</html>'
                page.set_content(markup,wait_until='load')
                content=page.pdf(format='A4',margin={'top':'18mm','bottom':'18mm','left':'18mm','right':'18mm'})
                metadata=DocumentMetadata(**{k:v for k,v in entry.items() if k not in ['id','paragraphs']},synthetic=True,
                    publisher='Atelier synthétique ONMT AI',corpus_id='onmt-library-v1:'+entry['id'])
                doc,duplicate=app.state.documents.ingest_pdf(content,metadata,access,row['document_id'] if row else None)
                if duplicate and not doc.policy.shared_library:
                    raise AppError('invalid_request','Un import privé identique existe ; il reste privé et ne sera pas publié automatiquement.',409)
                # Seuls les documents créés explicitement par cette commande deviennent partagés.
                doc.policy=ResourcePolicy(owner_id=access.user_id,roles=['report_editor'],modules=['reports'],territories=['*'],private=False,shared_library=True)
                with store.connect() as db:
                    db.execute('UPDATE documents SET payload=? WHERE id=? AND version=?',(doc.model_dump_json(),doc.document_id,doc.version))
                    db.execute('INSERT OR REPLACE INTO library_registry VALUES(?,?,?)',(entry['id'],fingerprint,doc.document_id))
                store.audit(access.user_id,'library','library.publish',doc.document_id)
                output.append({'id':entry['id'],'document_id':doc.document_id,'version':doc.version,'status':'indexed'})
        finally: browser.close()
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--confirm-shared-library',action='store_true')
    parser.add_argument('--data-dir',type=Path,default=ROOT/'local_data/full-app')
    args=parser.parse_args()
    if not args.confirm_shared_library: parser.error('--confirm-shared-library requis : crée des documents partagés explicitement')
    from app.main import create_app
    from app.schemas.common import AccessContext
    app=create_app(Settings(full_app=True,data_dir=args.data_dir))
    with app.state.application_state.connect() as db: raw=db.execute("SELECT access FROM users WHERE username='direction'").fetchone()[0]
    try: print(json.dumps(prepare_library(app,AccessContext.model_validate_json(raw)),ensure_ascii=False,indent=2))
    finally: app.state.jobs.close()
