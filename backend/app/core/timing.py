"""Durées d'étapes réellement exécutées, sans pourcentage ni contenu utilisateur."""
from contextvars import ContextVar
from functools import wraps
from time import perf_counter

trace = ContextVar('onmt_trace',default=None)
stage_callback = ContextVar('onmt_stage',default=None)


def measured(stage):
    def decorate(function):
        @wraps(function)
        def run(*args,**kwargs):
            callback=stage_callback.get()
            if callback: callback(stage)
            started=perf_counter(); outcome='failed'
            try:
                result=function(*args,**kwargs); outcome='completed'; return result
            finally:
                target=trace.get()
                if target is not None: target.append({'stage':stage,'seconds':round(perf_counter()-started,6),'status':outcome})
        return run
    return decorate
