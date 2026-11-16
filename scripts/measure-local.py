"""Mesures répétées des outils QVD ; pas d'inférence simulée ni de revendication SLA."""
import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime,timezone

from app.core.config import ROOT
from app.core.state import AppState
from app.data_access.catalog import Catalog
from app.analytics.service import AnalyticsService
from app.analytics.diagnostics import Diagnostics
from app.schemas.common import AccessContext,Period
from app.schemas.analysis import AnalysisRequest


def measure(repetitions=3):
    output=ROOT/'local_data/cps-completion-results/performance-native.json';output.parent.mkdir(parents=True,exist_ok=True)
    cpu=platform.processor()
    if os.name=='nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu=winreg.QueryValueEx(key,'ProcessorNameString')[0]
    result={'at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
        'cpu':cpu,'logical_cpus':os.cpu_count(),'python':platform.python_version(),'platform':platform.platform(),
        'disk_free_gib':round(shutil.disk_usage(ROOT).free/1024**3,2),
        'versions':{n:importlib.metadata.version(n) for n in ['pyqvd','langgraph','torch','transformers','sentence-transformers','chromadb','playwright']},
        'dataset_rows':{'commercial':2100,'finance':2100,'performance':2100,'extension':2100,'international':420,'regional':840,'competitiveness':2100},
        'inference':'Non mesurée par ce programme. Voir les essais réels et leurs durées par étape.','runs':[]}
    access=AccessContext(user_id='performance-audit',roles=['report_editor'],allowed_modules=['reports','commercial','finance','performance'],allowed_territories=['Agadir','Marrakech','Fès','Tanger','Rabat','Casablanca'])
    analytics=AnalyticsService(Catalog(ROOT/'config/sources.extended.json',ROOT/'local_data/qvd-synthetic'),AppState(output.parent/'performance-state'))
    for i in range(repetitions):
        run={'cache':'cold_decode' if i==0 else 'warm_decode','iteration':i+1}
        started=time.perf_counter(); catalog=analytics.catalog.describe(access);run['discovery_seconds']=time.perf_counter()-started
        assert all(not s['quality_errors'] for s in catalog['sources'])
        request=AnalysisRequest(request_id='profile',metric_id='spend_per_night',operation='compare',period={'start':'2025-02-01','end':'2025-02-28'},comparison_period={'start':'2024-02-01','end':'2024-02-29'},filters={'destination':'Agadir'},language='fr')
        started=time.perf_counter();analytics.run(request,access);run['cross_module_calculation_seconds']=time.perf_counter()-started
        started=time.perf_counter();diagnostic=Diagnostics(analytics).international(request.period,request.comparison_period,access);run['international_6_by_13_seconds']=time.perf_counter()-started
        assert len(diagnostic['rows'])==6 and len(diagnostic['units'])==13
        result['runs'].append(run)
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repetitions',type=int,choices=range(1,11),default=3)
    measure(parser.parse_args().repetitions)
