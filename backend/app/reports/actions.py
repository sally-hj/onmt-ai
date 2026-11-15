"""Propositions contrôlées, rattachées à des résultats ; aucun effet causal revendiqué."""
LABELS={
 'fr':{'volume':'Examiner la qualité du périmètre puis les contributions des marchés et la durée de séjour avant de choisir une mesure de soutien.',
       'budget':'Examiner les engagements et le calendrier d’exécution avant de proposer une réaffectation des crédits.',
       'digital':'Comparer les conversions et les coûts sur le même périmètre avant toute décision de budget de campagne.',
       'review':'Proposition à valider ; responsable et échéance à fixer par l’utilisateur.'},
 'en':{'volume':'Review data scope, source markets and length of stay before choosing a support measure.',
       'budget':'Review commitments and execution timing before proposing a budget reallocation.',
       'digital':'Compare conversions and costs on the same scope before deciding campaign budgets.',
       'review':'Proposal for validation; the user must assign an owner and deadline.'},
 'es':{'volume':'Verificar el alcance, los mercados y la estancia antes de elegir una medida de apoyo.',
       'budget':'Revisar los compromisos y el calendario antes de proponer una reasignación.',
       'digital':'Comparar conversiones y costes con el mismo alcance antes de decidir el presupuesto.',
       'review':'Propuesta a validar; el usuario debe fijar responsable y plazo.'},
 'ar':{'volume':'مراجعة نطاق البيانات والأسواق ومدة الإقامة قبل اختيار إجراء للدعم.',
       'budget':'مراجعة الالتزامات وجدول التنفيذ قبل اقتراح إعادة تخصيص الميزانية.',
       'digital':'مقارنة التحويلات والتكاليف ضمن النطاق نفسه قبل قرار ميزانية الحملة.',
       'review':'اقتراح يحتاج إلى التحقق وتحديد المسؤول والأجل من طرف المستخدم.'}}
LABELS['ary']=LABELS['ar']


def proposals(analyses,language):
    output=[]
    for analysis in analyses:
        key='change_pct' if analysis.metric_id in ['arrivals','overnight_stays'] else 'current' if 'current' in analysis.values else 'value'
        value=analysis.values.get(key)
        if value is None: continue
        rule=None
        if analysis.metric_id in ['arrivals','overnight_stays'] and key=='change_pct' and value<0: rule=('volume',0,'territorial')
        elif analysis.metric_id=='budget_execution' and value<75: rule=('budget',75,'finance')
        elif analysis.metric_id=='click_rate' and value<3: rule=('digital',3,'performance')
        if rule:
            lever,threshold,role=rule
            output.append({'analysis_id':analysis.analysis_id,'lever':lever,'condition':f'{analysis.metric_id}.{key} < {threshold}',
                'observed_value':value,'unit':'%' if key=='change_pct' else analysis.unit,'proposal':LABELS[language][lever],
                'validation':LABELS[language]['review'],'suggested_role':role,'status':'proposed'})
    return output
