"""Vraie erreur réseau : à lancer seulement après arrêt volontaire de son service Ollama."""
import json
import os

import httpx
import pytest

from app.core.config import ROOT


@pytest.mark.full_models
def test_real_ollama_unavailable_does_not_create_report():
    if os.getenv('ONMT_EXPECT_OLLAMA_OFFLINE')!='1':
        pytest.skip('Arrêter Ollama puis définir ONMT_EXPECT_OLLAMA_OFFLINE=1 ; API complète requise.')
    with httpx.Client(base_url='http://127.0.0.1:8000',trust_env=False,timeout=30) as client:
        assert client.post('/api/auth/login',json={'username':'direction','password':'OnmtLocal!2026'}).status_code==200
        before=client.get('/api/reports').json()
        response=client.post('/api/conversations/messages',json={'message':'Compare les nuitées à Agadir en février 2025 et février 2024.'})
        assert response.status_code==503,response.text
        assert response.json()['code']=='tool_failed'
        assert 'Ollama' in response.json()['message']
        assert client.get('/api/reports').json()==before
        output=ROOT/'local_data/cps-completion-results/ollama-offline.json'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({'status':response.status_code,'error':response.json(),'reports_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
