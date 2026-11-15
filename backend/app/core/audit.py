"""Journal local vérifiable ; une chaîne ne remplace pas un stockage WORM externe."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone


class AuditLog:
    def __init__(self, directory):
        self.path=directory/'audit.sqlite3'
        with sqlite3.connect(self.path) as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, event TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;''')

    @staticmethod
    def digest(seq,event,previous):
        return hashlib.sha256(f'{seq}\n{previous}\n{event}'.encode()).hexdigest()

    def append(self, actor, request_id, action, resource, outcome='success', versions=None,details=None):
        event=json.dumps({'at':datetime.now(timezone.utc).isoformat(),'actor':actor,'request_id':request_id,
            'action':action,'resource':resource,'outcome':outcome,'versions':versions or {},'details':details or {}},ensure_ascii=False,sort_keys=True,separators=(',',':'))
        with sqlite3.connect(self.path,timeout=30) as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT seq,digest FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            seq,previous=(row[0]+1,row[1]) if row else (1,'0'*64)
            digest=self.digest(seq,event,previous)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',(seq,event,previous,digest))
        return {'seq':seq,'digest':digest}

    def verify(self, trusted_head=None):
        previous='0'*64; count=0
        anchor_matches=trusted_head is None or trusted_head=={'seq':0,'digest':'0'*64}
        with sqlite3.connect(self.path) as db:
            for seq,event,link,digest in db.execute('SELECT * FROM events ORDER BY seq'):
                if seq!=count+1 or link!=previous or digest!=self.digest(seq,event,link):
                    return {'valid':False,'at_sequence':seq,'count':count,'reason':'chain_mismatch'}
                previous=digest; count+=1
                if trusted_head and trusted_head.get('seq')==seq:
                    anchor_matches=trusted_head.get('digest')==digest
        head={'seq':count,'digest':previous}
        return {'valid':anchor_matches,'count':count,'head':head,
                'external_anchor_checked':trusted_head is not None,'limit':'Un administrateur contrôlant tout le stockage peut réécrire la chaîne ; conserver les empreintes hors du poste pour détecter une troncature ou reconstruction.'}


if __name__=='__main__':
    import argparse
    from pathlib import Path
    from .config import ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=ROOT/'local_data/full-app')
    parser.add_argument('--anchor',type=Path,help='Empreinte de tête précédemment conservée sur un support de confiance.')
    args=parser.parse_args()
    if not (args.directory/'audit.sqlite3').is_file(): parser.error('Journal absent ; aucune vérification possible.')
    result=AuditLog(args.directory).verify(json.loads(args.anchor.read_text(encoding='utf-8')) if args.anchor else None)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['valid'] else 1)
