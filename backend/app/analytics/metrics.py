"""Définitions explicites ; aucune formule envoyée par le LLM n'est exécutée."""
from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class Metric:
    id: str
    label: str
    unit: str
    fields: dict[str, list[str]]
    formula: str
    kind: str = 'sum'
    limit: str = 'Définition pédagogique du corpus synthétique de référence ; aucune représentativité statistique ONMT revendiquée.'

    def source_formula(self, sources):
        """Décrit les colonnes réellement lues, même après un changement de mapping."""
        mapping={field:(sid+'.' if len(self.fields)>1 else '')+sources[sid]['fields'][field]
                 for sid,fields in self.fields.items() for field in fields}
        pattern=r'\b('+'|'.join(re.escape(field) for field in sorted(mapping,key=len,reverse=True))+r')\b'
        return re.sub(pattern,lambda match:mapping[match.group(0)],self.formula)


METRICS = {m.id:m for m in [
    Metric('overnight_stays','Nuitées','nuitees',{'commercial':['overnight_stays']},'SUM(overnight_stays)'),
    Metric('arrivals','Arrivées touristiques','arrivees',{'commercial':['arrivals']},'SUM(arrivals)'),
    Metric('seats','Sièges aériens disponibles','sieges',{'commercial':['seats']},'SUM(seats)'),
    Metric('bookings','Réservations','reservations',{'commercial':['bookings']},'SUM(bookings)'),
    Metric('budget','Budget prévu','MAD',{'finance':['budget']},'SUM(budget)'),
    Metric('spent','Dépenses exécutées','MAD',{'finance':['spent']},'SUM(spent)'),
    Metric('committed','Engagements','MAD',{'finance':['committed']},'SUM(committed)'),
    Metric('travel_receipts','Recettes voyages','MAD',{'performance':['travel_receipts']},'SUM(travel_receipts)'),
    Metric('room_revenue','Recettes des chambres','MAD',{'performance':['room_revenue']},'SUM(room_revenue)'),
    Metric('average_stay','Durée moyenne de séjour','nuits/arrivee',{'commercial':['overnight_stays','arrivals']},'SUM(overnight_stays) / SUM(arrivals)','ratio'),
    Metric('occupancy','Taux d’occupation des chambres','%',{'performance':['rooms_sold','rooms_available']},'100 * SUM(rooms_sold) / SUM(rooms_available)','percent'),
    Metric('revpar','Revenu par chambre disponible','MAD/chambre-nuit',{'performance':['room_revenue','rooms_available']},'SUM(room_revenue) / SUM(rooms_available)','ratio'),
    Metric('average_room_price','Prix moyen par chambre vendue','MAD/chambre-nuit',{'performance':['room_revenue','rooms_sold']},'SUM(room_revenue) / SUM(rooms_sold)','ratio'),
    Metric('budget_execution','Taux d’exécution budgétaire','%',{'finance':['spent','budget']},'100 * SUM(spent) / SUM(budget)','percent'),
    Metric('click_rate','Taux de clic','%',{'performance':['clicks','impressions']},'100 * SUM(clicks) / SUM(impressions)','percent'),
    Metric('spend_per_night','Dépenses promotionnelles par nuitée','MAD/nuitee',{'finance':['spent'],'commercial':['overnight_stays']},'SUM(spent) / SUM(overnight_stays)','ratio',
           'Rapprochement descriptif de périmètres identiques, pas un ROI causal ni une attribution des nuitées aux dépenses.')
]}


def metric_catalog(access, sources):
    return [asdict(m) for m in METRICS.values() if all(sources[s]['module'] in access.allowed_modules for s in m.fields)]


def calculate(metric, totals):
    values = [totals[(source,field)] for source,fields in metric.fields.items() for field in fields]
    if metric.kind == 'sum':
        return round(values[0],4)
    return round(values[0]/values[1]*(100 if metric.kind == 'percent' else 1),4) if values[1] else None
