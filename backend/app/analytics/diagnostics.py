"""Outils de diagnostic transparents, indépendants de la prose du modèle."""
import math
import calendar
from collections import defaultdict
from datetime import date

from app.core.config import ROOT
from app.core.errors import AppError, forbidden
from app.data_access.catalog import Catalog
from app.data_access.supplement import COMPARATORS, REGIONS


def butler(series):
    """Indication sur cinq années complètes ; aucune identification certaine d'un cycle."""
    years=defaultdict(dict)
    for p in series:
        if p.value is not None and p.kind=='observed': years[p.date.year][p.date.month]=p.value
    complete=sorted(y for y,months in years.items() if len(months)==12)
    answer={'stage':'indetermine','confidence':'faible','simulation':True,
            'rule':'5 années complètes consécutives ; 3 variations >5% : développement ; 3 variations dans ±2% : stabilité ; 3 variations <−5% : déclin possible ; sinon indéterminé.',
            'limit':'Les flux seuls ne décrivent ni capacité, ni impacts sociaux, ni gouvernance ; aucune certitude sur un stade Butler.'}
    if len(complete)<5 or complete[-1]-complete[-5]!=4: return answer
    values=[sum(years[y].values()) for y in complete[-5:]]
    if any(v<=0 for v in values): return answer
    growth=[100*(b/a-1) for a,b in zip(values,values[1:])]
    recent=growth[-3:]
    stage='developpement_possible' if all(x>5 for x in recent) else 'stabilite_possible' if all(abs(x)<=2 for x in recent) else 'declin_possible' if all(x < -5 for x in recent) else 'indetermine'
    return {**answer,'stage':stage,'annual_growth_pct':growth,'years':complete[-5:]}


def bcg_point(current, previous, market_current, market_previous, competitor, threshold=5):
    if min(previous,market_previous,competitor)<=0:
        return {'quadrant':'indetermine','market_growth_pct':None,'relative_share':None}
    growth=100*(market_current/market_previous-1); share=current/competitor
    quadrant=('vedette' if share>=1 else 'dilemme') if growth>=threshold else ('vache_a_lait' if share>=1 else 'poids_mort')
    return {'quadrant':quadrant,'market_growth_pct':round(growth,4),'relative_share':round(share,4)}


class Diagnostics:
    def __init__(self, analytics): self.analytics=analytics

    def international(self, period, comparison, access, threshold=5,regional=False):
        if 'commercial' not in access.allowed_modules: raise forbidden()
        source_id='regional' if regional else 'international'
        names=REGIONS if regional else COMPARATORS
        catalog=Catalog(ROOT/f'config/sources.{source_id}.json',self.analytics.catalog.reader.root)
        for window in [period,comparison]:
            if window.start.day!=1 or window.end.day!=calendar.monthrange(window.end.year,window.end.month)[1]:
                raise AppError('invalid_request','Benchmark mensuel : mois complets requis.',422)
        if (period.start.month,period.end.month)!=(comparison.start.month,comparison.end.month):
            raise AppError('invalid_request','Comparer les mêmes mois pour une croissance non corrigée de la saisonnalité.',422)
        # Ce catalogue distinct ne contient que des agrégats comparateurs synthétiques
        # partagés ; cet élargissement ne s'applique jamais aux QVD internes.
        shared=access.model_copy(update={'allowed_territories':names})
        fields=list(catalog.sources[source_id]['units'])
        from .metrics import FIELD_UNITS
        expected={f:('arrivees' if f in ['market_total_arrivals','competitor_arrivals'] else FIELD_UNITS.get(f,'MAD')) for f in fields}
        if catalog.sources[source_id]['units']!=expected:
            raise AppError('data_quality','Unités du benchmark incompatibles ; aucune conversion monétaire implicite.',422)
        rows,version=catalog.read_authorized_data(source_id,['month','destination','market',*fields],{},shared)
        def totals(name,window):
            chosen=[r for r in rows if r['destination']==name and window.start<=date.fromisoformat(r['month'])<=window.end]
            expected=(window.end.year-window.start.year)*12+window.end.month-window.start.month+1
            if len(chosen)!=expected: raise AppError('missing_data','Comparateurs incomplets pour la période.',422)
            return {f:sum(r[f] for r in chosen) for f in fields}
        result=[]
        for name in names:
            c,p=totals(name,period),totals(name,comparison)
            def ratio(a,b,factor=1): return round(c[a]/c[b]*factor,4) if c[b] else None
            indicators={'arrivals':c['arrivals'],'overnight_stays':c['overnight_stays'],'seats':c['seats'],'bookings':c['bookings'],
                'travel_receipts':c['travel_receipts'],'room_revenue':c['room_revenue'],
                'average_stay':ratio('overnight_stays','arrivals'),'occupancy':ratio('rooms_sold','rooms_available',100),
                'revpar':ratio('room_revenue','rooms_available'),'average_room_price':ratio('room_revenue','rooms_sold'),
                'receipts_per_arrival':ratio('travel_receipts','arrivals'),'receipts_per_night':ratio('travel_receipts','overnight_stays'),
                'tourism_gdp_share':ratio('tourism_gva','gdp',100)}
            point=bcg_point(c['arrivals'],p['arrivals'],c['market_total_arrivals'],p['market_total_arrivals'],c['competitor_arrivals'],threshold)
            result.append({'destination':name,'indicators':indicators,**point})
        return {'kind':'bcg_regions' if regional else 'international','synthetic':True,'period':period.model_dump(mode='json'),'comparison_period':comparison.model_dump(mode='json'),
                'rows':result,'units':{'arrivals':'arrivees','overnight_stays':'nuitees','seats':'sieges','bookings':'reservations','travel_receipts':'MAD',
                'room_revenue':'MAD','average_stay':'nuits/arrivee','occupancy':'%','revpar':'MAD/chambre-nuit','average_room_price':'MAD/chambre-nuit',
                'receipts_per_arrival':'MAD/arrivee','receipts_per_night':'MAD/nuitee','tourism_gdp_share':'%'},
                'source':{'id':source_id,'name':source_id+'.qvd','version':version,'fields':fields},
                'bcg':{'growth_threshold_pct':threshold,'relative_share_threshold':1,'x':'Arrivées de la destination / arrivées de son principal concurrent fictif',
                       'y':'100 * (arrivées du marché total actuel / marché total précédent − 1)'},
                'comparability':('Douze régions aux noms réels, indicateurs et marchés concurrentiels fictifs ; aucun découpage cartographique inventé. ' if regional else 'Scénario fictif de périmètres touristiques comparables : pays et Dubaï comme destination, pas classement officiel de pays. ')+ 'Même calendrier mensuel, définitions et MAD de scénario ; aucune conversion monétaire ni statistique externe.',
                'warning':'Les marchés totaux et concurrents sont fictifs. Les ratios BCG ne sont pas des parts internes des nuitées.'}

    def value_volume(self, request, access, value_threshold=2500, volume_threshold=10000):
        from app.schemas.analysis import AnalysisRequest
        request=request.model_copy(update={'operation':'value','comparison_period':None,'forecast_horizon':None,'forecast_frequency':None})
        dimensions=[request.filters['market']] if request.filters.get('market') else None
        arrivals=self.analytics.benchmark(request.model_copy(update={'metric_id':'arrivals'}),access,'market',dimensions)
        receipts=self.analytics.benchmark(request.model_copy(update={'metric_id':'travel_receipts'}),access,'market',dimensions)
        lookup={a.filters['market']:a for a in receipts}
        points=[]
        for a in arrivals:
            volume=a.values['value']; b=lookup[a.filters['market']]; revenue=b.values['value']
            value=revenue/volume if volume and revenue is not None else None
            quadrant='indetermine' if value is None else ('valeur_forte' if value>=value_threshold else 'valeur_faible')+'_'+('volume_fort' if volume>=volume_threshold else 'volume_faible')
            points.append({'market':a.filters['market'],'volume':volume,'value':round(value,4) if value is not None else None,'quadrant':quadrant,'analysis_ids':[a.analysis_id,b.analysis_id]})
        return {'kind':'value_volume','synthetic':self.analytics.catalog.config['synthetic'],'points':points,
                'period':request.period.model_dump(mode='json'),'filters':request.filters,'thresholds':{'value_mad_per_arrival':value_threshold,'volume_arrivals':volume_threshold},
                'formula':'Valeur = SUM(recettes voyages) / SUM(arrivées) ; volume = SUM(arrivées), par marché émetteur.',
                'interpretation':'Quatre segments descriptifs : valeur et volume forts/faibles. Déplacer les seuils peut changer le quadrant ; aucun potentiel ou rentabilité déduit automatiquement.'}

    def destination(self, request, access):
        analysis=self.analytics.run(request.model_copy(update={'metric_id':'overnight_stays','operation':'value','comparison_period':None,'forecast_horizon':None,'forecast_frequency':None}),access)
        return {'kind':'butler','synthetic':analysis.is_synthetic,'analysis_id':analysis.analysis_id,**butler(analysis.series)}

    def map(self,request,access):
        import json
        geography=json.loads((ROOT/'config/geography.json').read_text(encoding='utf-8'))
        dimensions=[request.filters['destination']] if request.filters.get('destination') else None
        results=self.analytics.benchmark(request,access,'destination',dimensions)
        locations={p['destination']:p for p in geography['points']}
        points=[{**locations[a.filters['destination']],'value':a.values.get('value',a.values.get('current')),
                 'unit':a.unit,'analysis_id':a.analysis_id} for a in results if a.filters['destination'] in locations]
        return {'kind':'map','synthetic':self.analytics.catalog.config['synthetic'],'period':request.period.model_dump(mode='json'),
                'metric_id':request.metric_id,'points':points,'geography':{k:v for k,v in geography.items() if k!='points'},
                'warning':'Géographie réelle et indicateurs synthétiques ; taille des points proportionnelle à la racine de la valeur absolue, sans limites administratives.'}

    def scenario(self,request,access,shock_pct):
        metric=self.analytics._metric(request.metric_id,access)
        if metric.kind not in ['sum','international']:
            raise AppError('invalid_request','Ce scénario proportionnel accepte un volume ou montant additif ; préciser un modèle pour un ratio ou indice.',422)
        if not -90<=shock_pct<=100: raise AppError('invalid_request','Choc de scénario limité entre −90% et +100%.',422)
        baseline=self.analytics.run(request.model_copy(update={'operation':'value','comparison_period':None,'forecast_horizon':None,'forecast_frequency':None}),access)
        value=baseline.values['value']
        if value is None: raise AppError('missing_data','Aucune valeur de référence pour ce scénario.',422)
        return {'kind':'scenario','synthetic':baseline.is_synthetic,'analysis_id':baseline.analysis_id,
                'metric_id':baseline.metric_id,'baseline':value,'shock_pct':shock_pct,'scenario_value':round(value*(1+shock_pct/100),4),
                'unit':baseline.unit,'period':request.period.model_dump(mode='json'),'filters':baseline.filters,
                'formula':'scenario = baseline * (1 + hypothèse_pct / 100)',
                'warning':'Hypothèse utilisateur et transformation mécanique, pas une observation, une prévision probabiliste ou un effet causal démontré.'}
