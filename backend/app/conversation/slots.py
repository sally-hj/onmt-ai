"""Ancrage des dates écrites explicitement : le petit LLM ne peut pas les remplacer."""
import calendar
import json
import re
import unicodedata

from app.core.config import ROOT

ALIASES = json.loads((ROOT/'config/dimension-aliases.json').read_text(encoding='utf-8'))


MONTHS = [
    'janvier january enero يناير','fevrier february febrero فبراير','mars march marzo مارس',
    'avril april abril abril ابريل أبريل','mai may mayo ماي مايو','juin june junio يونيو',
    'juillet july julio يوليوز يوليو','aout august agosto غشت اغسطس أغسطس',
    'septembre september septiembre شتنبر سبتمبر','octobre october octubre اكتوبر أكتوبر',
    'novembre november noviembre نونبر نوفمبر','decembre december diciembre دجنبر ديسمبر']


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c)).translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))


def explicit_periods(message):
    text = normalized(message)
    names = {normalized(name):index+1 for index,line in enumerate(MONTHS) for name in line.split()}
    pattern = r'(?<!\w)(?:و)?(?:ف|ب)?('+'|'.join(sorted(names,key=len,reverse=True))+r')\s+(20\d{2})(?!\d)'
    matches = [(names[m.group(1)],int(m.group(2))) for m in re.finditer(pattern,text)]
    # « février 2025 et 2024 » : même mois explicitement nommé.
    if len(matches)==1:
        shared = re.search(pattern+r'\s*(?:et|and|y|و)\s*(20\d{2})(?!\d)',text)
        if shared:
            matches.append((matches[0][0],int(shared.group(3))))
    return [{'start':f'{year}-{month:02}-01','end':f'{year}-{month:02}-{calendar.monthrange(year,month)[1]}'} for month,year in matches[:2]]


def ground_intent(intent,message,allowed=None):
    payload = intent.model_dump()
    text = normalized(message)
    if allowed is not None:
        multiple_group=None
        for dimension,key in [('destination','destinations'),('market','markets')]:
            aliases={name:list(terms) for name,terms in ALIASES[dimension].items()}
            for name in allowed.get(key,[]):
                aliases.setdefault(name,[name])
            # Un filtre n'est admis que s'il est effectivement écrit ou hérité du contexte.
            found=[name for name,terms in aliases.items() if any(re.search(r'(?<!\w)(?:و)?(?:ف|ب|ل)?'+re.escape(normalized(term))+r'(?!\w)',text) for term in terms)]
            if len(found)>1:
                if multiple_group is not None and multiple_group!=dimension:
                    payload.update(action='clarify',clarification='Précisez une seule dimension de comparaison à la fois.')
                else:
                    payload.update(action='benchmark',group_by=dimension,dimensions=found)
                    multiple_group=dimension
                payload[dimension]=None
            elif found:
                payload[dimension]=found[0]
            else:
                supplied=payload.get(dimension)
                other='market' if dimension=='destination' else 'destination'
                other_terms={normalized(term) for terms in ALIASES[other].values() for term in terms}
                payload[dimension]=None
                if supplied and normalized(supplied) not in other_terms and re.search(r'(?<!\w)'+re.escape(normalized(supplied))+r'(?!\w)',text):
                    # Une valeur de l'autre dimension (Marrakech comme marché) est un mauvais typage du modèle.
                    # Un périmètre réellement demandé mais inconnu nécessite une précision, pas un total implicite.
                    if supplied in allowed.get(key,[]):
                        payload[dimension]=supplied
                    else:
                        payload.update(action='clarify',clarification='Le périmètre demandé est inconnu du catalogue. Précisez une destination et un marché disponibles.')
        if multiple_group in [None,'market'] and re.search(r'par marche|by market|por mercado|حسب الاسواق|حسب السوق',text):
            payload.update(action='benchmark',group_by='market')
    # Canonicaliser une traduction explicitement demandée, pas une instruction inventée par le LLM.
    if intent.action == 'revise' and re.search(r'tradui|translat|traduc|ترجم',text):
        for language,terms in [('ary',['darija','دارجة']),('ar',['arabe','arabic','عربي','العربية']),
                               ('en',['anglais','english','ingles']),('es',['espagnol','spanish','espanol']),
                               ('fr',['francais','french','frances'])]:
            if any(term in text for term in terms):
                payload['instruction']='langue:'+language
                payload['language']=language
                break
    periods = explicit_periods(message)
    if not periods:
        return type(intent).model_validate(payload)
    if payload.get('action')=='benchmark' and len(periods)==1:
        payload.update(operation='value',comparison_period=None)
    if payload.get('operation')=='compare':
        payload['period'] = periods[0]
        if len(periods)>1:
            payload['comparison_period'] = periods[1]
    else:
        payload['period'] = {'start':periods[0]['start'],'end':periods[-1]['end']}
    # Revalider la structure après l'ancrage ; aucune date approximative ou calcul KPI.
    return type(intent).model_validate(payload)
