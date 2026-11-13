"""Contrôle à la demande : baisse annuelle des nuitées, sans promesse de monitoring 24/7."""
import hashlib
import json
from collections import defaultdict

from app.core.errors import AppError, forbidden


class AlertService:
    def __init__(self,catalog,state):
        self.catalog,self.state = catalog,state

    def refresh(self,access):
        # Une actualisation ne voit et ne remplace que les alertes du périmètre autorisé.
        rows,version = self.catalog.read_authorized_data('commercial',['month','destination','overnight_stays'],{},access)
        totals = defaultdict(float)
        for row in rows:
            totals[(row['destination'],row['month'])] += row['overnight_stays']
        found = []
        for (destination,month),current in totals.items():
            year = int(month[:4]); previous = totals.get((destination,str(year-1)+month[4:]))
            if previous and (current-previous)/previous <= -.15:
                change = round((current-previous)/previous*100,4)
                alert_id = hashlib.sha256(f'overnight_stays:{destination}:{month}:yoy15'.encode()).hexdigest()[:24]
                found.append({'id':alert_id,'destination':destination,'month':month,'metric_id':'overnight_stays',
                    'current':current,'previous':previous,'change_pct':change,'threshold_pct':-15,'version':version,
                    'formula':'100 * (current - same_month_previous_year) / same_month_previous_year',
                    'source':'commercial.qvd','synthetic':self.catalog.config['synthetic'],
                    'warning':'Baisse annuelle descriptive ; aucune cause déduite.'})
        with self.state.connect() as db:
            existing = list(db.execute('SELECT id,payload FROM alerts'))
            for row in existing:
                if json.loads(row['payload'])['destination'] in access.allowed_territories:
                    db.execute('DELETE FROM alerts WHERE id=?',(row['id'],))
            for alert in found:
                db.execute('INSERT OR REPLACE INTO alerts VALUES(?,?)',(alert['id'],json.dumps(alert,ensure_ascii=False)))
        return self.list(access)

    def list(self,access):
        if 'commercial' not in access.allowed_modules:
            raise forbidden()
        with self.state.connect() as db:
            values = [json.loads(row[0]) for row in db.execute('SELECT payload FROM alerts')]
        version = self.catalog.versions(['commercial'])['commercial']
        return [{**v,'stale':v['version']!=version} for v in values if v['destination'] in access.allowed_territories]
