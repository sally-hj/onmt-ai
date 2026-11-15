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
    expression: dict | None = None
    version: int = 1

    def describe(self, sources):
        return {**asdict(self), 'formula': self.source_formula(sources),
                'dimensions': ['destination', 'market'], 'grain': 'month',
                'aggregation': 'somme des lignes' if self.kind == 'sum' else 'calcul sur sommes ou distribution du périmètre, jamais moyenne des ratios',
                'missing_values': 'source invalide : refus ; période absente ou dénominateur nul : null',
                'interpretation': self.limit}

    def source_formula(self, sources):
        """Décrit les colonnes réellement lues, même après un changement de mapping."""
        if self.expression:
            result=self.formula
            for sid, fields in self.fields.items():
                for field in fields:
                    result=result.replace(sid+'.'+field,sid+'.'+sources[sid]['fields'][field])
            return result
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

# Chaque entrée représente un calcul distinct. Les indices sont des conventions
# pédagogiques explicitement nommées, pas des indices officiels OMT/WEF.
for metric in [
    Metric('receipts_per_arrival','DMT — Recettes par arrivée','MAD/arrivee',{'performance':['travel_receipts'],'commercial':['arrivals']},'SUM(travel_receipts) / SUM(arrivals)','ratio'),
    Metric('receipts_per_night','DMN — Recettes par nuitée','MAD/nuitee',{'performance':['travel_receipts'],'commercial':['overnight_stays']},'SUM(travel_receipts) / SUM(overnight_stays)','ratio'),
    Metric('spend_per_arrival','Dépenses promotionnelles par arrivée','MAD/arrivee',{'finance':['spent'],'commercial':['arrivals']},'SUM(spent) / SUM(arrivals)','ratio'),
    Metric('commitment_rate','Taux d’engagement','%',{'finance':['committed','budget']},'100 * SUM(committed) / SUM(budget)','percent'),
    Metric('budget_remaining','Crédits non exécutés','MAD',{'finance':['budget','spent']},'SUM(budget) - SUM(spent)','difference'),
    Metric('commitments_unpaid','Engagements non exécutés','MAD',{'finance':['committed','spent']},'SUM(committed) - SUM(spent)','difference'),
    Metric('impressions','Impressions publicitaires','impressions',{'performance':['impressions']},'SUM(impressions)'),
    Metric('clicks','Clics publicitaires','clics',{'performance':['clicks']},'SUM(clicks)'),
    Metric('cost_per_click','Coût par clic','MAD/clic',{'finance':['spent'],'performance':['clicks']},'SUM(spent) / SUM(clicks)','ratio'),
    Metric('cost_per_thousand','Coût de mille impressions','MAD/1000 impressions',{'finance':['spent'],'performance':['impressions']},'1000 * SUM(spent) / SUM(impressions)','per_thousand'),
    Metric('rooms_available','Capacité disponible','chambres-nuits',{'performance':['rooms_available']},'SUM(rooms_available)'),
    Metric('rooms_sold','Chambres-nuits vendues','chambres-nuits',{'performance':['rooms_sold']},'SUM(rooms_sold)'),
    Metric('international_arrivals','ATI — Arrivées internationales','arrivees',{'commercial':['arrivals']},'SUM(arrivals WHERE market != Maroc)','international'),
    Metric('market_concentration','ICME — Concentration des marchés émetteurs','indice 0-10000',{'commercial':['arrivals']},'10000 * SUM((arrivals_market / arrivals_total)^2)','hhi'),
    Metric('market_diversification','IDT — Diversification des marchés','indice 0-1',{'commercial':['arrivals']},'1 - SUM((arrivals_market / arrivals_total)^2)','diversification'),
    Metric('tourism_gini','CGT — Inégalité territoriale des nuitées','indice 0-1',{'commercial':['overnight_stays']},'SUM_i SUM_j ABS(nights_i - nights_j) / (2 * n * SUM(nights))','gini'),
    Metric('seasonality','ISM — Coefficient de variation mensuel','%',{'commercial':['overnight_stays']},'100 * STDDEV_POP(monthly_nights) / MEAN(monthly_nights)','seasonality', 'Au moins douze mois consécutifs ; mélange de tendance et saisonnalité, pas une correction saisonnière.'),
    Metric('annual_growth','TCA — Croissance des arrivées entre années complètes','%',{'commercial':['arrivals']},'100 * (arrivals_last_year / arrivals_previous_year - 1)','annual_growth'),
    Metric('annual_cagr','TCAM — Croissance annuelle moyenne des arrivées','%',{'commercial':['arrivals']},'100 * ((arrivals_last_year / arrivals_first_year)^(1/years_elapsed) - 1)','cagr'),
    Metric('conversions','Conversions attribuées fictives','conversions',{'extension':['conversions']},'SUM(conversions)'),
    Metric('campaign_conversion','ECT — Conversion des clics','%',{'extension':['conversions'],'performance':['clicks']},'100 * SUM(conversions) / SUM(clicks)','percent'),
    Metric('event_attendance','Fréquentation événementielle','entrees',{'extension':['event_attendance']},'SUM(event_attendance)'),
    Metric('event_fill','SFE — Remplissage événementiel','%',{'extension':['event_attendance','event_capacity']},'100 * SUM(event_attendance) / SUM(event_capacity)','percent'),
    Metric('tourism_gdp_share','CT-PIB — Part de valeur ajoutée touristique','%',{'extension':['tourism_gva','gdp']},'100 * SUM(tourism_gva) / SUM(gdp)','percent','Valeur ajoutée directe fictive ; ni compte satellite officiel ni effets indirects.'),
    Metric('employment_share','Part d’emploi touristique','%',{'extension':['tourism_jobs','total_jobs']},'100 * SUM(tourism_jobs) / SUM(total_jobs)','percent'),
    Metric('web_conversion','Conversion des visites web','%',{'extension':['conversions','web_visits']},'100 * SUM(conversions) / SUM(web_visits)','percent'),
    Metric('marketing_visibility','SVM — Engagements pour mille impressions','engagements/1000 impressions',{'extension':['engagements'],'performance':['impressions']},'1000 * SUM(engagements) / SUM(impressions)','per_thousand'),
    Metric('campaign_roi','IRT — Marge attribuée moins coût, sur coût','%',{'extension':['attributed_margin'],'finance':['spent']},'100 * (SUM(attributed_margin) - SUM(spent)) / SUM(spent)','roi','Attribution imposée par le générateur fictif ; ce scénario ne démontre aucune causalité publicitaire.'),
]:
    METRICS[metric.id] = metric

FIELD_UNITS = {'overnight_stays':'nuitees','arrivals':'arrivees','seats':'sieges','bookings':'reservations',
               'rooms_sold':'chambres-nuits','rooms_available':'chambres-nuits','impressions':'impressions','clicks':'clics',
               'conversions':'conversions','event_attendance':'entrees','event_capacity':'places','tourism_jobs':'emplois',
               'total_jobs':'emplois','web_visits':'visites','engagements':'engagements'}


def metric_catalog(access, sources):
    return [m.describe(sources) for m in METRICS.values() if all(s in sources and sources[s]['module'] in access.allowed_modules for s in m.fields)]


def calculate(metric, totals):
    values = [totals[(source,field)] for source,fields in metric.fields.items() for field in fields]
    if metric.kind == 'sum':
        return round(values[0],4)
    if metric.kind == 'difference':
        return round(values[0]-values[1],4)
    if metric.kind == 'roi':
        return round(100*(values[0]-values[1])/values[1],4) if values[1] else None
    return round(values[0]/values[1]*({'percent':100,'per_thousand':1000}.get(metric.kind,1)),4) if values[1] else None


def evaluate(metric, data):
    """Réducteurs autorisés sur données structurées ; aucun langage exécutable."""
    import math
    from collections import defaultdict
    if metric.expression:
        from .custom import KpiDefinition, term_sum
        spec=KpiDefinition.model_validate(metric.expression)
        a,b=term_sum(spec.numerator,data),term_sum(spec.denominator,data)
        if spec.operation=='difference': return round(a-b,4)
        return round(a/b*(100 if spec.operation=='percent' else 1),4) if b else None
    rows = data[next(iter(metric.fields))]
    field = metric.fields[next(iter(metric.fields))][0]
    if metric.kind == 'international':
        return sum(r[field] for r in rows if r['market'] != 'Maroc')
    if metric.kind in ['hhi','diversification','gini','seasonality','annual_growth','cagr']:
        group = {'hhi':'market','diversification':'market','gini':'destination'}.get(metric.kind,'month')
        totals = defaultdict(float)
        for row in rows:
            totals[row[group]] += row[field]
        values = list(totals.values()); total = sum(values)
        if not total:
            return None
        if metric.kind in ['hhi','diversification']:
            concentration = sum((v/total)**2 for v in values)
            value = concentration*10000 if metric.kind == 'hhi' else 1-concentration
        elif metric.kind == 'gini':
            value = sum(abs(a-b) for a in values for b in values)/(2*len(values)*total)
        elif metric.kind == 'seasonality':
            months = sorted(totals)
            distance = (int(months[-1][:4])-int(months[0][:4]))*12+int(months[-1][5:7])-int(months[0][5:7])+1
            if len(months)<12 or distance != len(months):
                return None
            mean=total/len(values)
            value=100*math.sqrt(sum((v-mean)**2 for v in values)/len(values))/mean
        else:
            years = defaultdict(list)
            for month, value in totals.items():
                years[int(month[:4])].append(value)
            ordered=sorted(years)
            if len(ordered)<2 or any(len(years[y])!=12 for y in ordered):
                return None
            first = ordered[-2] if metric.kind=='annual_growth' else ordered[0]
            baseline=sum(years[first]); last=sum(years[ordered[-1]])
            if not baseline or (metric.kind=='annual_growth' and ordered[-1]-first!=1):
                return None
            value=100*((last/baseline)**(1/(ordered[-1]-first))-1)
        return round(value,4)
    totals={(s,f):sum(r[f] for r in rows) for s,rows in data.items() for f in metric.fields[s]}
    return calculate(metric,totals)
