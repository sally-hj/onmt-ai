import type { AppConfig, ErrorResponse, EvidenceResult, Language, ReportRequest, ReportResult, ReportRevisionRequest } from './types';

export class ApiError extends Error {
  constructor(public detail: ErrorResponse) { super(detail.message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(path, { credentials: 'same-origin', ...init }); }
  catch { throw new Error('API inaccessible. Vérifiez que le backend est démarré.'); }
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ code: 'tool_failed', request_id: '', message: 'Erreur du serveur.' }));
    throw new ApiError(detail);
  }
  return response.json();
}
const json = (body: unknown, method = 'POST'): RequestInit => ({ method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
export const api = {
  config: () => request<AppConfig>('/api/reports/config'),
  list: () => request<ReportResult[]>('/api/reports'),
  create: (body: ReportRequest) => request<ReportResult>('/api/reports', json(body)),
  read: (id: string, version?: number) => request<ReportResult>(`/api/reports/${encodeURIComponent(id)}${version ? `?version=${version}` : ''}`),
  revise: (body: ReportRevisionRequest) => request<ReportResult>(`/api/reports/${encodeURIComponent(body.report_id)}/sections/${body.section_id}`, json(body, 'PATCH')),
  export: (id: string, version: number) => request<ReportResult>(`/api/reports/${encodeURIComponent(id)}/export?version=${version}`, {method:'POST'}),
  search: (question: string) => request<EvidenceResult>('/api/documents/search', json({question, limit:5})),
  upload: (file: File, title: string, language: Language, id: string) => {
    const body = new FormData(); body.append('file', file); body.append('metadata', JSON.stringify({ title, language }));
    if (id.trim()) body.append('document_id', id.trim());
    return request<{document: {document_id: string; version: number; warnings: string[]}; duplicate: boolean}>('/api/documents', {method:'POST', body});
  },
  download: async (path: string) => {
    if (!/^\/api\/reports\/[^/]+\/pdf\?version=\d+$/.test(path)) throw new Error('Route PDF invalide.');
    const response = await fetch(path, {credentials:'same-origin'});
    if (!response.ok) throw new ApiError(await response.json());
    const blob = await response.blob();
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'rapport.pdf'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
