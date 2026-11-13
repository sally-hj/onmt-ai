"""Conversation persistante : chaque résultat cite l'outil réellement appelé."""
from threading import Lock
from uuid import uuid4

from app.core.errors import AppError, forbidden
from app.schemas.report import ReportRequest, ReportRevisionRequest
from .context import analysis_request
from .graph import build_graph


MESSAGES = {
    'fr':('Analyse calculée depuis les QVD autorisés.','Précise l’indicateur, la destination et les périodes souhaitées.','Le rapport est prêt.','La nouvelle version du rapport est prête.'),
    'en':('Analysis calculated from authorized QVD files.','Please specify the metric, destination and periods.','Your report is ready.','The revised report is ready.'),
    'es':('Análisis calculado desde los QVD autorizados.','Indica el indicador, destino y períodos.','El informe está listo.','La nueva versión está lista.'),
    'ar':('تم حساب التحليل من ملفات البيانات المسموح بها.','يرجى تحديد المؤشر والوجهة والفترات المطلوبة.','التقرير جاهز.','النسخة الجديدة من التقرير جاهزة.'),
    'ary':('تحسب التحليل من ملفات البيانات المسموح بها.','حدد لينا المؤشر والوجهة والفترات اللي بغيتي.','التقرير واجد.','النسخة الجديدة ديال التقرير واجدة.')}


class ConversationService:
    def __init__(self,state,analytics,reports,exporter,parser):
        self.state,self.analytics,self.reports,self.exporter,self.parser = state,analytics,reports,exporter,parser
        self.lock = Lock()
        self.graph = build_graph(self._interpret,self._execute)

    def _title(self, analysis, access, multiple=False):
        label=next((m['label'] for m in self.analytics.metrics(access) if m['id']==analysis.metric_id),analysis.metric_id)
        scope='comparaison des périmètres' if multiple else analysis.filters.get('destination','Territoires autorisés')
        return f'{label} — {scope} — {analysis.period.start}/{analysis.period.end}'

    def _interpret(self, turn):
        catalog = self.analytics.catalog.describe(turn['access'])
        allowed = {'metrics':[{k:m[k] for k in ['id','label']} for m in self.analytics.metrics(turn['access'])],
                   'destinations':turn['access'].allowed_territories,
                   'markets':sorted({m for s in catalog['sources'] for m in s.get('markets',[])})}
        intent = self.parser.parse(turn['message'],turn['context'],allowed,turn['language'])
        return {'intent':intent}

    def _execute(self, turn):
        intent, access, context = turn['intent'],turn['access'],dict(turn['context'])
        text = MESSAGES[intent.language]
        response = {'message':text[1],'actions':[{'tool':'intent','status':'completed','detail':intent.action}],
                    'language':intent.language,'needs_clarification':False}
        if intent.action == 'clarify':
            response.update(message=intent.clarification or text[1],needs_clarification=True)
        elif intent.action in ['analyse','benchmark','update_report']:
            request = analysis_request(intent,context)
            if request is None:
                response.update(message=text[1],needs_clarification=True)
            else:
                if intent.action == 'update_report' and not context.get('report_id'):
                    raise AppError('missing_data','Aucun rapport dans cette conversation à recalculer.',422)
                if intent.action=='benchmark':
                    request=request.model_copy(update={'filters':{k:v for k,v in request.filters.items() if k!=intent.group_by}})
                    results=self.analytics.benchmark(request,access,intent.group_by,intent.dimensions)
                    result=results[-1]
                    context['analysis_ids']=[a.analysis_id for a in results]
                    response.update(message=text[0],benchmark=[a.model_dump(mode='json') for a in results])
                else:
                    result=self.analytics.run(request,access)
                    context['analysis_ids']=[result.analysis_id]
                    response.update(message=text[0],analysis=result.model_dump(mode='json'))
                context.update(analysis_request=request.model_dump(mode='json'),analysis_id=result.analysis_id)
                response['actions'].append({'tool':'analytics.benchmark' if intent.action=='benchmark' else 'analytics.run','status':'completed','detail':result.formula})
                if intent.action == 'update_report':
                    report = self.reports.recalculate_report(context['report_id'],[result.analysis_id],context['report_version'],access,
                                                             title=self._title(result,access))
                    response['report'] = report.model_dump(mode='json')
                    response['message'] = text[3]
                    context['report_version'] = report.version
                    response['actions'].append({'tool':'reports.recalculate','status':'completed','detail':'Nouveaux calculs ; sections et dépendances régénérées.'})
        elif intent.action == 'report':
            if not context.get('analysis_id'):
                response.update(message=text[1],needs_clarification=True)
            else:
                analysis = self.analytics.get_analysis(context['analysis_id'],access)
                request = ReportRequest(request_id=uuid4().hex,analysis_ids=context.get('analysis_ids',[analysis.analysis_id]),
                    title=self._title(analysis,access,len(context.get('analysis_ids',[]))>1),
                    language=intent.language,audience=intent.audience,sections=['summary'])
                report = self.reports.create_report(request,access)
                context.update(report_id=report.report_id,report_version=report.version)
                response.update(message=text[2],report=report.model_dump(mode='json'))
                response['actions'].append({'tool':'reports.create','status':'completed','detail':'Analyse QVD, recherche documentaire et rédaction validée.'})
        elif intent.action == 'revise':
            if not context.get('report_id'):
                response.update(message=text[1],needs_clarification=True)
            else:
                report = self.reports.revise_report(ReportRevisionRequest(request_id=uuid4().hex,report_id=context['report_id'],
                    base_version=context['report_version'],section_id=intent.section_id,instruction=intent.instruction or 'reformuler'),access)
                context['report_version'] = report.version
                response.update(message=text[3],report=report.model_dump(mode='json'))
                response['actions'].append({'tool':'reports.revise','status':'completed','detail':intent.instruction})
        elif intent.action == 'document':
            found = self.reports.retriever.search_evidence(intent.instruction or turn['message'],access)
            response.update(message='Passages documentaires retrouvés.' if found.evidence else 'Aucun passage documentaire autorisé pertinent.',evidence=found.model_dump(mode='json'))
            response['actions'].append({'tool':'documents.search','status':'completed','detail':str(len(found.evidence))+' passages'})
        return {'response':response,'context':context}

    def send(self, message, access, cid=None, base_version=0, language='fr'):
        # Un tour par service à la fois : les modèles locaux sont eux aussi sérialisés.
        if not self.lock.acquire(blocking=False):
            raise AppError('busy','Une conversation est en cours de traitement ; réessayez après sa fin.',409)
        try:
            saved = self.state.conversation(cid,access.user_id) if cid else None
            if cid and not saved:
                raise forbidden()
            if (saved or {}).get('version',0) != base_version:
                raise AppError('version_conflict','Conversation modifiée ; rechargez son état.',409)
            cid = cid or 'chat_'+uuid4().hex
            context = saved.get('context',{}) if saved else {}
            for analysis_id in context.get('analysis_ids',[context.get('analysis_id')]):
                if analysis_id:
                    self.analytics.authorize_snapshot(analysis_id,access)
            turn = self.graph.invoke({'message':message,'context':context,'access':access,'language':language},
                                     config={'recursion_limit':6})
            response = turn['response']
            history = list(saved.get('messages',[])) if saved else []
            history.extend([{'role':'user','message':message},{'role':'assistant',**response}])
            payload = {'conversation_id':cid,'version':base_version+1,'context':turn['context'],'messages':history}
            self.state.save_conversation(cid,access.user_id,payload,base_version)
            return {'conversation_id':cid,'version':base_version+1,**response}
        finally:
            self.lock.release()

    def link_context(self, access, cid, base_version, analysis_id=None, report_id=None):
        """Synchroniser une sélection/révision faite dans un écran complémentaire avec le chat."""
        if not self.lock.acquire(blocking=False):
            raise AppError('busy','Conversation en cours ; réessayez après son traitement.',409)
        try:
            saved = self.state.conversation(cid,access.user_id) if cid else None
            if cid and not saved:
                raise forbidden()
            if (saved or {}).get('version',0) != base_version:
                raise AppError('version_conflict','Le contexte a changé ; rechargez la conversation.',409)
            context = dict((saved or {}).get('context',{}))
            if report_id:
                report = self.reports.get_report(report_id,access)
                context.update(report_id=report_id,report_version=report.version)
                ids = self.reports.store.report(report_id)['request']['analysis_ids']
                if analysis_id and analysis_id not in ids:
                    raise AppError('invalid_request','L’analyse sélectionnée ne fait pas partie de ce rapport.',422)
                analysis_id = analysis_id or ids[-1]
            if analysis_id:
                analysis = self.analytics.get_analysis(analysis_id,access)
                context.update(analysis_id=analysis.analysis_id,analysis_ids=ids if report_id else [analysis.analysis_id],
                               analysis_request=self.state.analysis(analysis_id,access.user_id)['request'])
            cid = cid or 'chat_'+uuid4().hex
            payload = {'conversation_id':cid,'version':base_version+1,'context':context,'messages':(saved or {}).get('messages',[])}
            self.state.save_conversation(cid,access.user_id,payload,base_version)
            return payload
        finally:
            self.lock.release()
