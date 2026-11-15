"""Note paginée en quinze parties distinctes ; aucun calcul de KPI dans l'export."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.errors import AppError
from .generation import TEXT

TITLE={
 'fr':['Note stratégique','Périmètre et traçabilité','Résumé exécutif','Diagnostic historique','Séries observées','Comparaisons temporelles','Destinations et marchés','Lecture budgétaire','Performance des campagnes','Prévisions','Incertitude et valeurs projetées','Scénarios et conditions','Actions proposées','Documentation et citations','Méthodes, sources et limites'],
 'en':['Strategic note','Scope and traceability','Executive summary','Historical diagnosis','Observed series','Time comparisons','Destinations and markets','Budget review','Campaign performance','Forecast','Uncertainty and projections','Scenarios and conditions','Proposed actions','Documents and citations','Methods, sources and limits'],
 'es':['Nota estratégica','Alcance y trazabilidad','Resumen ejecutivo','Diagnóstico histórico','Series observadas','Comparaciones temporales','Destinos y mercados','Presupuesto','Campañas','Previsiones','Incertidumbre','Escenarios','Acciones propuestas','Documentos y citas','Métodos y límites'],
 'ar':['مذكرة استراتيجية','النطاق والتتبع','الملخص التنفيذي','التشخيص التاريخي','السلاسل المرصودة','المقارنات الزمنية','الوجهات والأسواق','الميزانية','أداء الحملات','التوقعات','عدم اليقين والقيم المتوقعة','السيناريوهات والشروط','الإجراءات المقترحة','الوثائق والاستشهادات','المنهجية والمصادر والحدود']}
TITLE['ary']=TITLE['ar']


def note_pages(payload):
    request=payload['request']; lang=request['language']; t=TEXT[lang]; analyses=payload['analyses']
    sections={s['section_id']:s['content'] for s in payload['result']['sections']}
    pages=[{'title':title,'paragraphs':[],'rows':[],'plots':[]} for title in TITLE[lang]]
    def section(index,key): pages[index]['paragraphs']=[sections.get(key,t['missing'])]
    pages[0]['paragraphs']=[request['title'],t['audiences'][request['audience']],payload['created_at']]
    pages[1]['paragraphs']=[f"{a['metric_id']} : {a['period']} ; {a['filters']} ; {a['status']}" for a in analyses]
    section(2,'summary'); section(3,'diagnostic'); section(5,'comparison'); section(9,'forecast'); section(12,'recommendations')
    pages[12]['paragraphs'] += [f"{p['analysis_id']} ; {p['condition']} ; {p['proposal']} {p['validation']}" for p in payload['result'].get('proposals',[])][:3]
    pages[6]['paragraphs']=[f"{a['metric_id']} ; {a['filters']} ; {a['values']} {a['unit']}" for a in analyses]
    for a in analyses:
        snapshot=f"{a['metric_id']} : {a['values']} {a['unit']} ; {a['period']} ; {a['filters']}"
        if any(s['source_id']=='finance' for s in a['sources']): pages[7]['paragraphs'].append(snapshot)
        if any(s['source_id'] in ['performance','extension'] for s in a['sources']): pages[8]['paragraphs'].append(snapshot)
        projected=[p for p in a['series'] if p['kind']=='forecast']
        for p in projected[:12]: pages[10]['rows'].append([a['metric_id'],p['date'],p['value'],p['lower'],p['upper'],a['unit']])
        if len(projected)>12: pages[10]['paragraphs'].append(f"{a['analysis_id']} · {t['forecast']} : 12 / {len(projected)} ; {t['sources']} : /api/analyses/{a['analysis_id']}")
        observed=[p for p in a['series'] if p['kind']=='observed' and p['value'] is not None]
        if observed and len(pages[4]['plots'])<2:
            values=[p['value'] for p in observed]; low=min(0,min(values)); span=max(values)-low or 1
            pages[4]['plots'].append({'metric':a['metric_id'],'unit':a['unit'],
                'points':[{'x':30+i*580/max(1,len(observed)-1),'y':150-(p['value']-low)/span*120,**p} for i,p in enumerate(observed)]})
    pages[11]['paragraphs']=[t['hypothesis'],t['limit'],t['missing']]
    for diagnostic in payload.get('diagnostics',[]):
        if diagnostic['kind']=='scenario':
            pages[11]['paragraphs']=[diagnostic['formula'],f"{diagnostic['baseline']} → {diagnostic['scenario_value']} {diagnostic['unit']} ; {diagnostic['shock_pct']} %",diagnostic['warning']]
    pages[13]['paragraphs']=[f"{e['source']['name']} v{e['source']['version']} p.{e['source']['pages']} : {e['passage']['text']}" for e in payload.get('evidence',[])][:8]
    pages[14]['paragraphs']=[f"{s['name']} · v{s['version']} · {s['fields']}" for s in payload['result']['sources']]+[sections.get('limitations',t['missing'])]
    for page in pages:
        if not page['paragraphs'] and not page['rows'] and not page['plots']: page['paragraphs']=[t['missing']]
    return pages


def render_strategic(payload):
    from playwright.sync_api import sync_playwright
    lang=payload['request']['language']
    env=Environment(loader=FileSystemLoader(Path(__file__).parent/'templates'),autoescape=select_autoescape(['html']))
    markup=env.get_template('strategic.html').render(pages=note_pages(payload),payload=payload,t=TEXT[lang],rtl=lang in ['ar','ary'])
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                context=browser.new_context(java_script_enabled=False,service_workers='block');context.route('**/*',lambda route:route.abort())
                page=context.new_page();page.set_content(markup,wait_until='load')
                overflow=page.evaluate("Array.from(document.querySelectorAll('.sheet')).some(e=>e.scrollHeight>e.clientHeight+2||e.scrollWidth>e.clientWidth+2)")
                if overflow: raise AppError('tool_failed','Note trop dense pour quinze pages ; résumer les sections ou réduire les analyses. Aucun texte masqué.',422)
                return page.pdf(format='A4',print_background=True,margin={k:'0' for k in ['top','bottom','left','right']})
            finally: browser.close()
    except AppError: raise
    except Exception as exc: raise AppError('tool_failed','Export de la note indisponible ; vérifier Chromium.',503) from exc
