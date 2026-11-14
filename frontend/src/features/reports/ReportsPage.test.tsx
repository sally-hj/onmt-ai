import { act, fireEvent, render, screen, waitFor, cleanup } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ReportsPage } from './ReportsPage';
import { api, ApiError } from './api';
import type { ReportResult } from './types';

vi.mock('./api', async importOriginal => {
  const original = await importOriginal<typeof import('./api')>();
  return {...original, api:{config:vi.fn(),list:vi.fn(),create:vi.fn(),read:vi.fn(),revise:vi.fn(),export:vi.fn(),download:vi.fn(),upload:vi.fn(),search:vi.fn()}};
});
const report: ReportResult={request_id:'r1',report_id:'rpt_test',version:1,status:'completed',sections:[{section_id:'summary',title:'Résumé exécutif',content:'Observation : 80000 nuitees [s1]',source_ids:['s1']}],sources:[{source_id:'s1',source_type:'qvd',name:'DEMO.qvd',version:'v1',fields:['nuitees'],pages:[]}],warnings:['synthetic_data'],is_synthetic:true,download_path:null};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(api.config).mockResolvedValue({demo:true,demo_embeddings:true,generation:'synchronous',ollama_enabled:false});vi.mocked(api.list).mockResolvedValue([]);});
afterEach(cleanup);

describe('Rapports — tests interface avec API simulée',()=>{
  it('transmet une traduction ciblée et affiche le mode OCR et IA réels',async()=>{
    vi.mocked(api.config).mockResolvedValue({demo:true,demo_embeddings:false,generation:'synchronous',ollama_enabled:true,ocr_enabled:true,generation_mode:'ollama'});
    vi.mocked(api.create).mockResolvedValue(report);
    vi.mocked(api.revise).mockResolvedValue({...report,version:2});
    render(<ReportsPage/>);
    await waitFor(()=>expect(screen.getByRole('button',{name:/Générer le rapport/})).toBeEnabled());
    expect(screen.getByText(/Rédaction par un modèle IA local/)).toBeInTheDocument();
    expect(screen.getByText(/OCR local activé pour les pages scannées/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:/Générer le rapport/}));
    await screen.findByText('Rapport · version 1');
    fireEvent.change(screen.getByLabelText('Modification'),{target:{value:'langue:ar'}});
    fireEvent.click(screen.getByRole('button',{name:'Enregistrer une nouvelle version'}));
    await screen.findByText('Rapport · version 2');
    expect(vi.mocked(api.revise).mock.calls[0][0]).toMatchObject({instruction:'langue:ar',section_id:'summary',base_version:1});
  });
  it('affiche attente, rapport, marquage synthétique, révision et téléchargement',async()=>{
    let finish!: (value:ReportResult)=>void;
    vi.mocked(api.create).mockReturnValue(new Promise(resolve=>{finish=resolve;}));
    vi.mocked(api.revise).mockResolvedValue({...report,version:2});
    vi.mocked(api.export).mockResolvedValue({...report,version:2,download_path:'/api/reports/rpt_test/pdf?version=2'});
    vi.mocked(api.download).mockResolvedValue(undefined);
    render(<ReportsPage/>);
    await waitFor(()=>expect(screen.getByLabelText('Identifiants des analyses')).toHaveValue('ana_demo_compare, ana_demo_forecast'));
    fireEvent.click(screen.getByRole('button',{name:/Générer le rapport/}));
    expect(await screen.findByRole('status')).toHaveTextContent('Récupération des analyses');
    expect(screen.getByRole('button',{name:/Générer le rapport/})).toBeDisabled();
    await act(async()=>finish(report));
    expect(await screen.findByText('Rapport · version 1')).toBeInTheDocument();
    expect(screen.getByText('DONNÉES SYNTHÉTIQUES — démonstration')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Enregistrer une nouvelle version'}));
    await screen.findByText('Rapport · version 2');
    expect(vi.mocked(api.revise).mock.calls[0][0].base_version).toBe(1);
    fireEvent.click(screen.getByRole('button',{name:'Préparer le PDF'}));
    fireEvent.click(await screen.findByRole('button',{name:'Télécharger le PDF'}));
    await waitFor(()=>expect(api.download).toHaveBeenCalledWith('/api/reports/rpt_test/pdf?version=2'));
  });
  it('présente les refus et les erreurs de version sans masquer le rapport',async()=>{
    vi.mocked(api.create).mockRejectedValue(new ApiError({request_id:'r',code:'forbidden',message:'Accès refusé.'}));
    render(<ReportsPage/>);
    await waitFor(()=>expect(screen.getByRole('button',{name:/Générer le rapport/})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:/Générer le rapport/}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Accès refusé.');
    vi.mocked(api.create).mockResolvedValue(report);
    fireEvent.click(screen.getByRole('button',{name:/Générer le rapport/}));
    await screen.findByText('Rapport · version 1');
    vi.mocked(api.revise).mockRejectedValue(new ApiError({request_id:'r',code:'version_conflict',message:'Rechargez le rapport.'}));
    fireEvent.click(screen.getByRole('button',{name:'Enregistrer une nouvelle version'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('version_conflict');
    expect(screen.getByText('Rapport · version 1')).toBeInTheDocument();
  });
  it('affiche les preuves absentes et bloque sans authentification',async()=>{
    vi.mocked(api.search).mockResolvedValue({evidence:[],warnings:['documentary_evidence_absent']});
    render(<ReportsPage/>);
    await waitFor(()=>expect(screen.getByRole('button',{name:'Rechercher'})).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Rechercher une preuve'),{target:{value:'absent'}});
    fireEvent.click(screen.getByRole('button',{name:'Rechercher'}));
    expect(await screen.findByText('Aucune preuve suffisante.')).toBeInTheDocument();
    cleanup();
    vi.mocked(api.config).mockRejectedValue(new Error('Authentification serveur non connectée.'));
    render(<ReportsPage/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Authentification');
    expect(screen.getByRole('button',{name:/Générer le rapport/})).toBeDisabled();
  });
});
