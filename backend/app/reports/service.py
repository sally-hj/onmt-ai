from datetime import datetime, timezone
from uuid import uuid4

from app.core.errors import AppError, forbidden
from app.core.security import ResourcePolicy, authorize, private_policy, require_module
from app.schemas.analysis import AnalysisResult
from app.schemas.report import ReportRequest, ReportResult
from .documents import DocumentRecord, Evidence
from .generation import generate_sections, generate_edited_sections
from .revisions import parse_revision
from .generation import facts
from .validation import collect_sources, verify_report

DEPENDENTS = {
    'diagnostic': ['summary', 'recommendations', 'limitations'],
    'comparison': ['summary', 'recommendations', 'limitations'],
    'forecast': ['summary', 'recommendations', 'limitations'],
    'recommendations': ['summary'], 'summary': [], 'limitations': ['summary'],
}


class ReportService:
    def __init__(self, store, provider, retriever, planner=None, writer=None):
        self.store, self.provider, self.retriever, self.planner = store, provider, retriever, planner
        self.writer = writer

    def _analyses(self, ids, access):
        analyses = []
        for analysis_id in ids:
            a = self.provider.get_analysis(analysis_id, access)
            a = AnalysisResult.model_validate(a)
            if a.analysis_id != analysis_id:
                raise AppError('tool_failed', 'Le fournisseur a retourné un identifiant d’analyse incohérent.', 502)
            analyses.append(a)
        return analyses

    def create_report(self, request: ReportRequest, access_context, *, report_id=None, base_version=None, section_settings=None, evidence_result=None) -> ReportResult:
        require_module(access_context, True)
        analyses = self._analyses(request.analysis_ids, access_context)
        diagnostics=[]
        if request.diagnostic_ids:
            if not hasattr(self.provider,'products'): raise AppError('missing_data','Diagnostics non connectés.',422)
            diagnostics=[self.provider.products.get(i,access_context) for i in request.diagnostic_ids]
        from app.schemas.common import SourceReference
        diagnostic_sources=[SourceReference(source_id=d['source'].get('id','international'),source_type='qvd',name=d['source']['name'],
            version=d['source']['version'],fields=d['source']['fields'],pages=[]) for d in diagnostics if d.get('source')]
        for diagnostic in diagnostics:
            ids=[diagnostic['analysis_id']] if diagnostic.get('analysis_id') else []
            for point in diagnostic.get('points',[]):
                ids+=point.get('analysis_ids',[])
                if point.get('analysis_id'): ids.append(point['analysis_id'])
            for identifier in ids: diagnostic_sources.extend(self.provider.get_analysis(identifier,access_context).sources)
        found = evidence_result or self.retriever.search_report(request,analyses,access_context)
        evidence, styles = found.evidence, {}
        if self.planner:
            plan = self.planner.plan(request.language, request.audience, '', evidence)
            evidence = [e for e in evidence if e.passage.chunk_id in plan.evidence_ids]
            styles = {s: plan.style for s in request.sections}
        warnings = list(found.warnings)
        for a in analyses:
            warnings.extend(a.warnings)
            if not a.sources:
                warnings.append(f'analysis_sources_absent:{a.analysis_id}')
            if a.status != 'ok':
                warnings.append(f'analysis_{a.status}:{a.analysis_id}')
        if any(a.is_synthetic for a in analyses) or any(d['synthetic'] for d in diagnostics):
            warnings.append('synthetic_data')
        if request.language in ['ar','ary']:
            warnings.append('Brouillon à relire — validation linguistique humaine arabe/darija non réalisée.')
        report_id = report_id or 'rpt_' + uuid4().hex
        section_settings = section_settings or {}
        narratives, sections = {}, []
        if self.writer:
            if len(facts(analyses)) > 6 or len(evidence) > 2:
                warnings.append('ai_context_limited_full_snapshots_available_via_analysis_api')
            for section_id in request.sections:
                section, manifest = self.writer.generate_section(request, section_id, analyses, evidence,section_settings.get(section_id))
                sections.append(section)
                narratives[section_id] = manifest
            warnings.append('ai_narrative_verified_tokens_human_review_required')
        else:
            sections = generate_edited_sections(request, analyses, evidence, styles,section_settings)
            warnings.append('generation_mode_template_no_llm')
        result = ReportResult(request_id=request.request_id, report_id=report_id, version=(base_version or 0)+1, status='completed',
                              sections=sections,
                              sources=collect_sources(analyses, evidence,diagnostic_sources), download_path=None,
                              warnings=sorted(set(warnings)), is_synthetic=any(a.is_synthetic for a in analyses) or any(d['synthetic'] for d in diagnostics))
        from .actions import proposals
        result.proposals=proposals(analyses,request.language)
        verify_report(result, request, analyses, evidence, styles, narratives,section_settings)
        payload = {'result': result.model_dump(mode='json'), 'request': request.model_dump(mode='json'),
                   'policy': private_policy(access_context).model_dump(), 'analyses': [a.model_dump(mode='json') for a in analyses],
                   'evidence': [e.model_dump(mode='json') for e in evidence], 'styles': styles,
                   'narratives': narratives, 'section_settings': section_settings,
                   'generation_mode': 'ollama' if self.writer else 'template',
                   'section_versions': {s.section_id: result.version for s in result.sections},
                   'created_at': datetime.now(timezone.utc).isoformat()}
        payload['diagnostics']=diagnostics
        self.store.save_report(payload,base_version=base_version)
        self.store.audit(access_context.user_id, request.request_id, 'report.create', report_id)
        return result

    def recalculate_report(self, report_id, analysis_ids, base_version, access, title=None):
        """Hayat a déjà fait calculer les nouveaux résultats par Doha ; aucune arithmétique ici."""
        payload = self._authorized(report_id,access,edit=True,allow_stale=True)
        if payload['result']['version'] != base_version:
            raise AppError('version_conflict','Le rapport a changé avant son recalcul.',409)
        request = ReportRequest.model_validate(payload['request']).model_copy(update={
            'analysis_ids':analysis_ids,'request_id':uuid4().hex})
        if title is not None:
            request=request.model_copy(update={'title':title})
        return self.create_report(request,access,report_id=report_id,base_version=base_version,
                                  section_settings=payload.get('section_settings',{}))

    def _authorized(self, report_id, access, version=None, edit=False, allow_stale=False):
        require_module(access, edit)
        payload = self.store.report(report_id, version)
        if payload is None:
            raise forbidden()
        policy = ResourcePolicy.model_validate(payload['policy'])
        authorize(policy, access, edit)
        # Politique locale conservatrice : rapports privés à leur propriétaire.
        if policy.owner_id != access.user_id:
            raise forbidden()
        for identifier in payload['request'].get('diagnostic_ids',[]): self.provider.products.get(identifier,access)
        # Réévaluer les droits des analyses à chaque lecture, sans remplacer l'instantané historique.
        try:
            self._analyses(payload['request']['analysis_ids'], access)
        except AppError as exc:
            if not allow_stale or exc.code != 'stale_analysis' or not hasattr(self.provider,'authorize_snapshot'):
                raise
            for analysis_id in payload['request']['analysis_ids']:
                self.provider.authorize_snapshot(analysis_id,access)
        for raw in payload['evidence']:
            e = Evidence.model_validate(raw)
            old = self.store.document(e.passage.document_id, e.passage.version)
            current = self.store.document(e.passage.document_id)
            if old is None or current is None:
                raise forbidden()
            authorize(DocumentRecord.model_validate(old).policy, access)
            authorize(DocumentRecord.model_validate(current).policy, access)
        return payload

    def get_report(self, report_id, access_context, version=None):
        payload = self._authorized(report_id, access_context, version)
        result = ReportResult.model_validate(payload['result'])
        if self.store.pdf(report_id, result.version):
            result.download_path = f'/api/reports/{report_id}/pdf?version={result.version}'
        return result

    def list_reports(self, access_context):
        require_module(access_context)
        reports = []
        for report_id in self.store.report_ids():
            try:
                reports.append(self.get_report(report_id, access_context))
            except AppError as exc:
                if exc.code not in ['forbidden','stale_analysis']:
                    raise
        return reports

    def revise_report(self, request, access_context):
        payload = self._authorized(request.report_id, access_context, edit=True)
        old = ReportResult.model_validate(payload['result'])
        if request.base_version != old.version:
            raise AppError('version_conflict', 'La version de base est obsolète. Rechargez le rapport.', 409)
        if request.section_id not in {s.section_id for s in old.sections}:
            raise AppError('invalid_request', 'Section absente du rapport.', 422)
        operation = parse_revision(request.instruction)
        original_request = ReportRequest.model_validate(payload['request'])
        analyses = [AnalysisResult.model_validate(a) for a in payload['analyses']]
        evidence = [Evidence.model_validate(e) for e in payload['evidence']]
        styles = dict(payload['styles'])
        if operation.get('style') in ['concise', 'detailed']:
            styles[request.section_id] = operation['style']
        if not self.writer and operation.get('style') == 'rephrase':
            raise AppError('tool_failed', 'Reformulation libre indisponible en mode gabarits ; activez Ollama.', 503)
        section_settings = payload.get('section_settings', {})
        section_settings.setdefault(request.section_id, {}).update(operation)
        affected = {request.section_id}
        pending = [request.section_id]
        while pending:
            for dep in DEPENDENTS[pending.pop()]:
                if dep not in affected:
                    affected.add(dep)
                    pending.append(dep)
        result = old.model_copy(deep=True)
        result.version += 1
        result.request_id = request.request_id
        result.download_path = None
        from .actions import proposals
        result.proposals=proposals(analyses,original_request.language)
        if operation.get('language') in ['ar','ary']:
            result.warnings.append('Brouillon à relire — validation linguistique humaine arabe/darija non réalisée.')
        narratives = payload.get('narratives', {})
        if self.writer:
            sections = []
            for section in old.sections:
                if section.section_id in affected:
                    options = dict(section_settings.get(section.section_id, {}))
                    options.setdefault('style', styles.get(section.section_id, 'detailed'))
                    section, manifest = self.writer.generate_section(original_request, section.section_id, analyses, evidence, options)
                    narratives[section.section_id] = manifest
                sections.append(section)
            result.sections = sections
            result.warnings = [w for w in result.warnings if w not in ['generation_mode_template_no_llm', 'generation_mode_mixed']]
            if len(narratives) != len(result.sections):
                result.warnings.append('generation_mode_mixed')
            if 'ai_narrative_verified_tokens_human_review_required' not in result.warnings:
                result.warnings.append('ai_narrative_verified_tokens_human_review_required')
            payload['generation_mode'] = 'ollama' if len(narratives) == len(result.sections) else 'mixed'
        elif narratives:
            raise AppError('tool_failed', 'Ce rapport contient de la prose IA ; Ollama est requis pour le modifier.', 503)
        else:
            result.sections = generate_edited_sections(original_request, analyses, evidence, styles, section_settings)
        for section in result.sections:
            if section.section_id in affected:
                payload['section_versions'][section.section_id] = result.version
        verify_report(result, original_request, analyses, evidence, styles, narratives, section_settings)
        payload['result'] = result.model_dump(mode='json')
        payload['styles'] = styles
        payload['narratives'] = narratives
        payload['section_settings'] = section_settings
        self.store.save_report(payload, base_version=old.version)
        self.store.audit(access_context.user_id, request.request_id, 'report.revise', request.report_id)
        return result

    def export_pdf(self, report_id, access_context, exporter, version=None):
        payload = self._authorized(report_id, access_context, version)
        result = ReportResult.model_validate(payload['result'])
        if not self.store.pdf(report_id, result.version):
            pdf = exporter.render(payload)
            self.store.save_pdf(report_id, result.version, pdf)
        self.store.audit(access_context.user_id, result.request_id, 'report.export', report_id)
        return self.get_report(report_id, access_context, result.version)

    def download_pdf(self, report_id, access_context, version=None):
        result = self.get_report(report_id, access_context, version)
        pdf = self.store.pdf(report_id, result.version)
        if pdf is None:
            raise AppError('missing_data', 'PDF non généré. Lancez l’export.', 404)
        self.store.audit(access_context.user_id, result.request_id, 'report.download', report_id)
        return pdf

    def export_deck(self,report_id,access,version=None):
        payload=self._authorized(report_id,access,version)
        result=payload['result']
        with self.store.connect() as db:
            row=db.execute('SELECT deck FROM reports WHERE id=? AND version=?',(report_id,result['version'])).fetchone()
        if row and row[0]: return bytes(row[0])
        from .presentation import PresentationExporter
        content=PresentationExporter().render(payload)
        with self.store.connect() as db:
            db.execute('UPDATE reports SET deck=? WHERE id=? AND version=?',(content,report_id,result['version']))
        self.store.audit(access.user_id,result['request_id'],'report.presentation',report_id)
        return content
