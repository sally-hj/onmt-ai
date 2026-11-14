"""Petite évaluation réelle d'intentions ; aucune mesure ne vaut une recette linguistique."""
import argparse
import json
import time
from pathlib import Path

from app.conversation.intent import IntentParser
from app.core.config import ROOT
from app.core.llm_client import OllamaPlanner

QUESTIONS={
 'fr':'Compare les nuitées à Agadir en février 2025 et février 2024.',
 'en':'Compare overnight stays in Agadir in February 2025 and February 2024.',
 'es':'Compara las pernoctaciones en Agadir en febrero 2025 y febrero 2024.',
 'ar':'قارن الليالي السياحية في أكادير في فبراير ٢٠٢٥ و فبراير ٢٠٢٤.',
 'ary':'قارن ليا الليالي السياحية فأكادير ففبراير 2025 وففبراير 2024.'}


def evaluate(languages):
    parser=IntentParser(OllamaPlanner('onmt-qwen25:3b'))
    output=ROOT/'local_data/full-app-results/languages.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    for language in languages:
        started=time.monotonic()
        row={'language':language,'question':QUESTIONS[language],'synthetic':True}
        try:
            intent=parser.parse(QUESTIONS[language],{},
                {'metrics':[{'id':'overnight_stays','label':'Nuitées touristiques'},{'id':'arrivals','label':'Arrivées'}],
                 'destinations':['Agadir','Marrakech'],'markets':['France','Espagne']},language)
            row['intent']=intent.model_dump(mode='json')
            row['exact_reference_match']=(intent.action=='analyse' and intent.operation=='compare' and intent.metric_id=='overnight_stays'
                and intent.destination=='Agadir' and intent.period is not None and str(intent.period.start)=='2025-02-01'
                and intent.comparison_period is not None and str(intent.comparison_period.end)=='2024-02-29'
                and intent.market is None and intent.language==language)
        except Exception as exc:
            row.update(exact_reference_match=False,error=str(exc))
        row['seconds']=round(time.monotonic()-started,2)
        results.append(row)
        output.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(language,':',row['exact_reference_match'],';',row['seconds'],'s',flush=True)
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages',nargs='+',choices=list(QUESTIONS),default=list(QUESTIONS))
    evaluate(parser.parse_args().languages)
