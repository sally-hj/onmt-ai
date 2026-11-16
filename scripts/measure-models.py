"""Trois mesures réelles E5/Qwen ; arrêter les autres clients d'inférence avant exécution."""
import json
import platform
import subprocess
import time
from datetime import datetime,timezone

import httpx

from app.core.config import ROOT,Settings
from app.core.state import AppState
from app.analytics.service import AnalyticsService
from app.data_access.catalog import Catalog
from app.conversation.intent import IntentParser
from app.core.llm_client import OllamaPlanner
from app.reports.retrieval import LocalSentenceEmbedder
from app.schemas.common import AccessContext


def measure():
    output=ROOT/'local_data/cps-completion-results/performance-models-real.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    result={'at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
        'python':platform.python_version(),'model':'onmt-qwen25:3b','context':4096,'repetitions':3,
        'note':'Premier chargement du modèle mesuré, cache disque Windows non vidé. Question identique de performance, pas une évaluation linguistique aveugle.',
        'e5':[],'qwen':[]}
    def save():output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    settings=Settings()
    embedder=LocalSentenceEmbedder(settings.embedding_model,settings.embedding_revision)
    for i in range(3):
        started=time.perf_counter();vector=embedder.encode(['Difference entre arrivees touristiques et nuitees'],query=True)
        assert len(vector)==1 and len(vector[0])==384
        result['e5'].append({'cache':'model_load' if i==0 else 'warm','seconds':time.perf_counter()-started,'dimensions':len(vector[0])});save()
    access=AccessContext(user_id='model-measure',roles=['report_editor'],allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'])
    analytics=AnalyticsService(Catalog(ROOT/'config/sources.extended.json',ROOT/'local_data/qvd-synthetic'),AppState(output.parent/'model-measure-state'))
    described=analytics.catalog.describe(access)
    catalog={'metrics':[{k:m[k] for k in ['id','label']} for m in analytics.metrics(access)],
        'destinations':access.allowed_territories,
        'markets':sorted({m for s in described['sources'] for m in s.get('markets',[])}),
        'fields':{s['id']:s.get('units',{}) for s in described['sources']}}
    # Décharge explicite du modèle sélectionné ; ne stoppe pas le service.
    with httpx.Client(timeout=60,trust_env=False) as client:
        response=client.post('http://127.0.0.1:11434/api/generate',json={'model':result['model'],'keep_alive':0})
        response.raise_for_status()
    llm=OllamaPlanner(result['model']); parser=IntentParser(llm)
    try:
        for i in range(3):
            started=time.perf_counter()
            intent=parser.parse('Compare les nuitées à Agadir en février 2025 et février 2024.',{},catalog,'fr')
            elapsed=time.perf_counter()-started
            valid=(intent.action=='analyse' and intent.metric_id=='overnight_stays' and intent.destination=='Agadir'
                   and str(intent.period.start)=='2025-02-01' and str(intent.comparison_period.start)=='2024-02-01')
            result['qwen'].append({'cache':'model_load' if i==0 else 'warm','seconds':elapsed,'correct':valid,'inference_metrics':llm.last_metrics});save()
            assert valid,'Intention incorrecte : consulter la mesure, aucun remplacement simulé.'
        result['status']='passed'
    except Exception as exc:
        result.update(status='failed',error=str(exc));raise
    finally:save()
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':measure()
