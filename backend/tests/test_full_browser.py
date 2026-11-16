"""Vrai navigateur et API déjà démarrée : comptes locaux, calcul QVD, navigation et alertes."""
import os
import json
import re

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

from app.core.config import ROOT


@pytest.mark.browser
def test_full_workspace_browser():
    if os.getenv('ONMT_TEST_FULL_BROWSER')!='1':
        pytest.skip('ONMT_TEST_FULL_BROWSER=1 : lancer scripts/start-full-app.ps1 et npm run dev.')
    api = os.getenv('ONMT_FULL_API_URL','http://127.0.0.1:8000')
    ui = os.getenv('ONMT_FULL_UI_URL','http://127.0.0.1:5173')
    # Un véritable calcul QVD pour tester l'affichage sans demander une interprétation IA ici.
    with httpx.Client(base_url=api,trust_env=False,timeout=60) as client:
        assert client.post('/api/auth/login',json={'username':'direction','password':'OnmtLocal!2026'}).status_code==200
        response = client.post('/api/analyses',json={'request_id':'browser-reference','operation':'compare','metric_id':'overnight_stays',
            'period':{'start':'2025-02-01','end':'2025-02-28'},'comparison_period':{'start':'2024-02-01','end':'2024-02-29'},
            'filters':{'destination':'Agadir'},'language':'fr'})
        assert response.status_code==201,response.text
    output = ROOT/'local_data/cps-completion-results/browser-regression';output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={'width':1440,'height':1100},reduced_motion='reduce')
            failures=[]
            page.on('pageerror',lambda error:failures.append(str(error)))
            page.goto(ui)
            expect(page.get_by_label('Identifiant')).to_be_visible()
            page.screenshot(path=str(output/'01-connexion.png'),full_page=True)
            page.get_by_label('Identifiant').fill('direction')
            page.get_by_label('Mot de passe').fill('OnmtLocal!2026')
            page.get_by_role('button',name='Accéder à mon espace').click()
            expect(page.get_by_role('heading',name='Que souhaitez-vous comprendre aujourd’hui ?')).to_be_visible(timeout=30000)
            # Échantillon de contrastes des textes secondaires sur leur surface effective.
            def luminance(rgb):
                values=[float(x)/255 for x in re.findall(r'[\d.]+',rgb)[:3]]
                linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
                return sum(v*w for v,w in zip(linear,[.2126,.7152,.0722]))
            contrasts=[]
            for selector in ['.w-nav-caption','.w-page-title .w-overline','.w-welcome>p','.w-suggestions button small','.w-chat-note']:
                colors=page.locator(selector).first.evaluate('''element => {
                    let current=element, background='rgb(255,255,255)';
                    while(current){const c=getComputedStyle(current).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent'){background=c;break;}current=current.parentElement;}
                    return {foreground:getComputedStyle(element).color,background};
                }''')
                light,dark=sorted([luminance(colors['foreground']),luminance(colors['background'])],reverse=True)
                ratio=(light+.05)/(dark+.05)
                contrasts.append({'selector':selector,**colors,'ratio':round(ratio,2)})
                assert ratio>=4.5,(selector,colors,ratio)
            (output/'contrastes.json').write_text(json.dumps(contrasts,indent=2),encoding='utf-8')
            page.screenshot(path=str(output/'02-conversation.png'),full_page=True)
            page.get_by_role('button',name='Comparer deux périodes',exact=False).click()
            expect(page.get_by_label('Votre question')).to_have_value('Compare les nuitées à Agadir en février 2025 et février 2024.')
            page.get_by_role('navigation').get_by_role('button',name='Analyses',exact=True).click()
            expect(page.locator('.w-analysis').first).to_contain_text('80')
            expect(page.locator('.w-analysis').first.locator('svg')).to_have_attribute('aria-label',__import__('re').compile('Nuitées touristiques'))
            page.locator('.w-analysis').first.get_by_text('Sources, filtres et formule').click()
            expect(page.locator('.w-analysis').first).to_contain_text('commercial.qvd')
            page.screenshot(path=str(output/'03-analyses.png'),full_page=True)
            page.get_by_role('navigation').get_by_role('button',name='Diagnostics & cartes',exact=True).click()
            page.get_by_role('button',name='Calculer',exact=True).click()
            expect(page.locator('.w-table-scroll table tbody tr')).to_have_count(6,timeout=30000)
            page.get_by_label('Indicateur du benchmark').select_option('occupancy')
            expect(page.get_by_role('columnheader',name='occupancy (%)',exact=True)).to_be_visible()
            page.screenshot(path=str(output/'07-benchmark.png'),full_page=True)
            page.get_by_label('Outil',exact=True).select_option('bcg_regions')
            page.get_by_role('button',name='Calculer',exact=True).click()
            expect(page.locator('.w-table-scroll table tbody tr')).to_have_count(12,timeout=30000)
            page.get_by_label('Outil',exact=True).select_option('map')
            page.get_by_label('Destination interne',exact=True).select_option('Agadir')
            page.get_by_role('button',name='Calculer',exact=True).click()
            expect(page.get_by_role('img',name='Carte ponctuelle, sans frontières administratives')).to_be_visible()
            expect(page.locator('.w-diagnostic-chart circle')).to_have_count(1)
            expect(page.locator('.w-diagnostic-chart circle title')).to_contain_text('80')
            page.locator('.w-diagnostic-chart circle').focus()
            expect(page.locator('.w-diagnostic-chart circle')).to_be_focused()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            page.screenshot(path=str(output/'08-carte-mobile.png'),full_page=True)
            page.set_viewport_size({'width':1440,'height':1100})
            page.get_by_role('navigation').get_by_role('button',name='Sources & services').click()
            expect(page.get_by_role('heading',name='commercial.qvd',exact=True)).to_be_visible()
            page.get_by_role('button',name='Actualiser et vérifier').click()
            expect(page.get_by_role('button',name='Actualiser et vérifier')).to_be_enabled(timeout=30000)
            page.screenshot(path=str(output/'04-sources.png'),full_page=True)
            page.get_by_role('navigation').get_by_role('button',name='Alertes',exact=False).click()
            expect(page.locator('.w-alert-card').filter(has_text='Agadir').first).to_contain_text('-20 %')
            page.screenshot(path=str(output/'05-alertes.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.get_by_label('Ouvrir la navigation').click()
            page.get_by_role('navigation').get_by_role('button',name='Conversation',exact=True).click()
            expect(page.get_by_label('Votre question')).to_have_value('Compare les nuitées à Agadir en février 2025 et février 2024.')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            page.screenshot(path=str(output/'06-mobile.png'),full_page=True)
            page.get_by_label('Votre question').focus();page.keyboard.press('Tab')
            expect(page.get_by_role('button',name='Envoyer la question')).to_be_focused()
            assert failures==[]
        finally:
            browser.close()
