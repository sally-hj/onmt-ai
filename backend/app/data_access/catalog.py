"""Catalogue configuré, découverte réelle, contrôle de grain et version des sources."""
import json
import hashlib
from pathlib import Path

from app.analytics.quality import inspect_rows
from app.core.errors import AppError, forbidden
from .qvd_reader import QvdReader, source_version


class Catalog:
    def __init__(self, config: Path, root: Path):
        self.config_path = config
        self.config = json.loads(config.read_text(encoding='utf-8-sig'))
        self.sources = {s['id']:s for s in self.config['sources']}
        if len(self.sources) != len(self.config['sources']):
            raise ValueError('Identifiants de source dupliqués')
        for source in self.sources.values():
            if source['grain'] != ['month','destination','market'] or not {'key','month','destination','market'}.issubset(source['fields']):
                raise ValueError('Grain mensuel destination/marché et dimensions obligatoires requis ; adapter explicitement un autre grain.')
            if len(set(source['fields'].values())) != len(source['fields']):
                raise ValueError('Deux champs logiques ne peuvent pas désigner la même colonne physique.')
        self.reader = QvdReader(root)

    def version(self, sid, digest):
        metadata = json.dumps({'source':self.sources[sid],'synthetic':self.config['synthetic']},sort_keys=True,ensure_ascii=False)
        return hashlib.sha256((digest+metadata).encode()).hexdigest()

    def read_authorized_data(self, dataset_id, fields, filters, access_context):
        source = self.sources.get(dataset_id)
        if source is None or source['module'] not in access_context.allowed_modules:
            raise forbidden()
        if set(fields)-set(source['fields']):
            raise AppError('invalid_request','Champ non déclaré dans le catalogue.',422)
        rows, version, _ = self.reader.read(source,access_context,filters)
        errors = inspect_rows(rows,source)
        if errors:
            raise AppError('data_quality','Calcul bloqué : ' + ', '.join(errors),422)
        return [{k:r[k] for k in fields} for r in rows], self.version(dataset_id,version)

    def versions(self, source_ids):
        return {sid:self.version(sid,source_version(self.reader.path(self.sources[sid]))) for sid in source_ids}

    def describe(self, access):
        result = []
        for source in self.sources.values():
            if source['module'] not in access.allowed_modules:
                continue
            try:
                rows, version, types = self.reader.read(source,access)
                result.append({'id':source['id'],'name':Path(source['file']).name,'module':source['module'],
                    'version':self.version(source['id'],version),'fields':source['fields'],'types':types,'units':source['units'],'grain':source['grain'],
                    'rows':len(rows),'period':{'start':min((r['month'] for r in rows if not r.get('_invalid_date')),default=None),
                                          'end':max((r['month'] for r in rows if not r.get('_invalid_date')),default=None)},
                    'destinations':sorted({r['destination'] for r in rows}), 'markets':sorted({r['market'] for r in rows}),
                    'quality_errors':inspect_rows(rows,source),'synthetic':self.config['synthetic']})
            except AppError as exc:
                result.append({'id':source['id'],'module':source['module'],'error':exc.message,'quality_errors':[exc.code]})
        relations = []
        for relation in self.config.get('relations',[]):
            if all(self.sources[s]['module'] in access.allowed_modules for s in [relation['left'],relation['right']]):
                try:
                    sets = []
                    for sid in [relation['left'],relation['right']]:
                        rows,_ = self.read_authorized_data(sid,relation['keys'],{},access)
                        sets.append({tuple(r[k] for k in relation['keys']) for r in rows})
                    relations.append({**relation,'valid':sets[0]==sets[1],'unmatched_keys':len(sets[0]^sets[1])})
                except AppError:
                    relations.append({**relation,'valid':False,'warning':'quality_or_source_error'})
        return {'label':self.config['label'],'synthetic':self.config['synthetic'],'sources':result,'relations':relations}
