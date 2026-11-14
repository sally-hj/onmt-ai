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
}
export interface Status {
  ollama_available: boolean;
  configured_model_available: boolean;
  generation_mode: string;
  ocr_enabled: boolean;
  tesseract_available: boolean;
  synthetic: boolean;
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
  me: () => request<AccessContext>('/api/auth/me'),
  login: (username: string, password: string) =>
    request('/api/auth/login', { username, password }, 'POST'),
  logout: () => request('/api/auth/logout', {}, 'POST'),
  catalog: () => request<Catalog>('/api/sources'),
  alerts: () => request<Alert[]>('/api/alerts'),
  analyses: () => request<AnalysisResult[]>('/api/analyses'),
  status: () => request<Status>('/api/system/status'),
  send: (
    message: string,
    cid: string | undefined,
    version: number,
    language: Language,
  ) =>
    request<Turn>(
      '/api/conversations/messages',
      {
        message,
        conversation_id: cid ?? null,
        base_version: version,
        language,
      },
      'POST',
    ),
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
