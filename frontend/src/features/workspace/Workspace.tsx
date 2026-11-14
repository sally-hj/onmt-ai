import { useEffect, useRef, useState, type FormEvent } from 'react';
import type {
  AccessContext,
  AnalysisResult,
  Language,
  ReportResult,
} from '../reports/types';
import { api } from '../reports/api';
import { AnalysisCard, metricNames } from './AnalysisCard';
import { DocumentsPanel } from './DocumentsPanel';
import { ReportPanel } from './ReportPanel';
import {
  workspaceApi,
  type Alert,
  type Catalog,
  type Message,
  type Status,
} from './api';
import './workspace.css';

type View =
  | 'conversation'
  | 'analyses'
  | 'reports'
  | 'documents'
  | 'alerts'
  | 'sources';
const navigation: { id: View; label: string; icon: string }[] = [
  { id: 'conversation', label: 'Conversation', icon: 'chat' },
  { id: 'analyses', label: 'Analyses', icon: 'chart' },
  { id: 'reports', label: 'Rapports', icon: 'report' },
  { id: 'documents', label: 'Documents', icon: 'folder' },
  { id: 'alerts', label: 'Alertes', icon: 'bell' },
  { id: 'sources', label: 'Sources & services', icon: 'database' },
];
const paths: Record<string, string> = {
  chat: 'M4 4h16v12H9l-5 4V4Zm4 4h8M8 12h5',
  chart: 'M4 20V4m0 16h16M8 16v-4m5 4V7m5 9V4',
  report: 'M6 3h9l4 4v14H6V3Zm8 0v5h5M9 12h7m-7 4h7',
  folder: 'M3 6h7l2 3h9v11H3V6Z',
  bell: 'M6 16V9a6 6 0 0 1 12 0v7l2 2H4l2-2Zm4 5h4',
  database:
    'M4 6c0-4 16-4 16 0s-16 4-16 0Zm0 0v12c0 4 16 4 16 0V6M4 12c0 4 16 4 16 0',
  arrow: 'M5 12h14m-5-5 5 5-5 5',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z',
  plus: 'M12 5v14M5 12h14',
  logout: 'M9 4H4v16h5m5-13 5 5-5 5m-6-5h11',
};
function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.spark} />
    </svg>
  );
}

const suggestions = [
  {
    label: 'Comparer deux périodes',
    description: 'Les nuitées à Agadir, février 2025 / 2024',
    question: 'Compare les nuitées à Agadir en février 2025 et février 2024.',
  },
  {
    label: 'Explorer la saisonnalité',
    description: 'Un historique mensuel sur cinq années',
    question: 'Montre les nuitées à Agadir de janvier 2021 à décembre 2025.',
  },
  {
    label: 'Prévoir les prochains mois',
    description: 'Une référence évaluée sur l’historique',
    question:
      'Prévois les nuitées à Agadir pour les 6 prochains mois avec un historique de janvier 2021 à décembre 2025.',
  },
];

function Login({ onLogin }: { onLogin: () => Promise<void> }) {
  const [username, setUsername] = useState('direction'),
    [password, setPassword] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await workspaceApi.login(username, password);
      await onLogin();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Connexion impossible.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="w-login">
      <section className="w-login-art">
        <div className="w-brand">
          onmt<span>intelligence</span>
          <i />
        </div>
        <div>
          <span className="w-overline">OBSERVER. COMPRENDRE. DÉCIDER.</span>
          <h1>
            Un nouveau regard
            <br />
            sur le tourisme
            <br />
            <em>marocain.</em>
          </h1>
          <p>
            Les données, les analyses et vos documents réunis dans une
            conversation.
          </p>
        </div>
        <p className="w-login-footer">
          ONMT AI · Projet académique · Développement local
        </p>
        <div className="w-arch" aria-hidden="true" />
      </section>
      <main className="w-login-form">
        <span className="w-overline">VOTRE ESPACE DE DÉCISION</span>
        <h2>Bienvenue.</h2>
        <p className="w-muted">
          Connectez-vous à votre compte local pour retrouver vos analyses et
          rapports autorisés.
        </p>
        {error && (
          <p role="alert" className="w-error">
            {error}
          </p>
        )}
        <form onSubmit={submit}>
          <fieldset disabled={busy}>
            <label>
              Identifiant
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>
            <label>
              Mot de passe
              <input
                autoComplete="current-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <button className="w-primary" type="submit">
              {busy ? 'Connexion…' : 'Accéder à mon espace'}
              <Icon name="arrow" />
            </button>
          </fieldset>
        </form>
        <p className="w-login-note">
          Les comptes de démonstration et les instructions de connexion sont
          documentés dans le guide de démarrage.
        </p>
      </main>
    </div>
  );
}

export function Workspace() {
  const [user, setUser] = useState<AccessContext>(),
    [checking, setChecking] = useState(true),
    [view, setView] = useState<View>('conversation');
  const [catalog, setCatalog] = useState<Catalog>(),
    [status, setStatus] = useState<Status>(),
    [alerts, setAlerts] = useState<Alert[]>([]),
    [analyses, setAnalyses] = useState<AnalysisResult[]>([]),
    [reports, setReports] = useState<ReportResult[]>([]);
  const [messages, setMessages] = useState<Message[]>([]),
    [draft, setDraft] = useState(''),
    [cid, setCid] = useState<string>(),
    [version, setVersion] = useState(0),
    [language, setLanguage] = useState<Language>('fr');
  const [busy, setBusy] = useState(''),
    [error, setError] = useState(''),
    [selectedReport, setSelectedReport] = useState<ReportResult>(),
    [menu, setMenu] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null),
    bottom = useRef<HTMLDivElement>(null);
  const latest = analyses[0];

  async function load() {
    const identity = await workspaceApi.me();
    setUser(identity);
    const results = await Promise.allSettled([
      workspaceApi.catalog(),
      workspaceApi.status(),
      workspaceApi.analyses(),
      api.list(),
      workspaceApi.alerts(),
    ]);
    if (results[0].status === 'fulfilled') setCatalog(results[0].value);
    if (results[1].status === 'fulfilled') setStatus(results[1].value);
    if (results[2].status === 'fulfilled') setAnalyses(results[2].value);
    if (results[3].status === 'fulfilled') setReports(results[3].value);
    if (results[4].status === 'fulfilled') setAlerts(results[4].value);
    const failures = results.filter((r) => r.status === 'rejected');
    if (failures.length)
      setError(
        'Certaines ressources sont indisponibles. Consultez Sources & services ou réessayez.',
      );
    const previous = localStorage.getItem('onmt-chat:' + identity.user_id);
    if (previous) {
      try {
        const saved = await workspaceApi.conversation(previous);
        setCid(saved.conversation_id);
        setVersion(saved.version);
        setMessages(saved.messages);
      } catch {
        localStorage.removeItem('onmt-chat:' + identity.user_id);
        setError(
          'La dernière conversation ne peut plus être restaurée. Vérifiez les sources et vos droits, puis démarrez une nouvelle conversation.',
        );
      }
    }
  }
  useEffect(() => {
    void load()
      .catch(() => setUser(undefined))
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    bottom.current?.scrollIntoView?.({ behavior: 'auto', block: 'nearest' });
  }, [messages, busy]);

  async function send(value = draft) {
    if (!value.trim() || busy) return;
    setBusy('Interprétation de la demande et exécution des outils autorisés…');
    setError('');
    try {
      const response = await workspaceApi.send(value, cid, version, language);
      setCid(response.conversation_id);
      setVersion(response.version);
      setDraft('');
      localStorage.setItem(
        'onmt-chat:' + user!.user_id,
        response.conversation_id,
      );
      setMessages((prev) => [
        ...prev,
        { role: 'user', message: value },
        { role: 'assistant', ...response },
      ]);
      if (response.benchmark)
        setAnalyses((prev) => [
          ...response.benchmark!,
          ...prev.filter(
            (a) =>
              !response.benchmark!.some((b) => b.analysis_id === a.analysis_id),
          ),
        ]);
      if (response.analysis)
        setAnalyses((prev) => [
          response.analysis!,
          ...prev.filter(
            (a) => a.analysis_id !== response.analysis!.analysis_id,
          ),
        ]);
      if (response.report) {
        setSelectedReport(response.report);
        setReports((prev) => [
          response.report!,
          ...prev.filter((r) => r.report_id !== response.report!.report_id),
        ]);
      }
    } catch (e) {
      setDraft(value);
      setError(
        e instanceof Error
          ? e.message
          : 'La demande n’a pas abouti. Votre saisie est conservée.',
      );
    } finally {
      setBusy('');
    }
  }
  async function createFor(analysis: AnalysisResult) {
    if (busy) return;
    setBusy('Recherche des preuves et rédaction du rapport…');
    setError('');
    try {
      const r = await api.create({
        request_id: crypto.randomUUID(),
        analysis_ids: [analysis.analysis_id],
        title: `${metricNames[analysis.metric_id] || analysis.metric_id} — ${String(analysis.filters.destination || 'Territoires autorisés')}`,
        language,
        audience: 'direction',
        sections: ['summary'],
      });
      setSelectedReport(r);
      setReports((prev) => [r, ...prev]);
      setView('reports');
      await linkContext(analysis.analysis_id, r.report_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur du rapport.');
    } finally {
      setBusy('');
    }
  }
  async function linkContext(analysisId?: string, reportId?: string) {
    const saved = await workspaceApi.link(cid, version, analysisId, reportId);
    setCid(saved.conversation_id);
    setVersion(saved.version);
    localStorage.setItem('onmt-chat:' + user!.user_id, saved.conversation_id);
  }
  function reportChanged(report: ReportResult) {
    setSelectedReport(report);
    setReports((prev) => [
      report,
      ...prev.filter((r) => r.report_id !== report.report_id),
    ]);
    void linkContext(undefined, report.report_id).catch((e) =>
      setError(e.message),
    );
  }
  async function refresh() {
    setBusy('Vérification des sources et recherche des baisses annuelles…');
    setError('');
    try {
      const result = await workspaceApi.refresh();
      setCatalog(result.catalog);
      setAlerts(result.alerts);
      setAnalyses(await workspaceApi.analyses());
      setReports(await api.list());
      setStatus(await workspaceApi.status());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Actualisation impossible.');
    } finally {
      setBusy('');
    }
  }
  function newConversation() {
    setMessages([]);
    setCid(undefined);
    setVersion(0);
    setDraft('');
    setError('');
    setView('conversation');
    localStorage.removeItem('onmt-chat:' + user!.user_id);
    textarea.current?.focus();
  }

  if (checking)
    return (
      <div className="w-start" role="status">
        <span className="w-spinner" />
        Ouverture de votre espace…
      </div>
    );
  if (!user) return <Login onLogin={load} />;
  return (
    <div className="w-app">
      <a href="#main-content" className="w-skip">
        Aller au contenu
      </a>
      <aside
        className={`w-sidebar ${menu ? 'is-open' : ''}`}
        aria-label="Navigation principale"
      >
        <a className="w-brand" href="/" aria-label="ONMT Intelligence, accueil">
          onmt<span>intelligence</span>
          <i />
        </a>
        <p className="w-nav-caption">VOTRE ESPACE</p>
        <nav>
          {navigation.map((n) => (
            <button
              key={n.id}
              className={view === n.id ? 'is-active' : ''}
              onClick={() => {
                setView(n.id);
                setMenu(false);
                setError('');
              }}
              aria-current={view === n.id ? 'page' : undefined}
            >
              <Icon name={n.icon} />
              {n.label}
              {n.id === 'alerts' &&
                alerts.filter((a) => !a.stale).length > 0 && (
                  <span className="w-nav-count">
                    {alerts.filter((a) => !a.stale).length}
                  </span>
                )}
            </button>
          ))}
        </nav>
        <div className="w-sidebar-bottom">
          <div className="w-local-note">
            <span
              className={`w-dot ${status?.ollama_available ? '' : 'is-off'}`}
            />
            <div>
              <strong>
                {status === undefined
                  ? 'Vérification des services…'
                  : status.ollama_available
                    ? 'Ollama disponible'
                    : 'Ollama indisponible'}
              </strong>
              <small>Services sur votre ordinateur</small>
            </div>
          </div>
          <button
            className="w-account"
            disabled={!!busy}
            onClick={() => {
              void workspaceApi.logout().then(() => {
                setUser(undefined);
                setMessages([]);
                setCid(undefined);
                setVersion(0);
                setReports([]);
                setAnalyses([]);
              });
            }}
          >
            <span className="w-avatar">
              {user.user_id.slice(0, 1).toUpperCase()}
            </span>
            <span>
              <strong>
                {user.user_id === 'direction'
                  ? 'Direction'
                  : 'Équipe régionale'}
              </strong>
              <small>Se déconnecter</small>
            </span>
            <Icon name="logout" size={17} />
          </button>
        </div>
      </aside>
      <div className="w-main">
        <header className="w-header">
          <button
            className="w-mobile-menu"
            onClick={() => setMenu((v) => !v)}
            aria-expanded={menu}
            aria-label="Ouvrir la navigation"
          >
            ☰
          </button>
          <div className="w-breadcrumb">
            ONMT AI <span>/</span>{' '}
            {navigation.find((n) => n.id === view)?.label}
          </div>
          <div className="w-header-right">
            <span className="w-synthetic">
              <span className="w-dot" />{' '}
              {catalog === undefined
                ? 'Vérification des sources'
                : catalog.synthetic
                  ? 'Données synthétiques'
                  : 'Sources configurées'}
            </span>
            <label className="w-language">
              <span className="w-sr">Langue de la conversation</span>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
              >
                <option value="fr">FR · Français</option>
                <option value="ar">AR · العربية</option>
                <option value="ary">ARY · الدارجة</option>
                <option value="en">EN · English</option>
                <option value="es">ES · Español</option>
              </select>
            </label>
          </div>
        </header>
        <main id="main-content" className="w-content">
          <div className="w-page-title">
            <div>
              <span className="w-overline">
                INTELLIGENCE TOURISTIQUE · MAROC
              </span>
              <h1>
                {view === 'conversation' ? (
                  <>
                    Éclairer vos décisions,
                    <br />
                    <em>une conversation à la fois.</em>
                  </>
                ) : view === 'analyses' ? (
                  'Les données mises en perspective.'
                ) : view === 'reports' ? (
                  'Des constats aux décisions.'
                ) : view === 'documents' ? (
                  'Le contexte derrière les chiffres.'
                ) : view === 'alerts' ? (
                  'Les évolutions à regarder de près.'
                ) : (
                  'Des sources identifiées. Des services visibles.'
                )}
              </h1>
              <p>
                {view === 'conversation'
                  ? 'Interrogez vos données, explorez les résultats et préparez vos prochaines synthèses.'
                  : view === 'analyses'
                    ? 'Des calculs reproductibles, des périodes explicites et une formule pour chaque résultat.'
                    : view === 'reports'
                      ? 'Vos rapports sourcés, leurs révisions et les versions prêtes à partager.'
                      : view === 'documents'
                        ? 'Une bibliothèque autorisée pour enrichir vos analyses, avec des références vérifiables.'
                        : view === 'alerts'
                          ? 'Des baisses annuelles détectées lors d’une actualisation contrôlée.'
                          : 'Consultez le périmètre des données et l’état réel des outils locaux.'}
              </p>
            </div>
            {view === 'conversation' ? (
              <button
                className="w-secondary"
                disabled={!!busy}
                onClick={newConversation}
              >
                <Icon name="plus" size={16} /> Nouvelle conversation
              </button>
            ) : view === 'sources' || view === 'alerts' ? (
              <button
                className="w-secondary"
                disabled={!!busy}
                onClick={() => void refresh()}
              >
                <Icon name="database" size={16} /> Actualiser et vérifier
              </button>
            ) : null}
          </div>
          {error && (
            <div className="w-error" role="alert">
              {error}
            </div>
          )}
          {busy && (
            <div className="w-processing" role="status">
              <span className="w-spinner" />
              {busy}
              <span>
                Le traitement est local. Aucun pourcentage d’avancement n’est
                estimé.
              </span>
            </div>
          )}
          {view === 'conversation' && (
            <div className="w-chat-layout">
              <section className="w-chat">
                <div className="w-chat-top">
                  <span className="w-assistant-badge">
                    <Icon name="spark" size={17} />
                  </span>
                  <div>
                    <strong>Votre assistant ONMT</strong>
                    <small>Comprendre · analyser · rédiger</small>
                  </div>
                  <span className="w-secure-label">Accès contrôlé</span>
                </div>
                <div className="w-messages" aria-live="polite">
                  {!messages.length ? (
                    <div className="w-welcome">
                      <div className="w-motif" aria-hidden="true">
                        <Icon name="spark" size={38} />
                      </div>
                      <span className="w-overline">PARTONS D’UNE QUESTION</span>
                      <h2>
                        Que souhaitez-vous
                        <br />
                        comprendre aujourd’hui ?
                      </h2>
                      <p>
                        Une destination, une évolution, une période.
                        <br />
                        L’assistant retrouve les données de votre périmètre.
                      </p>
                      <div className="w-suggestions">
                        {suggestions.map((s, i) => (
                          <button
                            key={s.label}
                            onClick={() => {
                              setDraft(s.question);
                              textarea.current?.focus();
                            }}
                          >
                            <span>0{i + 1}</span>
                            <div>
                              <strong>{s.label}</strong>
                              <small>{s.description}</small>
                            </div>
                            <Icon name="arrow" size={16} />
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    messages.map((m, i) => (
                      <div
                        className={`w-message ${m.role === 'user' ? 'is-user' : 'is-assistant'}`}
                        key={i}
                      >
                        <div className="w-message-author">
                          {m.role === 'user' ? 'VOUS' : 'ONMT INTELLIGENCE'}
                        </div>
                        <p dir="auto">{m.message}</p>
                        {m.analysis && (
                          <AnalysisCard
                            analysis={m.analysis}
                            onReport={() => void createFor(m.analysis!)}
                          />
                        )}
                        {m.benchmark?.map((a) => (
                          <AnalysisCard
                            key={a.analysis_id}
                            analysis={a}
                            onReport={() => void createFor(a)}
                          />
                        ))}
                        {m.report && (
                          <div className="w-inline-report">
                            <Icon name="report" />
                            <div>
                              <strong>
                                Rapport disponible · version {m.report.version}
                              </strong>
                              <small>
                                {m.report.sections.length} section ·{' '}
                                {m.report.sources.length} sources
                              </small>
                            </div>
                            <button
                              className="w-text-button"
                              onClick={() => {
                                setSelectedReport(
                                  reports.find(
                                    (r) => r.report_id === m.report!.report_id,
                                  ) || m.report,
                                );
                                setView('reports');
                              }}
                            >
                              Ouvrir ↗
                            </button>
                          </div>
                        )}
                        {m.evidence?.evidence.map((e) => (
                          <blockquote key={e.passage.chunk_id}>
                            {e.passage.text}
                            <footer>
                              {e.source.name} · p. {e.passage.page_start} ·{' '}
                              {e.passage.extraction_method === 'ocr'
                                ? 'OCR à relire'
                                : 'Texte extrait'}
                            </footer>
                          </blockquote>
                        ))}
                        {m.actions && (
                          <details className="w-execution">
                            <summary>
                              Opérations effectuées · {m.actions.length}
                            </summary>
                            <ol>
                              {m.actions.map((a, j) => (
                                <li key={j}>
                                  <b>{a.tool}</b> · {a.detail}
                                </li>
                              ))}
                            </ol>
                          </details>
                        )}
                      </div>
                    ))
                  )}
                  <div ref={bottom} />
                </div>
                <form
                  className="w-composer"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void send();
                  }}
                >
                  <label className="w-sr" htmlFor="onmt-question">
                    Votre question
                  </label>
                  <textarea
                    id="onmt-question"
                    ref={textarea}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Posez votre question sur les données touristiques…"
                    dir="auto"
                    maxLength={4000}
                    rows={2}
                    onKeyDown={(e) => {
                      if (
                        e.key === 'Enter' &&
                        !e.shiftKey &&
                        !e.nativeEvent.isComposing
                      ) {
                        e.preventDefault();
                        void send();
                      }
                    }}
                  />
                  <div className="w-composer-footer">
                    <span>
                      <Icon name="database" size={14} /> Sources et calculs
                      traçables
                    </span>
                    <button
                      className="w-send"
                      disabled={!!busy || !draft.trim()}
                      aria-label="Envoyer la question"
                      type="submit"
                    >
                      <Icon name="arrow" />
                    </button>
                  </div>
                </form>
                <p className="w-chat-note">
                  Vérifiez les sources avant toute décision.{' '}
                  {catalog?.synthetic
                    ? 'Les données affichées sont synthétiques.'
                    : 'Les droits et sources sont contrôlés côté serveur.'}
                </p>
              </section>
              <aside className="w-context">
                <section className="w-panel w-context-card">
                  <span className="w-overline">LE CADRE DE VOTRE ANALYSE</span>
                  <h2>
                    Une réponse,
                    <br />
                    des fondations claires.
                  </h2>
                  <div className="w-context-row">
                    <span>Destinations accessibles</span>
                    <strong>{user.allowed_territories.length}</strong>
                  </div>
                  <div className="w-context-row">
                    <span>Sources dans votre périmètre</span>
                    <strong>{catalog?.sources.length ?? '—'}</strong>
                  </div>
                  <div className="w-context-row">
                    <span>Rapports disponibles</span>
                    <strong>{reports.length}</strong>
                  </div>
                  <p className="w-muted">
                    {user.allowed_territories.join(' · ')}
                  </p>
                  <button
                    className="w-text-button"
                    onClick={() => setView('sources')}
                  >
                    Explorer les sources <Icon name="arrow" size={16} />
                  </button>
                </section>
                <section className="w-editorial-card">
                  <span className="w-overline">POUR ALLER PLUS LOIN</span>
                  <h3>
                    Le contexte se construit
                    <br />
                    dans la conversation.
                  </h3>
                  <p>
                    Après une comparaison, essayez « Et pour Marrakech ? », puis
                    « Prépare un rapport pour la direction ».
                  </p>
                  <button
                    onClick={() => {
                      setDraft('Et pour Marrakech ?');
                      textarea.current?.focus();
                    }}
                    className="w-text-button"
                  >
                    Préparer une relance <Icon name="arrow" size={16} />
                  </button>
                </section>
                <p className="w-local-caption">
                  Traitement IA local · aucun service payant
                  <br />
                  Périmètre de développement académique
                </p>
              </aside>
            </div>
          )}
          {view === 'analyses' && (
            <div className="w-analysis-grid">
              {!analyses.length ? (
                <Empty
                  icon="chart"
                  title="Votre première analyse commence dans le chat."
                  action="Poser une question"
                  onClick={() => setView('conversation')}
                />
              ) : (
                analyses.map((a) => (
                  <AnalysisCard
                    key={a.analysis_id}
                    analysis={a}
                    onReport={() => void createFor(a)}
                  />
                ))
              )}
            </div>
          )}
          {view === 'reports' && (
            <div className="w-reports-layout">
              <aside className="w-report-list">
                <h2>
                  Votre bibliothèque <span>{reports.length}</span>
                </h2>
                {!reports.length && (
                  <p className="w-muted">
                    Les rapports créés depuis vos analyses apparaîtront ici.
                  </p>
                )}
                {reports.map((r) => (
                  <button
                    className={
                      selectedReport?.report_id === r.report_id
                        ? 'is-active'
                        : ''
                    }
                    key={r.report_id}
                    onClick={() => {
                      void api
                        .read(r.report_id)
                        .then(setSelectedReport)
                        .catch((e) => setError(e.message));
                    }}
                  >
                    <Icon name="report" />
                    <div>
                      <strong>{r.sections[0]?.title || 'Rapport'}</strong>
                      <small>
                        Version {r.version} · {r.sources.length} sources
                      </small>
                    </div>
                  </button>
                ))}
              </aside>
              {selectedReport ? (
                <ReportPanel
                  key={selectedReport.report_id}
                  report={selectedReport}
                  onChange={reportChanged}
                  onError={setError}
                />
              ) : (
                <Empty
                  icon="report"
                  title="Une synthèse fidèle à vos résultats."
                  action={
                    latest
                      ? 'Créer depuis la dernière analyse'
                      : 'Commencer une analyse'
                  }
                  onClick={() =>
                    latest ? void createFor(latest) : setView('conversation')
                  }
                />
              )}
            </div>
          )}
          {view === 'documents' && <DocumentsPanel />}
          {view === 'alerts' && (
            <section className="w-panel">
              <div className="w-card-heading">
                <h2>Signaux détectés</h2>
                <span className="w-tag">
                  À l’actualisation · seuil −15 % annuel
                </span>
              </div>
              <p className="w-muted">
                Ce contrôle compare chaque mois au même mois de l’année
                précédente. Il ne prouve aucune cause et ne tourne pas en
                continu.
              </p>
              {!alerts.length ? (
                <Empty
                  icon="bell"
                  title="Aucun signal enregistré."
                  action="Lancer une vérification"
                  onClick={() => void refresh()}
                />
              ) : (
                <div className="w-alert-grid">
                  {alerts.map((a) => (
                    <article className="w-alert-card" key={a.id}>
                      <span className="w-alert-icon">
                        <Icon name="bell" />
                      </span>
                      <span className="w-overline">
                        {a.stale
                          ? 'SOURCE MODIFIÉE · À REVÉRIFIER'
                          : 'BAISSE ANNUELLE DÉTECTÉE'}
                      </span>
                      <h3>{a.destination}</h3>
                      <strong>{a.change_pct} %</strong>
                      <p>Nuitées · {a.month.slice(0, 7)}</p>
                      <details className="w-proof">
                        <summary>Voir le constat et la règle</summary>
                        <p>
                          {a.current} nuitées contre {a.previous} l’année
                          précédente.
                        </p>
                        <p>{a.source}</p>
                        <code>{a.formula}</code>
                        <p>{a.warning}</p>
                      </details>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}
          {view === 'sources' && (
            <div className="w-sources">
              <section className="w-panel">
                <div className="w-card-heading">
                  <h2>Catalogue des sources</h2>
                  <span className="w-tag">Lecture native QVD</span>
                </div>
                <p className="w-muted">{catalog?.label}</p>
                {catalog?.sources.map((s) => (
                  <article className="w-source-card" key={s.id}>
                    <div className="w-card-heading">
                      <h3>{s.name || s.id}</h3>
                      <span
                        className={`w-tag ${s.quality_errors.length ? 'is-warning' : ''}`}
                      >
                        {s.quality_errors.length
                          ? 'À vérifier'
                          : 'Schéma contrôlé'}
                      </span>
                    </div>
                    <p>
                      {s.rows ?? '—'} lignes autorisées · {s.module}
                    </p>
                    <p className="w-muted">
                      {s.period?.start} → {s.period?.end}
                    </p>
                    <details className="w-proof">
                      <summary>Champs, grain et version</summary>
                      <p>Grain : {s.grain?.join(' × ')}</p>
                      <ul>
                        {Object.entries(s.fields || {}).map(
                          ([logical, physical]) => (
                            <li key={logical}>
                              {logical} → {physical} ·{' '}
                              {s.units?.[logical] || 'dimension'}
                            </li>
                          ),
                        )}
                      </ul>
                      <p className="w-break">SHA-256 : {s.version}</p>
                      {s.quality_errors.map((e) => (
                        <p key={e}>{e}</p>
                      ))}
                      {s.error && <p>{s.error}</p>}
                    </details>
                  </article>
                ))}
                <h3>Relations configurées</h3>
                {catalog?.relations.map((r) => (
                  <p key={r.left + r.right}>
                    {r.left} ↔ {r.right} ·{' '}
                    {r.valid ? 'grains concordants' : 'relation à vérifier'} ·{' '}
                    {r.keys.join(' × ')}
                  </p>
                ))}
              </section>
              <section className="w-panel w-services">
                <span className="w-overline">SUR VOTRE ORDINATEUR</span>
                <h2>Services locaux</h2>
                {[
                  ['Ollama', status?.ollama_available],
                  ['Modèle configuré', status?.configured_model_available],
                  ['OCR activé', status?.ocr_enabled],
                  ['Tesseract présent', status?.tesseract_available],
                ].map(([label, ok]) => (
                  <div className="w-service" key={String(label)}>
                    <span>{label}</span>
                    <span className={`w-dot ${ok ? '' : 'is-off'}`} />
                    <strong>{ok ? 'Oui' : 'Non'}</strong>
                  </div>
                ))}
                <p className="w-muted">
                  Ces contrôles indiquent la disponibilité observée lors du
                  chargement ou de l’actualisation. Une génération peut encore
                  échouer.
                </p>
                <button
                  className="w-secondary"
                  disabled={!!busy}
                  onClick={() => void refresh()}
                >
                  Vérifier maintenant
                </button>
                <div className="w-service-note">
                  Les comptes, conversations et résultats sont stockés
                  localement. Le patrimoine QVD est lu directement, sans copie
                  dans une base analytique.
                </div>
              </section>
            </div>
          )}
        </main>
        <footer className="w-footer">
          <span>
            ONMT AI <i /> Intelligence au service du territoire
          </span>
          <span>
            Projet académique ·{' '}
            {catalog?.synthetic
              ? 'Données synthétiques'
              : 'Sources configurées'}
          </span>
        </footer>
      </div>
    </div>
  );
}

function Empty({
  icon,
  title,
  action,
  onClick,
}: {
  icon: string;
  title: string;
  action: string;
  onClick: () => void;
}) {
  return (
    <div className="w-empty">
      <span>
        <Icon name={icon} size={32} />
      </span>
      <h2>{title}</h2>
      <button className="w-secondary" onClick={onClick}>
        {action} <Icon name="arrow" size={17} />
      </button>
    </div>
  );
}
