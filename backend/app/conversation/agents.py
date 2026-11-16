"""Spécialistes à politiques Python ; Qwen planifie, les outils calculent.

Chaque spécialiste prend une décision, transmet des résultats structurés et respecte
les droits du tour. Les traces décrivent les tâches ; aucun raisonnement interne LLM.
"""
from uuid import uuid4
from app.core.errors import forbidden
from app.core.timing import measured
from .context import analysis_request

AGENTS={
 'territorial': {'inputs':'intention, droits, catalogue','outputs':'périmètre validé ou refus','tools':['droits.territoires'],'failure':'territoire interdit'},
 'marches': {'inputs':'KPI, périodes, marchés/destinations','outputs':'analyses ou benchmark sourcé','tools':['analytics.run','analytics.benchmark'],'failure':'source ou période absente'},
 'saisonnalite': {'inputs':'historique mensuel autorisé','outputs':'pic descriptif et décision de vérifier le budget','tools':['analytics.run'],'failure':'historique insuffisant'},
 'budget_performance': {'inputs':'demande ou pic transmis','outputs':'budget, dépense et coût par nuitée ; aucune causalité','tools':['analytics.run'],'failure':'droits Finance absents ou grain incompatible'},
 'recherche': {'inputs':'question, KPI, filtres et périodes','outputs':'passages autorisés avec versions/pages ou absence explicite','tools':['retriever.search_evidence'],'failure':'index indisponible'},
 'comex': {'inputs':'résultats calculés, preuves, demande de livrable','outputs':'réponse ou rapport versionné','tools':['reports.create','reports.revise'],'failure':'rédaction non vérifiée'},
 'verification': {'inputs':'réponse et références','outputs':'droits et fraîcheur contrôlés, trace factuelle','tools':['analytics.get_analysis','reports.get_report'],'failure':'source modifiée ou droit retiré'},
}


class Specialists:
    def __init__(self,analytics,reports): self.analytics,self.reports=analytics,reports

    def record(self,turn,agent,decision,analyses=()):
        trace=list(turn.get('specialist_trace',[]))
        trace.append({'agent':agent,'decision':decision,'tools':AGENTS[agent]['tools'],
            'analysis_ids':[a.analysis_id for a in analyses],
            'sources':[s.model_dump(mode='json') for a in analyses for s in a.sources]})
        self.reports.store.audit_log.append(turn['access'].user_id,turn.get('request_id','agent'),f'agent.{agent}',decision,
            versions={s.source_id:s.version for a in analyses for s in a.sources})
        return trace

    def request(self,turn): return analysis_request(turn['intent'],turn['context'])

    def route(self,turn):
        intent=turn['intent']; request=self.request(turn)
        if intent.action in ['document','report']: return 'research'
        if request is None: return 'execute'
        if intent.action=='briefing': return 'markets'
        if intent.action not in ['analyse','benchmark','update_report']: return 'execute'
        if request.operation=='forecast' or request.metric_id in ['seasonality','annual_growth','annual_cagr']: return 'seasonality'
        metric=self.analytics._metric(request.metric_id,turn['access'])
        return 'budget' if 'finance' in metric.fields else 'markets'

    @measured('agent_territorial')
    def territorial(self,turn):
        request=self.request(turn)
        if request and request.filters.get('destination') and request.filters['destination'] not in turn['access'].allowed_territories: raise forbidden()
        return {'specialist_trace':self.record(turn,'territorial','Périmètre vérifié avec les droits serveur.')}

    @measured('agent_marches')
    def markets(self,turn):
        request=self.request(turn); intent=turn['intent']
        if intent.action=='briefing': request=request.model_copy(update={'metric_id':'overnight_stays'})
        results=self.analytics.benchmark(request,turn['access'],intent.group_by,intent.dimensions) if intent.action=='benchmark' else [self.analytics.run(request,turn['access'])]
        return {'prepared':results,'specialist_trace':self.record(turn,'marches','Comparaison de périmètres.' if len(results)>1 else 'Calcul du KPI demandé.',results)}

    @measured('agent_saisonnalite')
    def seasonality(self,turn):
        request=self.request(turn)
        if turn['intent'].action=='briefing':
            request=request.model_copy(update={'metric_id':'overnight_stays','operation':'value','comparison_period':None})
            results=turn.get('prepared',[]); analysis=results[0] if results else self.analytics.run(request,turn['access'])
        else: analysis=self.analytics.run(request,turn['access']); results=[analysis]
        observed=[p for p in analysis.series if p.kind=='observed' and p.value is not None]
        complete=len(observed)>=12; mean=sum(p.value for p in observed)/len(observed) if observed else 0
        peak=max(observed,key=lambda p:p.value) if observed else None
        seasonal={'status':'ok' if complete else 'insufficient_history','peak_month':str(peak.date) if peak and complete else None,
            'peak_over_mean':round(peak.value/mean,4) if peak and mean and complete else None,
            'needs_budget':bool(complete and mean and peak.value/mean>=1.2),
            'interpretation':'Pic descriptif ≥ 120% de la moyenne ; vérifier les dépenses de même périmètre, sans attribution causale.'}
        return {'prepared':results,'seasonal':seasonal,'specialist_trace':self.record(turn,'saisonnalite',
            'Pic détecté : demande de contrôle Budget.' if seasonal['needs_budget'] else 'Aucun pic exploitable ; aucun stade du cycle inféré.',[analysis])}

    @measured('agent_budget')
    def budget(self,turn):
        request=self.request(turn); access=turn['access']; results=list(turn.get('prepared',[]))
        if 'finance' not in access.allowed_modules:
            if turn['intent'].action=='briefing' or not results: raise forbidden()
            return {'specialist_trace':self.record(turn,'budget_performance','Contrôle Finance non autorisé ; aucune donnée lue.')}
        if turn['intent'].action=='briefing' or turn.get('seasonal',{}).get('needs_budget'):
            for metric in ['budget','spent','spend_per_night','click_rate']:
                results.append(self.analytics.run(request.model_copy(update={'request_id':uuid4().hex,'metric_id':metric,'operation':'value','comparison_period':None,'forecast_horizon':None,'forecast_frequency':None}),access))
        else: results=[self.analytics.run(request,access)]
        return {'prepared':results,'specialist_trace':self.record(turn,'budget_performance','Périmètres rapprochés ; aucune efficacité causale déduite.',results)}

    @measured('agent_recherche')
    def research(self,turn):
        request=self.request(turn)
        if turn['intent'].action in ['report','briefing']:
            from app.schemas.report import ReportRequest
            analyses=turn.get('prepared',[]) or [self.analytics.get_analysis(i,turn['access']) for i in turn['context'].get('analysis_ids',[])]
            if analyses:
                query=ReportRequest(request_id=uuid4().hex,analysis_ids=[a.analysis_id for a in analyses],title=turn['message'][:300],
                    question=turn['message'],language=turn['language'],audience=turn['intent'].audience,sections=['summary','diagnostic'])
                found=self.reports.retriever.search_report(query,analyses,turn['access'])
            else: found=self.reports.retriever.search_evidence(turn['message'],turn['access'])
        else: found=self.reports.retriever.search_evidence(turn['intent'].instruction or turn['message'],turn['access'])
        return {'evidence_result':found,'specialist_trace':self.record(turn,'recherche',f'{len(found.evidence)} passages autorisés ; absence de preuve conservée si nécessaire.')}

    @measured('agent_verification')
    def verify(self,turn):
        response=turn['response']; access=turn['access']
        for a in response.get('benchmark',[])+([response['analysis']] if response.get('analysis') else []): self.analytics.get_analysis(a['analysis_id'],access)
        if response.get('report'): self.reports.get_report(response['report']['report_id'],access)
        response['agent_trace']=self.record(turn,'verification','Droits, versions et références contrôlés.')
        if turn.get('seasonal'): response['seasonal_diagnostic']=turn['seasonal']
        return {'response':response,'specialist_trace':response['agent_trace']}
