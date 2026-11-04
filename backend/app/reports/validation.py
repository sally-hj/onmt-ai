from app.core.errors import AppError
from .generation import generate_sections


def collect_sources(analyses, evidence):
    sources = {}
    for source in [s for a in analyses for s in a.sources] + [e.source for e in evidence]:
        if source.source_id in sources and sources[source.source_id] != source:
            raise AppError('missing_data', 'Référence ambiguë : un identifiant désigne plusieurs versions ou sources.', 422)
        sources[source.source_id] = source
    return list(sources.values())


def verify_report(result, request, analyses, evidence, styles):
    """La rédaction contrôlée est reconstruite depuis les valeurs typées pour bloquer toute altération."""
    expected = generate_sections(request, analyses, evidence, styles)
    if result.sections != expected:
        raise AppError('tool_failed', 'Échec de vérification des valeurs, unités ou références.', 500)
    if any(a.is_synthetic for a in analyses) and not result.is_synthetic:
        raise AppError('tool_failed', 'Marquage synthétique perdu.', 500)
    ReportType = type(result)
    ReportType.model_validate(result.model_dump())
