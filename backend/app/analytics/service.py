from app.core.timing import measured
"""Calculs QVD testables et adaptateur AnalysisProvider pour les rapports de Salma."""
import calendar
from collections import defaultdict
from datetime import date
from pathlib import Path
from uuid import uuid4

from app.core.errors import AppError, forbidden
from app.schemas.analysis import AnalysisResult, SeriesPoint
from app.schemas.common import SourceReference
from .forecasting import forecast
from .metrics import METRICS, FIELD_UNITS, evaluate, metric_catalog


class AnalyticsService:
    def __init__(self, catalog, state):
        self.catalog,self.state = catalog,state
        from .custom import CustomKpis
        self.custom = CustomKpis(state,catalog)
        from .products import Products
        self.products=Products(self)

    def metrics(self, access):
        return metric_catalog(access,self.catalog.sources)+[{**self.custom.metric(p).describe(self.catalog.sources),'author':p['author'],'created_at':p['created_at']} for p in self.custom.list(access)]

    def benchmark(self, request, access, group_by, dimensions=None):
        if group_by not in ['destination','market']:
            raise AppError('invalid_request','Dimension de comparaison non prise en charge.',422)
        self._metric(request.metric_id,access)
        request=request.model_copy(update={'filters':{k:v for k,v in request.filters.items() if k!=group_by}})
        if not dimensions:
            if group_by=='destination':
                dimensions=access.allowed_territories
            else:
                metric=self._metric(request.metric_id,access)
                sid=next(iter(metric.fields))
                rows,_=self.catalog.read_authorized_data(sid,['market'],request.filters,access)
                dimensions=sorted({r['market'] for r in rows})
        if not 1<=len(dimensions)<=12 or len(set(dimensions))!=len(dimensions):
            raise AppError('invalid_request','Comparaison limitée à douze périmètres distincts.',422)
        if group_by=='destination' and not set(dimensions).issubset(access.allowed_territories):
            raise forbidden()
        results=[]
        for dimension in dimensions:
            filters={**request.filters,group_by:dimension}
            item=request.model_copy(update={'request_id':uuid4().hex,'filters':filters})
            results.append(self.run(item,access))
        return results

    def _metric(self, metric_id, access):
        metric = METRICS.get(metric_id)
        if metric is None:
            metric=next((self.custom.metric(p) for p in self.custom.list(access) if p['definition']['id']==metric_id),None)
        if not metric:
            raise AppError('missing_data','Indicateur non défini ; aucun calcul inventé.',422)
        if any(s not in self.catalog.sources for s in metric.fields):
            raise AppError('missing_data','Source complémentaire absente ; préparez le corpus étendu.',422)
        if any(self.catalog.sources[s]['module'] not in access.allowed_modules for s in metric.fields):
            raise forbidden()
        return metric

    def _read(self, metric, filters, access):
        data, refs = {}, []
        for sid, fields in metric.fields.items():
            source = self.catalog.sources[sid]
            if any(source.get('units',{}).get(f) != FIELD_UNITS.get(f,'MAD') for f in fields):
                raise AppError('data_quality','Unité incompatible avec la définition de l’indicateur ; validez le mapping métier.',422)
            rows, version = self.catalog.read_authorized_data(sid,['month','destination','market',*fields],filters,access)
            data[sid] = rows
            refs.append(SourceReference(source_id=sid,source_type='qvd',name=Path(source['file']).name,version=version,
                        fields=[source['fields'][f] for f in ['month','destination','market',*fields]],pages=[]))
        if len(data)>1:
            grains = [{(r['month'],r['destination'],r['market']) for r in rows} for rows in data.values()]
            if any(s != grains[0] for s in grains[1:]):
                raise AppError('data_quality','Rapprochement refusé : périmètres ou grains des sources différents.',422)
        return data,refs

    def _aggregate(self, metric, data, period):
        selected = {s:[r for r in rows if period.start <= date.fromisoformat(r['month']) <= period.end] for s,rows in data.items()}
        if any(not rows for rows in selected.values()):
            return None,[],['requested_period_has_no_data']
        months = sorted({r['month'] for rows in selected.values() for r in rows})
        warnings = []
        expected = (period.end.year-period.start.year)*12+period.end.month-period.start.month+1
        if len(months) != expected:
            warnings.append('incomplete_requested_month_range')
        # Chaque destination/marché sélectionné doit être présent tous les mois.
        for sid,rows in selected.items():
            scopes = {(r['destination'],r['market']) for r in data[sid]}
            if len(rows) != len(months)*len(scopes):
                warnings.append('incomplete_monthly_scope_grid')
        def value_for(month=None):
            return evaluate(metric,{s:[r for r in rows if month is None or r['month']==month] for s,rows in selected.items()})
        points = [SeriesPoint(date=date.fromisoformat(m),value=value_for(m),kind='observed') for m in months]
        value = value_for()
        if value is None:
            warnings.append('insufficient_complete_history' if metric.kind in ['annual_growth','cagr','seasonality'] else 'zero_denominator')
        return value,points,warnings

    @measured('calcul_controles')
    def run(self, request, access):
        metric = self._metric(request.metric_id,access)
        for period in [request.period,request.comparison_period]:
            if period and (period.start.day != 1 or period.end.day != calendar.monthrange(period.end.year,period.end.month)[1]):
                raise AppError('invalid_request','Sources mensuelles : sélectionner des mois complets.',422)
        if request.operation == 'forecast' and request.forecast_frequency != 'month':
            raise AppError('invalid_request','Le modèle local prévoit uniquement des mois ; fréquence non prise en charge.',422)
        data,sources = self._read(metric,request.filters,access)
        current,series,warnings = self._aggregate(metric,data,request.period)
        values = {'value':current}
        if request.operation == 'compare':
            previous,_,other = self._aggregate(metric,data,request.comparison_period)
            warnings += other
            change = round((current-previous)/previous*100,4) if current is not None and previous not in [None,0] else None
            values = {'current':current,'previous':previous,'change_pct':change}
            if change is None:
                warnings.append('comparison_unavailable_or_zero_baseline')
        elif request.operation == 'forecast':
            projected,extra = forecast(series,request.forecast_horizon)
            series += projected; warnings += extra
            values = {}
        if self.catalog.config['synthetic']:
            warnings.append('synthetic_data_no_economic_causality')
        warnings.append(metric.limit)
        if metric.expression: warnings.append(f'metric_definition_version:{metric.version}')
        incomplete = any(w.startswith(('incomplete_','requested_period','zero_denominator','comparison_unavailable')) for w in warnings)
        result = AnalysisResult(request_id=request.request_id,analysis_id='ana_'+uuid4().hex,metric_id=metric.id,
            status='unavailable' if current is None else 'partial' if incomplete else 'ok',period=request.period,
            comparison_period=request.comparison_period,filters=request.filters,unit=metric.unit,values=values,series=series,
            formula=metric.source_formula(self.catalog.sources),sources=sources,warnings=sorted(set(warnings)),is_synthetic=self.catalog.config['synthetic'])
        self.state.save_analysis(result,access.user_id,request,access.allowed_territories)
        self.state.audit_log.append(access.user_id,request.request_id,'analytics.run',result.analysis_id,
            outcome=result.status,versions={s.source_id:s.version for s in result.sources},
            details={'formula':result.formula,'period':request.period.model_dump(mode='json'),'filters':request.filters})
        return result

    def authorize_snapshot(self, analysis_id, access_context):
        payload = self.state.analysis(analysis_id,access_context.user_id)
        if not payload:
            raise forbidden()
        result = AnalysisResult.model_validate(payload['result'])
        metric=self._metric(result.metric_id,access_context)
        destination = result.filters.get('destination')
        if destination and destination not in access_context.allowed_territories:
            raise forbidden()
        # Un résultat agrégé sans filtre est lié au périmètre exact du compte lors du calcul.
        request_scope = payload.get('request_scope')
        if request_scope is None or not set(request_scope).issubset(access_context.allowed_territories):
            raise forbidden()
        return result

    def get_analysis(self, analysis_id, access_context):
        result = self.authorize_snapshot(analysis_id,access_context)
        metric=self._metric(result.metric_id,access_context)
        if metric.expression and f'metric_definition_version:{metric.version}' not in result.warnings:
            raise AppError('stale_analysis','Définition du KPI modifiée ; recalcul requis.',409)
        versions = self.catalog.versions([s.source_id for s in result.sources])
        if any(versions[s.source_id] != s.version for s in result.sources):
            raise AppError('stale_analysis','Sources modifiées : relancez le calcul avant de réutiliser ce résultat.',409)
        return result
