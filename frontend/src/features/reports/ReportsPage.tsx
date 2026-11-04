import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from './api';
import type { AppConfig, EvidenceResult, Language, ReportResult, SectionId } from './types';

const sectionLabels: Record<SectionId, string> = {summary:'Résumé exécutif', diagnostic:'Diagnostic', comparison:'Comparaison', forecast:'Prévisions', recommendations:'Recommandations', limitations:'Limites'};

export function ReportsPage() {
  const [config, setConfig] = useState<AppConfig>();
  const [reports, setReports] = useState<ReportResult[]>([]);
  const [report, setReport] = useState<ReportResult>();
  const [title, setTitle] = useState('');
  const [ids, setIds] = useState('');
  const [language, setLanguage] = useState<Language>('fr');
  const [audience, setAudience] = useState<'direction'|'ministere'|'regional'>('direction');
  const [sections, setSections] = useState<SectionId[]>(['summary','diagnostic','comparison','forecast','recommendations','limitations']);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [editSection, setEditSection] = useState<SectionId>('summary');
  const [instruction, setInstruction] = useState('résumer');
  const [docFile, setDocFile] = useState<File>();
  const [docTitle, setDocTitle] = useState('');
  const [docId, setDocId] = useState('');
  const [docNotice, setDocNotice] = useState('');
  const [question, setQuestion] = useState('');
  const [evidence, setEvidence] = useState<EvidenceResult>();

  async function run(label: string, action: () => Promise<void>) {
    setBusy(label); setError('');
    try { await action(); }
    catch (e) { setError(e instanceof ApiError ? `${e.detail.message} (${e.detail.code} · ${e.detail.request_id})` : e instanceof Error ? e.message : 'Erreur inattendue.'); }
    finally { setBusy(''); }
  }
  function selectReport(value: ReportResult) {
    setReport(value); setEditSection(value.sections[0]?.section_id ?? 'summary');
    setReports(previous => {
      const latest = previous.find(r => r.report_id === value.report_id);
      return [latest && latest.version > value.version ? latest : value, ...previous.filter(r => r.report_id !== value.report_id)];
    });
  }
  useEffect(() => {
    let active = true;
    void Promise.all([api.config(), api.list()]).then(([cfg, list]) => {
      if (!active) return;
      setConfig(cfg); setReports(list);
      if (cfg.demo) { setIds('ana_demo_compare, ana_demo_forecast'); setTitle('Démonstration synthétique — Nuitées à Agadir'); }
    }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, []);

  function create(event: FormEvent) {
    event.preventDefault();
    void run('Récupération des analyses, rédaction et vérification…', async () => {
      const value = await api.create({ request_id: crypto.randomUUID(), title, analysis_ids: ids.split(',').map(v=>v.trim()).filter(Boolean), language, audience, sections });
      selectReport(value);
    });
  }

  return <div className="workspace">
    <aside className="sidebar"><a className="brand" href="/">ONMT<span>AI</span></a><p className="small">ESPACE DOCUMENTAIRE</p>
      <div className="nav-current">▤ &nbsp; Rapports intelligents</div><p className="sidebar-note">Des analyses aux décisions,<br/>avec des sources vérifiables.</p>
      <p className="small">RAPPORTS AUTORISÉS</p>
      {!reports.length && <p className="muted">Aucun rapport disponible.</p>}
      {reports.map(r=><button className="report-link" disabled={!!busy} key={r.report_id} onClick={()=>void run('Chargement du rapport…',async()=>selectReport(await api.read(r.report_id)))}>{r.report_id.slice(0,16)}… <span>v{r.version}</span></button>)}
    </aside>
    <main><header><span className="eyebrow">RECHERCHE & RAPPORTS</span><span className="pill">Espace Salma</span></header>
      <h1>Les données prennent<br/><em>la parole.</em></h1><p className="intro">Créez un rapport traçable à partir des analyses autorisées, enrichi par vos documents.</p>
      {config?.demo && <div className="demo">Démonstration explicite · utilisateur simulé · données synthétiques{config.demo_embeddings && ' · recherche lexicale de démonstration'}</div>}
      {error && <div role="alert" className="error">{error}</div>}
      {busy && <div role="status" className="progress"><span className="spinner"/>{busy} La requête reste ouverte pendant le traitement.</div>}
      <div className="columns"><form className="panel request-panel" onSubmit={create}><div className="panel-number">01 / COMPOSER</div><h2>Nouveau rapport</h2>
        <fieldset disabled={!!busy || !config}><label>Titre du rapport<input required maxLength={300} value={title} onChange={e=>setTitle(e.target.value)}/></label>
          <label>Identifiants des analyses<input required value={ids} onChange={e=>setIds(e.target.value)} placeholder="Séparés par des virgules"/></label>
          <div className="field-row"><label>Langue<select value={language} onChange={e=>setLanguage(e.target.value as Language)}><option value="fr">Français</option><option value="ar">العربية</option><option value="ary">الدارجة</option><option value="en">English</option><option value="es">Español</option></select></label>
            <label>Destinataire<select value={audience} onChange={e=>setAudience(e.target.value as typeof audience)}><option value="direction">Direction</option><option value="ministere">Ministère</option><option value="regional">Régional</option></select></label></div>
          <div className="label">Sections à inclure</div><div className="checks">{Object.entries(sectionLabels).map(([key,label])=><label key={key}><input type="checkbox" checked={sections.includes(key as SectionId)} onChange={e=>setSections(prev=>e.target.checked ? [...prev,key as SectionId] : prev.filter(s=>s!==key))}/>{label}</label>)}</div>
          <button className="primary" disabled={!sections.length} type="submit">Générer le rapport <span>↗</span></button>
        </fieldset>
      </form>
      <div className="panel preview"><div className="panel-number">02 / LIRE & AFFINER</div>
        {!report ? <div className="empty"><div className="paper-icon">▤</div><h2>Votre prochaine synthèse<br/>commence ici.</h2><p>Les sections, les références et les limites<br/>apparaîtront après la génération.</p></div> : <>
          <div className="report-heading"><h2>Rapport · version {report.version}</h2><span className="pill">{report.status}</span></div>
          {report.is_synthetic && <p className="demo">DONNÉES SYNTHÉTIQUES — démonstration</p>}
          {!!report.warnings.length && <details open><summary>Avertissements ({report.warnings.length})</summary><ul>{report.warnings.map(w=><li key={w}>{w}</li>)}</ul></details>}
          <div className="reading" dir="auto">{report.sections.map(s=><article key={s.section_id}><h3>{s.title}</h3><p className="content">{s.content}</p></article>)}</div>
          <details><summary>Sources utilisées ({report.sources.length})</summary>{report.sources.map(s=><p className="source" key={s.source_id}><strong>{s.name}</strong> · {s.source_type} · v{s.version}<br/>{s.source_id} · pages {s.pages.join(', ') || '—'} · champs {s.fields.join(', ') || '—'}</p>)}</details>
          <form className="edit-form" onSubmit={e=>{e.preventDefault(); void run('Modification et vérification des sections dépendantes…',async()=>selectReport(await api.revise({request_id:crypto.randomUUID(),report_id:report.report_id,base_version:report.version,section_id:editSection,instruction})));}}>
            <fieldset disabled={!!busy}><h3>Modifier une section</h3><label>Section<select value={editSection} onChange={e=>setEditSection(e.target.value as SectionId)}>{report.sections.map(s=><option key={s.section_id} value={s.section_id}>{s.title}</option>)}</select></label>
              <label>Modification<select value={instruction} onChange={e=>setInstruction(e.target.value)}><option value="résumer">Résumer</option><option value="détailler">Détailler</option></select></label><p className="muted">Un nouveau périmètre nécessite une nouvelle analyse.</p><button type="submit">Enregistrer une nouvelle version</button>
            </fieldset></form>
          <div className="actions"><button disabled={!!busy} onClick={()=>void run('Préparation du PDF…', async()=>selectReport(await api.export(report.report_id,report.version)))}>Préparer le PDF</button>
            {report.download_path && <button disabled={!!busy} onClick={()=>void run('Téléchargement…',()=>api.download(report.download_path!))}>Télécharger le PDF</button>}
            <label>Version<select aria-label="Version consultée" value={report.version} disabled={!!busy} onChange={e=>void run('Chargement de la version…',async()=>setReport(await api.read(report.report_id,Number(e.target.value))))}>{Array.from({length:reports.find(r=>r.report_id===report.report_id)?.version ?? report.version},(_,i)=><option key={i+1} value={i+1}>{i+1}</option>)}</select></label>
          </div>
        </>}
      </div></div>
      <section className="panel documents"><div className="panel-number">03 / DOCUMENTATION</div><h2>Enrichir le contexte</h2><p className="muted">PDF textuels autorisés uniquement · 20 Mio maximum · OCR non disponible.</p>
        <div className="columns"><form onSubmit={e=>{e.preventDefault(); if(docFile) void run('Extraction des pages et indexation locale…',async()=>{const value=await api.upload(docFile,docTitle,language,docId); setDocId(value.document.document_id); setDocNotice(`${value.duplicate?'Doublon déjà indexé':'Document indexé'} : ${value.document.document_id}, v${value.document.version}. ${value.document.warnings.join(' ')}`);});}}>
          <fieldset disabled={!!busy || !config}><label>Fichier PDF<input type="file" accept="application/pdf" required onChange={e=>setDocFile(e.target.files?.[0])}/></label><label>Titre du document<input required value={docTitle} onChange={e=>setDocTitle(e.target.value)}/></label><label>Identifiant à mettre à jour (facultatif)<input value={docId} onChange={e=>setDocId(e.target.value)}/></label><p className="muted">Langue du document : {language}. Les droits proviennent du contexte serveur.</p><button type="submit">Importer le PDF autorisé</button></fieldset>{docNotice && <p role="status">{docNotice}</p>}
        </form>
        <form onSubmit={e=>{e.preventDefault();void run('Recherche des passages autorisés…',async()=>setEvidence(await api.search(question)));}}><fieldset disabled={!!busy || !config}><label>Rechercher une preuve<input required value={question} onChange={e=>setQuestion(e.target.value)}/></label><button type="submit">Rechercher</button></fieldset>
          {evidence && <div>{!evidence.evidence.length && <p>Aucune preuve suffisante.</p>}{evidence.warnings.map(w=><p className="muted" key={w}>{w}</p>)}{evidence.evidence.map(e=><blockquote key={e.passage.chunk_id}><p>{e.passage.text}</p><cite>{e.source.name} · v{e.source.version} · p. {e.source.pages.join(', ')} · {e.passage.chunk_id}</cite></blockquote>)}</div>}
        </form></div>
      </section><footer>ONMT AI · Prototype de recherche documentaire et de reporting · Sources contrôlées côté serveur</footer>
    </main>
  </div>;
}
