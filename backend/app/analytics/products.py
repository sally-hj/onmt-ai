"""Diagnostics privés persistants, réutilisables dans les rapports, liés aux sources."""
import json
from uuid import uuid4
from app.core.config import ROOT
from app.core.errors import AppError,forbidden
from app.data_access.catalog import Catalog


class Products:
    def __init__(self,analytics):
        self.analytics=analytics
        with analytics.state.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS diagnostics(id TEXT PRIMARY KEY,owner TEXT,payload TEXT)')

    def save(self,result,access):
        result={**result,'diagnostic_id':'diag_'+uuid4().hex}
        record={'result':result,'scope':list(access.allowed_territories)}
        with self.analytics.state.connect() as db:
            db.execute('INSERT INTO diagnostics VALUES(?,?,?)',(result['diagnostic_id'],access.user_id,json.dumps(record,ensure_ascii=False)))
        return result

    def get(self,identifier,access):
        with self.analytics.state.connect() as db:
            row=db.execute('SELECT payload FROM diagnostics WHERE id=? AND owner=?',(identifier,access.user_id)).fetchone()
        if not row: raise forbidden()
        payload=json.loads(row[0]); result=payload['result']
        if not set(payload['scope']).issubset(access.allowed_territories): raise forbidden()
        if result.get('source'):
            source_id=result['source'].get('id','international')
            if source_id not in ['international','regional']: raise forbidden()
            catalog=Catalog(ROOT/f'config/sources.{source_id}.json',self.analytics.catalog.reader.root)
            if 'commercial' not in access.allowed_modules: raise forbidden()
            if catalog.versions([source_id])[source_id]!=result['source']['version']:
                raise AppError('stale_analysis','Comparateurs modifiés : recalculer le diagnostic.',409)
        identifiers=[]
        if result.get('analysis_id'): identifiers.append(result['analysis_id'])
        for point in result.get('points',[]):
            identifiers+=point.get('analysis_ids',[])
            if point.get('analysis_id'): identifiers.append(point['analysis_id'])
        for analysis in identifiers: self.analytics.get_analysis(analysis,access)
        return result
