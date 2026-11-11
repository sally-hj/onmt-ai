"""Vrais serveurs locaux et Chromium. Analyses et embeddings explicitement synthétiques."""
import io
import os
import shutil
import socket
import subprocess
import sys
import time

import httpx
import pdfplumber
import pytest
from playwright.sync_api import expect, sync_playwright

from app.core.config import ROOT
from conftest import text_pdf


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


@pytest.fixture
def live_servers(tmp_path):
    if os.getenv('ONMT_TEST_BROWSER') != '1':
        pytest.skip('ONMT_TEST_BROWSER=1 requis pour lancer les vrais serveurs et Chromium.')
    frontend = ROOT / 'frontend'
    if not (frontend/'node_modules/vite/bin/vite.js').is_file():
        pytest.fail('Exécutez npm ci dans frontend avant le test navigateur.')
    api_port, ui_port = free_port(), free_port()
    env = {**os.environ, 'PYTHONPATH':str(ROOT/'backend'), 'ONMT_DEMO':'1', 'ONMT_DEMO_EMBEDDINGS':'1',
           'ONMT_DATA_DIR':str(tmp_path/'state'), 'ONMT_OLLAMA_MODEL':'', 'ONMT_GENERATION_MODE':'template', 'ONMT_OCR':'0',
           'ONMT_API_TARGET':f'http://127.0.0.1:{api_port}'}
    processes=[]
    with (tmp_path/'servers.log').open('w',encoding='utf-8') as log:
        try:
            for command, cwd in [([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(api_port)],ROOT),
                                 ([shutil.which('node'),str(frontend/'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port',str(ui_port),'--strictPort'],frontend)]:
                processes.append(subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=log,
                                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
            deadline=time.monotonic()+40
            urls=[f'http://127.0.0.1:{api_port}/api/reports/config',f'http://127.0.0.1:{ui_port}']
            while time.monotonic()<deadline:
                if any(p.poll() is not None for p in processes):
                    pytest.fail((tmp_path/'servers.log').read_text(encoding='utf-8'))
                try:
                    if all(httpx.get(u,timeout=1,trust_env=False).status_code==200 for u in urls):
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.2)
            else:
                pytest.fail('Serveurs indisponibles : '+(tmp_path/'servers.log').read_text(encoding='utf-8'))
            yield urls[1]
        finally:
            for process in processes:
                process.terminate()
            for process in processes:
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


@pytest.mark.browser
def test_real_ui_api_report_revision_document_and_pdf(live_servers):
    artifact=ROOT/'local_data'/'test-artifacts';artifact.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
            failures=[]
            page.on('pageerror',lambda error:failures.append(str(error)))
            page.goto(live_servers)
            expect(page.get_by_text('Démonstration explicite',exact=False)).to_be_visible()
            page.get_by_role('button',name='Générer le rapport').click()
            expect(page.get_by_text('Rapport · version 1')).to_be_visible(timeout=30000)
            expect(page.get_by_text('DONNÉES SYNTHÉTIQUES — démonstration')).to_be_visible()
            expect(page.locator('.reading')).to_contain_text('80000 nuitees')
            page.get_by_role('button',name='Enregistrer une nouvelle version').click()
            expect(page.get_by_text('Rapport · version 2')).to_be_visible()
            page.get_by_role('button',name='Préparer le PDF').click()
            expect(page.get_by_role('button',name='Télécharger le PDF')).to_be_visible(timeout=30000)
            with page.expect_download() as info:
                page.get_by_role('button',name='Télécharger le PDF').click()
            download=info.value
            download.save_as(artifact/'rapport-demo.pdf')
            with pdfplumber.open(download.path()) as pdf:
                assert '80000' in '\n'.join(page.extract_text() or '' for page in pdf.pages)
            page.get_by_label('Fichier PDF').set_input_files({'name':'demo.pdf','mimeType':'application/pdf',
                                                             'buffer':text_pdf(['Nuitees Agadir definition synthetique.'])})
            page.get_by_label('Titre du document').fill('Definition synthetique')
            page.get_by_role('button',name='Importer le PDF autorisé').click()
            expect(page.get_by_text('Document indexé',exact=False)).to_be_visible(timeout=30000)
            page.get_by_label('Rechercher une preuve').fill('Nuitees Agadir definition synthetique.')
            page.get_by_role('button',name='Rechercher',exact=True).click()
            expect(page.locator('blockquote')).to_contain_text('Nuitees Agadir definition synthetique.')
            page.get_by_label('Version consultée').select_option('1')
            expect(page.get_by_text('Rapport · version 1')).to_be_visible()
            page.get_by_role('button',name='Enregistrer une nouvelle version').click()
            expect(page.get_by_role('alert')).to_contain_text('version_conflict')
            page.screenshot(path=str(artifact/'rapport-interface.png'),full_page=True)
            assert failures==[]
        finally:
            browser.close()
