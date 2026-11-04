export type Language = 'fr' | 'ar' | 'ary' | 'en' | 'es';
export interface Period { start: string; end: string }
export interface AccessContext { user_id: string; roles: string[]; allowed_modules: string[]; allowed_territories: string[] }
export interface AnalysisRequest { request_id: string; operation: 'value'|'compare'|'forecast'; metric_id: string; period: Period; comparison_period: Period|null; filters: Record<string,unknown>; language: Language; forecast_horizon: number|null; forecast_frequency: 'month'|'quarter'|'year'|null }
export interface AnalysisResult { request_id: string; analysis_id: string; metric_id: string; status: 'ok'|'partial'|'unavailable'; period: Period; comparison_period: Period|null; filters: Record<string,unknown>; unit: string; values: Record<string,number|null>; series: {date: string; value: number|null; kind: 'observed'|'forecast'; lower: number|null; upper: number|null}[]; formula: string; sources: SourceReference[]; warnings: string[]; is_synthetic: boolean }
export type SectionId = 'summary' | 'diagnostic' | 'comparison' | 'forecast' | 'recommendations' | 'limitations';
export interface SourceReference { source_id: string; source_type: 'qvd' | 'document' | 'external'; name: string; version: string; fields: string[]; pages: number[] }
export interface ReportRequest { request_id: string; analysis_ids: string[]; title: string; language: Language; audience: 'direction' | 'ministere' | 'regional'; sections: SectionId[] }
export interface ReportRevisionRequest { request_id: string; report_id: string; base_version: number; section_id: SectionId; instruction: string }
export interface ReportSection { section_id: SectionId; title: string; content: string; source_ids: string[] }
export interface ReportResult { request_id: string; report_id: string; version: number; status: 'pending' | 'running' | 'completed' | 'failed'; sections: ReportSection[]; sources: SourceReference[]; download_path: string | null; warnings: string[]; is_synthetic: boolean }
export interface ErrorResponse { request_id: string; code: string; message: string }
export interface AppConfig { demo: boolean; demo_embeddings: boolean; generation: 'synchronous'; ollama_enabled: boolean }
export interface EvidenceResult { evidence: {passage: {chunk_id: string; document_id: string; version: number; page_start: number; page_end: number; text: string; language: Language}; source: SourceReference; distance: number}[]; warnings: string[] }
