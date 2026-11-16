import type {
  AccessContext,
  AnalysisResult,
  EvidenceResult,
  Language,
  ReportResult,
} from '../reports/types';

export interface Source {
  id: string;
  name?: string;
  module: string;
  version?: string;
  rows?: number;
  fields?: Record<string, string>;
  units?: Record<string, string>;
  types?: Record<string, string[]>;
  grain?: string[];
  quality_errors: string[];
  destinations?: string[];
  markets?: string[];
  period?: { start: string; end: string };
  error?: string;
}
export interface Catalog {
  synthetic: boolean;
  label: string;
  sources: Source[];
  relations: { left: string; right: string; valid: boolean; keys: string[] }[];
}
export interface Alert {
  id: string;
  destination: string;
  month: string;
  current: number;
  previous: number;
  change_pct: number;
  stale: boolean;
  source: string;
  formula: string;
  warning: string;
  synthetic: boolean;
  metric_id?: string;
  market?: string | null;
}
export interface Status {
  ollama_available: boolean;
  configured_model_available: boolean;
  generation_mode: string;
  ocr_enabled: boolean;
  tesseract_available: boolean;
  synthetic: boolean;
  monitor?: {
    running: boolean;
    interval_seconds: number;
    last_success_at?: string;
    error?: string;
  };
}
export interface Job {
  id: string;
  status: string;
  stage: string;
  steps: { stage: string; started_at: string }[];
  result?: Turn;
  error?: { code: string; message: string };
}
export interface Message {
  role?: 'user' | 'assistant';
  message: string;
  language?: Language;
  analysis?: AnalysisResult;
  benchmark?: AnalysisResult[];
  report?: ReportResult;
  evidence?: EvidenceResult;
  actions?: { tool: string; status: string; detail: string }[];
  needs_clarification?: boolean;
  agent_trace?: { agent: string; decision: string; tools: string[] }[];
  diagnostic?: Diagnostic;
  kpi_proposal?: {
    proposal_id: string;
    definition: { label: string; interpretation: string };
    example: {
      formula: string;
      value: number;
      unit: string;
      period?: { start: string; end: string };
      filters?: Record<string, string>;
    };
  };
  deck_path?: string;
}
export interface Diagnostic {
  kind: string;
  synthetic: boolean;
  warning?: string;
  interpretation?: string;
  comparability?: string;
  formula?: string;
  stage?: string;
  rule?: string;
  limit?: string;
  points?: {
    market?: string;
    destination?: string;
    value: number | null;
    volume?: number;
    latitude?: number;
    longitude?: number;
    unit?: string;
    source?: string;
    quadrant?: string;
  }[];
  rows?: {
    destination: string;
    market_growth_pct: number | null;
    relative_share: number | null;
    quadrant: string;
    indicators: Record<string, number | null>;
  }[];
  units?: Record<string, string>;
  bcg?: {
    growth_threshold_pct: number;
    relative_share_threshold: number;
    x: string;
    y: string;
  };
  thresholds?: { value_mad_per_arrival: number; volume_arrivals: number };
  baseline?: number;
  scenario_value?: number;
  shock_pct?: number;
  unit?: string;
}
export interface Turn extends Message {
  conversation_id: string;
  version: number;
}
export interface Conversation {
  conversation_id: string;
  version: number;
  messages: Message[];
}

export async function request<T>(
  url: string,
  body?: unknown,
  method = 'GET',
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: 'same-origin',
    ...(body === undefined
      ? {}
      : {
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      `${data.message || 'Erreur du service'} (${data.code || response.status})`,
    );
  return data as T;
}

export const workspaceApi = {
  reportOperation: async (
    kind: 'create' | 'revise' | 'export' | 'presentation',
    body: Record<string, unknown>,
    progress?: (job: Job) => void,
  ) => {
    let job = await request<Job>(
      '/api/reports/jobs',
      { kind, ...body, idempotency_key: crypto.randomUUID() },
      'POST',
    );
    while (['queued', 'running', 'cancel_requested'].includes(job.status)) {
      progress?.(job);
      await new Promise((resolve) => setTimeout(resolve, 1200));
      job = await request<Job>('/api/conversations/jobs/' + job.id);
    }
    if (job.status !== 'completed' || !job.result)
      throw new Error(job.error?.message || 'Tâche interrompue.');
    return job.result;
  },
  me: () => request<AccessContext>('/api/auth/me'),
  login: (username: string, password: string) =>
    request('/api/auth/login', { username, password }, 'POST'),
  logout: async () => {
    try {
      return await request('/api/auth/logout', {}, 'POST');
    } finally {
      sessionStorage.removeItem('onmt-pending-job');
    }
  },
  catalog: () => request<Catalog>('/api/sources'),
  alerts: () => request<Alert[]>('/api/alerts'),
  analyses: () => request<AnalysisResult[]>('/api/analyses'),
  status: () => request<Status>('/api/system/status'),
  send: async (
    message: string,
    cid: string | undefined,
    version: number,
    language: Language,
    progress?: (job: Job) => void,
  ) => {
    const body = {
      message,
      conversation_id: cid ?? null,
      base_version: version,
      language,
    };
    const fingerprint = JSON.stringify(body);
    const saved = JSON.parse(
      sessionStorage.getItem('onmt-pending-job') || 'null',
    ) as { id: string; fingerprint: string } | null;
    if (saved && saved.fingerprint !== fingerprint)
      throw new Error(
        'Une tâche précédente reste à vérifier. Renvoyez sa question ou reconnectez-vous après sa fin.',
      );
    const job = saved
      ? await request<Job>('/api/conversations/jobs/' + saved.id)
      : await request<Job>(
          '/api/conversations/jobs',
          { ...body, idempotency_key: crypto.randomUUID() },
          'POST',
        );
    sessionStorage.setItem(
      'onmt-pending-job',
      JSON.stringify({ id: job.id, fingerprint }),
    );
    let current = job;
    while (['queued', 'running', 'cancel_requested'].includes(current.status)) {
      progress?.(current);
      await new Promise((resolve) => setTimeout(resolve, 1200));
      current = await request<Job>('/api/conversations/jobs/' + job.id);
    }
    sessionStorage.removeItem('onmt-pending-job');
    if (current.status !== 'completed' || !current.result)
      throw new Error(current.error?.message || 'Tâche interrompue.');
    return current.result;
  },
  cancel: (id: string) =>
    request<Job>('/api/conversations/jobs/' + id + '/cancel', {}, 'POST'),
  conversation: (id: string) =>
    request<Conversation>('/api/conversations/' + encodeURIComponent(id)),
  link: (
    conversation_id: string | undefined,
    base_version: number,
    analysis_id?: string,
    report_id?: string,
  ) =>
    request<Conversation>(
      '/api/conversations/context',
      {
        conversation_id: conversation_id ?? null,
        base_version,
        analysis_id: analysis_id ?? null,
        report_id: report_id ?? null,
      },
      'POST',
    ),
  refresh: () =>
    request<{ catalog: Catalog; alerts: Alert[] }>(
      '/api/sources/refresh',
      {},
      'POST',
    ),
};
