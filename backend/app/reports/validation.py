from app.core.errors import AppError
from .generation import generate_edited_sections


def collect_sources(analyses, evidence,additional=()):
    sources = {}
    for source in [s for a in analyses for s in a.sources] + [e.source for e in evidence]+list(additional):
        if source.source_id in sources:
            old=sources[source.source_id]
            if any(getattr(old,k)!=getattr(source,k) for k in ['source_type','name','version']):
                raise AppError('missing_data', 'Référence ambiguë : un identifiant désigne plusieurs versions ou sources.', 422)
            source=source.model_copy(update={'fields':sorted(set(old.fields+source.fields)),'pages':sorted(set(old.pages+source.pages))})
        sources[source.source_id] = source
    return list(sources.values())


def verify_report(result, request, analyses, evidence, styles, narratives=None, section_settings=None):
    """La rédaction contrôlée est reconstruite depuis les valeurs typées pour bloquer toute altération."""
    expected = {s.section_id: s for s in generate_edited_sections(request, analyses, evidence, styles, section_settings)}
    from .actions import proposals
    if result.proposals and result.proposals!=proposals(analyses,request.language):
        raise AppError('tool_failed','Propositions différentes des règles et constats vérifiés.',500)
    if len(result.sections) != len(request.sections) or {s.section_id for s in result.sections} != set(request.sections):
        raise AppError('tool_failed', 'Liste des sections différente de la demande validée.', 500)
    from .narrative import verify_narrative
    for section in result.sections:
        if narratives and section.section_id in narratives:
            verify_narrative(result.model_copy(update={'sections': [section]}), request, analyses, evidence, narratives)
        elif section != expected[section.section_id]:
            raise AppError('tool_failed', 'Échec de vérification des valeurs, unités ou références.', 500)
    if any(a.is_synthetic for a in analyses) and not result.is_synthetic:
        raise AppError('tool_failed', 'Marquage synthétique perdu.', 500)
    ReportType = type(result)
    ReportType.model_validate(result.model_dump())
