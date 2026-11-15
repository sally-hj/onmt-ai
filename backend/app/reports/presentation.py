"""Présentation PDF de 25 pages : contenus sélectionnés, constats et manques explicites."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.errors import AppError
from app.core.timing import measured
from .generation import TEXT

TITLES={
 'fr':['Présentation stratégique','Question de décision','Périmètre et période','Qualité des données','Synthèse exécutive','Indicateurs sélectionnés','Historique mensuel','Observations et prévisions','Comparaison temporelle','Référence historique','Variations calculées','Marchés émetteurs','Lecture territoriale','Saisonnalité','Budget prévu','Exécution budgétaire','Performance marketing','Positionnement concurrentiel','Valeur–Volume','Aide au diagnostic Butler','Prévisions et incertitude','Scénarios et hypothèses','Propositions à valider','Preuves documentaires','Sources et limites'],
 'en':['Strategic presentation','Decision question','Scope and period','Data quality','Executive summary','Selected indicators','Monthly history','Observations and forecasts','Time comparison','Historical baseline','Calculated changes','Source markets','Territorial view','Seasonality','Planned budget','Budget execution','Marketing performance','Competitive position','Value–Volume','Butler diagnostic aid','Forecast and uncertainty','Scenarios and assumptions','Proposals for validation','Documentary evidence','Sources and limitations'],
 'es':['Presentación estratégica','Decisión','Alcance y período','Calidad de datos','Resumen ejecutivo','Indicadores seleccionados','Historia mensual','Observaciones y previsiones','Comparación temporal','Referencia histórica','Cambios calculados','Mercados emisores','Vista territorial','Estacionalidad','Presupuesto','Ejecución presupuestaria','Rendimiento de campañas','Posición competitiva','Valor–Volumen','Ayuda al diagnóstico Butler','Previsiones e incertidumbre','Escenarios e hipótesis','Propuestas a validar','Evidencia documental','Fuentes y límites'],
 'ar':['العرض الاستراتيجي','سؤال القرار','النطاق والفترة','جودة البيانات','الملخص التنفيذي','المؤشرات المختارة','السجل الشهري','الملاحظات والتوقعات','المقارنة الزمنية','المرجع التاريخي','التغيرات المحسوبة','الأسواق المصدرة','القراءة الترابية','الموسمية','الميزانية المقررة','تنفيذ الميزانية','أداء الحملات','الموقع التنافسي','القيمة والحجم','مساعدة تشخيص دورة الحياة','التوقعات وعدم اليقين','السيناريوهات والفرضيات','اقتراحات للتحقق','الأدلة الوثائقية','المصادر والحدود']}
TITLES['ary']=TITLES['ar']
MISSING={'fr':'Élément non fourni par les analyses sélectionnées. Aucune valeur ajoutée artificiellement.',
 'en':'Not supplied by the selected analyses. No invented result.', 'es':'No disponible en los análisis seleccionados. Sin resultados inventados.',
 'ar':'هذا العنصر غير متوفر في التحليلات المختارة. لم تتم إضافة نتائج مصطنعة.','ary':'هاد العنصر ما متوفرش فالتحاليل المختارة. ما زدنا حتى نتيجة مخترعة.'}


def build_slides(payload):
    language=payload['request']['language']; missing=MISSING[language]
    analyses=payload['analyses']; sections={s['section_id']:s for s in payload['result']['sections']}
    def section(key): return sections.get(key,{}).get('content',missing)
    slides=[{'title':title,'lines':[],'plots':[],'missing':False} for title in TITLES[language]]
    def lines(index,items):
        slides[index]['lines']=items or [missing]; slides[index]['missing']=not bool(items)
    lines(0,[payload['request']['title'],f"{payload['result']['report_id']} · v{payload['result']['version']}",TEXT[language]['audiences'][payload['request']['audience']]])
    lines(1,[payload['request']['title'],TEXT[language]['limit']])
    lines(2,[f"{a['metric_id']} · {a['period']['start']} / {a['period']['end']} · {a['filters']}" for a in analyses])
    lines(3,[f"{a['metric_id']} : {a['status']}" for a in analyses]+[TEXT[language]['synthetic']] if payload['result']['is_synthetic'] else [f"{a['metric_id']} : {a['status']}" for a in analyses])
    lines(4,[section('summary')])
    lines(5,[f"{a['metric_id']} : {a['values']} {a['unit']}" for a in analyses])
    def plots(index,selected,kind=None):
        for a in selected[:1]:
            points=[p for p in a['series'] if p['value'] is not None and (kind is None or p['kind']==kind)]
            if not points: continue
            low=min(0,min(p['value'] for p in points)); high=max(p['value'] for p in points); span=high-low or 1
            slides[index]['plots'].append({'metric':a['metric_id'],'unit':a['unit'],'source':', '.join(s['name'] for s in a['sources']),
                'points':[{'x':45+i*1000/max(1,len(points)-1),'y':235-(p['value']-low)/span*190,**p} for i,p in enumerate(points)]})
        if not slides[index]['plots']: lines(index,[])
    plots(6,analyses,'observed'); plots(7,analyses)
    lines(8,[section('comparison')])
    lines(9,[f"{a['metric_id']} : {a['values']['previous']} {a['unit']} · {a.get('comparison_period')}" for a in analyses if 'previous' in a['values']])
    lines(10,[f"{a['metric_id']} : {a['values']['change_pct']} %" for a in analyses if 'change_pct' in a['values']])
    lines(11,[f"{a['filters'].get('market')} : {a['metric_id']} {a['values']} {a['unit']}" for a in analyses if a['filters'].get('market')])
    lines(12,[f"{a['filters'].get('destination')} : {a['metric_id']} {a['values']} {a['unit']}" for a in analyses if a['filters'].get('destination')])
    lines(13,[section('diagnostic')]); plots(14,[a for a in analyses if a['metric_id']=='budget'])
    lines(15,[f"{a['metric_id']} : {a['values']} {a['unit']}" for a in analyses if a['metric_id'] in ['budget_execution','spent','committed','budget_remaining']])
    lines(16,[f"{a['metric_id']} : {a['values']} {a['unit']}" for a in analyses if a['metric_id'] in ['campaign_roi','click_rate','campaign_conversion','spend_per_night','cost_per_click']])
    # Un rapport ne possédant pas ces diagnostics ne prétend pas les avoir calculés.
    for i in [17,18,19]: lines(i,[])
    for diagnostic in payload.get('diagnostics',[]):
        kind=diagnostic['kind']
        if kind=='scenario':
            lines(21,[diagnostic['formula'],f"{diagnostic['baseline']} → {diagnostic['scenario_value']} {diagnostic['unit']} ; hypothèse {diagnostic['shock_pct']} %",diagnostic['warning']]); continue
        if kind=='butler':
            lines(19,[diagnostic['stage'],diagnostic['rule'],diagnostic['limit']]); continue
        index={'international':17,'bcg_regions':17,'value_volume':18,'map':12}.get(kind)
        if index is None: continue
        if kind in ['international','bcg_regions']:
            raw=[{'label':r['destination'],'a':r['relative_share'],'b':r['market_growth_pct']} for r in diagnostic['rows']]
            label=diagnostic['bcg']['x']+' ; '+diagnostic['bcg']['y']
        else:
            raw=[{'label':r.get('destination',r.get('market')),'a':r.get('longitude',r.get('volume')),'b':r.get('latitude',r.get('value'))} for r in diagnostic['points']]
            label=diagnostic.get('formula',diagnostic.get('warning',''))
        raw=[r for r in raw if r['a'] is not None and r['b'] is not None]
        if not raw: continue
        xmin=min(r['a'] for r in raw); xmax=max(r['a'] for r in raw); ymin=min(r['b'] for r in raw); ymax=max(r['b'] for r in raw)
        matrix=[{**r,'x':70+(r['a']-xmin)/(xmax-xmin or 1)*850,'y':220-(r['b']-ymin)/(ymax-ymin or 1)*170} for r in raw]
        slides[index].update(matrix=matrix,lines=[label,diagnostic.get('warning',diagnostic.get('interpretation',''))],missing=False)
    lines(20,[section('forecast')]); plots(20,[a for a in analyses if any(p['kind']=='forecast' for p in a['series'])],'forecast')
    if not slides[21]['lines']: lines(21,[TEXT[language]['hypothesis'],TEXT[language]['limit']])
    lines(22,[section('recommendations')]+[p['proposal']+' '+p['validation'] for p in payload['result'].get('proposals',[])])
    lines(23,[f"{e['source']['name']} · v{e['source']['version']} · p.{e['source']['pages']} : {e['passage']['text']}" for e in payload.get('evidence',[])])
    lines(24,[f"{s['name']} · v{s['version'][:16]} · {', '.join(s['fields'])}" for s in payload['result']['sources']]+[section('limitations')])
    # Pas de masquage de texte : le deck abrège explicitement et le rapport conserve l'intégralité.
    for slide in slides:
        slide['abridged']=len(slide['lines'])>8 or any(len(t)>700 for t in slide['lines'])
        slide['lines']=[t if len(t)<=700 else t[:650]+' […]' for t in slide['lines'][:8]]
        budget=450 if slide['plots'] else 2200
        if sum(map(len,slide['lines']))>budget:
            slide['abridged']=True
            per_line=max(80,budget//max(1,len(slide['lines'])))
            slide['lines']=[t[:per_line]+' […]' if len(t)>per_line else t for t in slide['lines']]
    return slides


class PresentationExporter:
    @measured('export_presentation')
    def render(self,payload):
        from playwright.sync_api import sync_playwright
        language=payload['request']['language']
        env=Environment(loader=FileSystemLoader(Path(__file__).parent/'templates'),autoescape=select_autoescape(['html']))
        markup=env.get_template('presentation.html').render(slides=build_slides(payload),payload=payload,
            rtl=language in ['ar','ary'],language=language,t=TEXT[language])
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                try:
                    context=browser.new_context(java_script_enabled=False,service_workers='block')
                    context.route('**/*',lambda route:route.abort()); page=context.new_page()
                    page.set_content(markup,wait_until='load')
                    overflow=page.evaluate("Array.from(document.querySelectorAll('.slide')).map((e,i)=>({page:i+1,bad:e.scrollHeight>e.clientHeight+2||e.scrollWidth>e.clientWidth+2})).filter(e=>e.bad)")
                    if overflow: raise AppError('tool_failed','Présentation trop dense ; réduire les analyses ou le texte avant export.',422)
                    return page.pdf(width='320mm',height='180mm',print_background=True,margin={k:'0' for k in ['top','bottom','left','right']})
                finally: browser.close()
        except AppError: raise
        except Exception as exc: raise AppError('tool_failed','Présentation PDF indisponible ; vérifier Chromium local.',503) from exc
