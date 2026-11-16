"""Évaluation d'intentions avec Qwen réel ; aucun client simulé dans ce programme."""
import argparse
import json
import platform
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from app.core.config import ROOT
from app.conversation.intent import IntentParser
from app.core.llm_client import OllamaPlanner
from app.analytics.metrics import METRICS


def evaluate(limit=0,tasks=None,output_name='languages-real.json'):
    data=json.loads((ROOT/'examples/evaluation/multilingual-heldout.json').read_text(encoding='utf-8'))
    parser=IntentParser(OllamaPlanner('onmt-qwen25:3b',context=4096))
    output=ROOT/'local_data/cps-completion-results'/output_name
    output.parent.mkdir(parents=True,exist_ok=True)
    result={'at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'working_tree':subprocess.check_output(['git','status','--porcelain'],text=True).strip(),
        'python':platform.python_version(),'platform':platform.platform(),'model':'onmt-qwen25:3b','context':4096,
        'mode':'real_ollama_hybrid_parser','human_evaluation':False,'results':[]}
    counts=defaultdict(int)
    for case in data['cases']:
        if tasks and case['task'] not in tasks: continue
        language=case['language']
        if limit and counts[language]>=limit: continue
        counts[language]+=1; started=time.perf_counter()
        row={k:case[k] for k in ['id','language','task','message','expected']}
        try:
            intent=parser.parse(case['message'],case['context'],{'metrics':[{'id':m.id,'label':m.label} for m in METRICS.values()],
                'destinations':['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'],'markets':['France','Espagne','Allemagne','Royaume-Uni','Maroc']},language)
            actual=intent.model_dump(mode='json'); row['actual']=actual
            def lookup(key):
                value=actual
                for part in key.split('.'):
                    if not isinstance(value,dict): return None
                    value=value.get(part)
                return value
            row['passed']=all(lookup(k)==v for k,v in case['expected'].items())
            row['inference']=getattr(parser.client,'last_metrics',{})
        except Exception as exc: row.update(passed=False,error=str(exc))
        row['seconds']=round(time.perf_counter()-started,3); result['results'].append(row)
        result['summary']={}
        for item in result['results']:
            key=item['language']+':'+item['task']; summary=result['summary'].setdefault(key,{'passed':0,'failed':0})
            summary['passed' if item['passed'] else 'failed']+=1
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(case['id'],row['passed'],row['seconds'],flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--limit-per-language',type=int,default=0)
    parser.add_argument('--tasks',nargs='+',choices=['analysis','followup','ambiguity','revision','diagnostic'])
    parser.add_argument('--output-name',choices=['languages-real.json','languages-real-corrected-followups.json'],default='languages-real.json')
    args=parser.parse_args()
    evaluate(args.limit_per_language,args.tasks,args.output_name)
