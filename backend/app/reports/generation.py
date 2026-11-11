import json

from app.core.errors import AppError
from app.schemas.report import ReportSection

# Les chiffres et citations sont ajoutés par le serveur. Le modèle ne rédige aucune assertion libre.
TEXT = {
    'fr': {
        'titles': ['Résumé exécutif', 'Diagnostic', 'Comparaison', 'Prévisions', 'Recommandations', 'Limites'],
        'audiences': {'direction': 'Direction : points de décision et vigilance.', 'ministere': 'Ministère : synthèse institutionnelle et traçabilité.', 'regional': 'Responsables régionaux : constats du territoire et suivi opérationnel.'},
        'observed': 'Observation', 'forecast': 'Prévision', 'missing': 'Données insuffisantes pour cette section.',
        'unavailable': 'indisponible', 'hypothesis': 'Hypothèse : aucune hypothèse chiffrée ajoutée.',
        'action': 'Action proposée : vérifier le périmètre et la qualité avec l’équipe métier avant toute décision. Constat associé',
        'limit': 'Les documents apportent du contexte, sans démontrer de causalité. Les calculs ne sont pas reproduits dans ce module.',
        'quote': 'Extrait documentaire cité comme donnée de contexte', 'formula': 'Formule du calcul', 'scope': 'Filtres appliqués',
        'none': 'Aucune preuve documentaire suffisante.', 'synthetic': 'DÉMONSTRATION — DONNÉES SYNTHÉTIQUES',
        'columns': ['Analyse / indicateur', 'Date / nature', 'Valeur', 'Unité'], 'sources': 'Sources',
    },
    'en': {
        'titles': ['Executive summary', 'Diagnosis', 'Comparison', 'Forecast', 'Recommendations', 'Limitations'],
        'audiences': {'direction': 'Management: decisions and risks.', 'ministere': 'Ministry: institutional summary and traceability.', 'regional': 'Regional teams: territorial observations and operational follow-up.'},
        'observed': 'Observation', 'forecast': 'Forecast', 'missing': 'Insufficient data for this section.',
        'unavailable': 'unavailable', 'hypothesis': 'Assumption: no numerical assumptions added.',
        'action': 'Proposed action: verify scope and quality with the business team before deciding. Related evidence',
        'limit': 'Documents provide context without establishing causality. This module does not reproduce KPI calculations.',
        'quote': 'Document excerpt quoted as contextual data', 'formula': 'Calculation formula', 'scope': 'Applied filters',
        'none': 'No sufficient documentary evidence.', 'synthetic': 'DEMONSTRATION — SYNTHETIC DATA',
        'columns': ['Analysis / metric', 'Date / kind', 'Value', 'Unit'], 'sources': 'Sources',
    },
    'es': {
        'titles': ['Resumen ejecutivo', 'Diagnóstico', 'Comparación', 'Previsiones', 'Recomendaciones', 'Limitaciones'],
        'audiences': {'direction': 'Dirección: decisiones y riesgos.', 'ministere': 'Ministerio: síntesis institucional y trazabilidad.', 'regional': 'Equipos regionales: observaciones territoriales y seguimiento operativo.'},
        'observed': 'Observación', 'forecast': 'Previsión', 'missing': 'Datos insuficientes para esta sección.',
        'unavailable': 'no disponible', 'hypothesis': 'Hipótesis: no se añaden hipótesis numéricas.',
        'action': 'Acción propuesta: verificar el alcance y la calidad con el equipo antes de decidir. Evidencia asociada',
        'limit': 'Los documentos aportan contexto sin demostrar causalidad. Este módulo no reproduce cálculos de KPI.',
        'quote': 'Extracto documental citado como contexto', 'formula': 'Fórmula del cálculo', 'scope': 'Filtros aplicados',
        'none': 'Sin evidencia documental suficiente.', 'synthetic': 'DEMOSTRACIÓN — DATOS SINTÉTICOS',
        'columns': ['Análisis / indicador', 'Fecha / tipo', 'Valor', 'Unidad'], 'sources': 'Fuentes',
    },
    'ar': {
        'titles': ['الملخص التنفيذي', 'التشخيص', 'المقارنة', 'التوقعات', 'التوصيات', 'الحدود'],
        'audiences': {'direction': 'للإدارة: القرارات ونقاط اليقظة.', 'ministere': 'للوزارة: ملخص مؤسساتي ومصادر قابلة للتتبع.', 'regional': 'للمسؤولين الجهويين: المعطيات الترابية والمتابعة العملية.'},
        'observed': 'ملاحظة', 'forecast': 'توقع', 'missing': 'المعطيات غير كافية لهذا القسم.',
        'unavailable': 'غير متوفر', 'hypothesis': 'فرضية: لم تتم إضافة فرضيات رقمية.',
        'action': 'إجراء مقترح: التحقق من النطاق والجودة مع فريق العمل قبل اتخاذ القرار. الدليل المرتبط',
        'limit': 'الوثائق توفر السياق ولا تثبت السببية. لا تعاد حسابات المؤشرات في هذه الوحدة.',
        'quote': 'مقتطف وثائقي للسياق', 'formula': 'صيغة الحساب', 'scope': 'الفلاتر المطبقة',
        'none': 'لا توجد أدلة وثائقية كافية.', 'synthetic': 'عرض تجريبي — بيانات اصطناعية',
        'columns': ['التحليل / المؤشر', 'التاريخ / النوع', 'القيمة', 'الوحدة'], 'sources': 'المصادر',
    },
    'ary': {
        'titles': ['الخلاصة', 'التشخيص', 'المقارنة', 'التوقعات', 'الاقتراحات', 'الحدود'],
        'audiences': {'direction': 'للإدارة: القرارات والنقط اللي خاصها الانتباه.', 'ministere': 'للوزارة: خلاصة مؤسساتية مع المصادر.', 'regional': 'للمسؤولين فالجهات: المعطيات المحلية والتتبع.'},
        'observed': 'ملاحظة', 'forecast': 'توقع', 'missing': 'المعطيات ما كافياش لهاد القسم.',
        'unavailable': 'ما متوفرش', 'hypothesis': 'فرضية: ما زدنا حتى فرضية بالأرقام.',
        'action': 'اقتراح: تأكدو من النطاق والجودة مع الفريق قبل القرار. الدليل المرتبط',
        'limit': 'الوثائق كتعطي السياق وما كتثبتش السبب. هاد الوحدة ما كتعاودش حساب المؤشرات.',
        'quote': 'مقتطف من الوثيقة للسياق', 'formula': 'صيغة الحساب', 'scope': 'الفلاتر المطبقة',
        'none': 'ما كايناش أدلة وثائقية كافية.', 'synthetic': 'عرض تجريبي — معطيات اصطناعية',
        'columns': ['التحليل / المؤشر', 'التاريخ / النوع', 'القيمة', 'الوحدة'], 'sources': 'المصادر',
    },
}
SECTION_IDS = ['summary', 'diagnostic', 'comparison', 'forecast', 'recommendations', 'limitations']


def number(value, unavailable):
    # Aucune conversion, agrégation ou arrondi métier.
    return unavailable if value is None else str(value)


def facts(analyses):
    rows = []
    for a in analyses:
        if a.status == 'unavailable' or not a.sources:
            continue
        source_ids = [s.source_id for s in a.sources]
        for key,value in a.values.items():
            rows.append({'analysis_id': a.analysis_id, 'metric_id': a.metric_id, 'key': key, 'value': value,
                         'unit': '%' if key == 'change_pct' else a.unit, 'kind': 'observed',
                         'date': (f'{a.comparison_period.start}/{a.comparison_period.end}'
                                  if key == 'previous' and a.comparison_period else f'{a.period.start}/{a.period.end}'),
                         'source_ids': source_ids, 'filters': a.filters})
        for point in a.series:
            for key in ['value', 'lower', 'upper']:
                # Les bornes nulles sont absentes du graphique mais restent dans l'instantané original.
                if key != 'value' and getattr(point, key) is None:
                    continue
                rows.append({'analysis_id': a.analysis_id, 'metric_id': a.metric_id, 'key': key,
                             'value': getattr(point, key), 'unit': a.unit, 'kind': point.kind,
                             'date': str(point.date), 'source_ids': source_ids, 'filters': a.filters})
    return rows


def render_fact(row, t):
    label = t['forecast'] if row['kind'] == 'forecast' else t['observed']
    value = number(row['value'], t['unavailable'])
    filters = json.dumps(row['filters'], ensure_ascii=False, sort_keys=True)
    return (f"{label} — {row['metric_id']} / {row['key']} / {row['date']} : {value} {row['unit']} "
            f"[{', '.join(row['source_ids'])}] · {t['scope']} : {filters}")


def revision_style(instruction):
    normalized = instruction.casefold().strip()
    if normalized in ['résumer', 'résume', 'plus concis', 'simplifier', 'concise']:
        return 'concise'
    if normalized in ['détailler', 'détaille', 'plus détaillé', 'detailed']:
        return 'detailed'
    raise AppError('invalid_request', 'Modifications disponibles : « résumer » ou « détailler ». Un nouveau périmètre ou calcul nécessite une nouvelle analyse de Doha.', 422)


def generate_sections(request, analyses, evidence, styles=None):
    t = TEXT[request.language]
    all_rows = facts(analyses)
    sections = []
    for section_id in request.sections:
        style = (styles or {}).get(section_id, 'detailed')
        if section_id == 'comparison':
            rows = [r for r in all_rows if r['key'] in ['current', 'previous', 'change_pct']]
        elif section_id == 'forecast':
            rows = [r for r in all_rows if r['kind'] == 'forecast']
        else:
            rows = [r for r in all_rows if r['kind'] == 'observed']
        if style == 'concise':
            rows = rows[:3]
        parts = [t['audiences'][request.audience]]
        if section_id == 'limitations':
            parts += [t['limit'], t['hypothesis']]
            parts += [f'{a.analysis_id}: {w}' for a in analyses for w in a.warnings]
            cited = []
        elif section_id == 'recommendations':
            rows = [r for r in rows if r['value'] is not None]
            parts += [f"{t['action']} : {render_fact(r,t)}. {t['limit']}" for r in rows[:2]] or [t['missing']]
            cited = sorted({sid for r in rows[:2] for sid in r['source_ids']})
        else:
            parts += [render_fact(r,t) for r in rows] or [t['missing']]
            cited = sorted({sid for r in rows for sid in r['source_ids']})
        if section_id == 'forecast':
            parts.append(t['hypothesis'])
        if section_id in ['summary', 'diagnostic']:
            for e in evidence:
                # Citation brute explicitement séparée des constats ; aucune instruction n'est exécutée.
                parts.append(f"{t['quote']} [{e.source.source_id}] :\n« {e.passage.text} »")
                cited.append(e.source.source_id)
            if not evidence:
                parts.append(t['none'])
        if style == 'detailed' and section_id in ['diagnostic', 'comparison', 'forecast']:
            parts += [f"{t['formula']} ({a.analysis_id}) : {a.formula}" for a in analyses if a.sources]
        sections.append(ReportSection(section_id=section_id, title=t['titles'][SECTION_IDS.index(section_id)],
                                      content='\n\n'.join(parts), source_ids=sorted(set(cited))))
    return sections


def generate_edited_sections(request, analyses, evidence, styles=None, section_settings=None):
    result = []
    for section_id in request.sections:
        options = (section_settings or {}).get(section_id, {})
        target = request.model_copy(update={'sections': [section_id],
                                           'language': options.get('language', request.language),
                                           'audience': options.get('audience', request.audience)})
        result.extend(generate_sections(target, analyses, evidence, styles))
    return result
