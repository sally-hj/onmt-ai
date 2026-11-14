import { useState } from 'react';
import { api } from '../reports/api';
import type { ReportResult, SectionId } from '../reports/types';

export function ReportPanel({
  report,
  onChange,
  onError,
}: {
  report: ReportResult;
  onChange: (r: ReportResult) => void;
  onError: (s: string) => void;
}) {
  const [busy, setBusy] = useState('');
  const [instruction, setInstruction] = useState('résumer');
  const [section, setSection] = useState<SectionId>(
    report.sections[0]?.section_id || 'summary',
  );
  const [preview, setPreview] = useState(false);
  async function run(label: string, operation: () => Promise<void>) {
    setBusy(label);
    onError('');
    try {
      await operation();
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Erreur du rapport.');
    } finally {
      setBusy('');
    }
  }
  return (
    <article className="w-report">
      <div className="w-card-heading">
        <div>
          <span className="w-overline">NOTE DE SYNTHÈSE</span>
          <h3>Rapport · version {report.version}</h3>
        </div>
        <span className="w-tag">{report.status}</span>
      </div>
      {report.is_synthetic && (
        <p className="w-synthetic">
          Données synthétiques · document de développement
        </p>
      )}
      {report.sections.map((s) => (
        <section className="w-report-section" key={s.section_id}>
          <h4>{s.title}</h4>
          <p dir="auto">{s.content}</p>
        </section>
      ))}
      <details className="w-proof">
        <summary>
          Références et limites ({report.sources.length} sources)
        </summary>
        {report.sources.map((s) => (
          <p key={s.source_id}>
            {s.name} · {s.source_type} · {s.source_id}
            <br />
            <small>
              Version {s.version} · pages {s.pages.join(', ') || '—'} ·{' '}
              {s.fields.join(', ')}
            </small>
          </p>
        ))}
        <ul>
          {report.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      </details>
      <form
        className="w-edit"
        onSubmit={(e) => {
          e.preventDefault();
          void run('Révision en cours…', async () =>
            onChange(
              await api.revise({
                request_id: crypto.randomUUID(),
                report_id: report.report_id,
                base_version: report.version,
                section_id: section,
                instruction,
              }),
            ),
          );
        }}
      >
        <fieldset disabled={!!busy}>
          <legend>Affiner ce rapport</legend>
          <label>
            Section
            <select
              value={section}
              onChange={(e) => setSection(e.target.value as SectionId)}
            >
              {report.sections.map((s) => (
                <option key={s.section_id} value={s.section_id}>
                  {s.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Modification
            <select
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            >
              <option value="résumer">Résumer</option>
              <option value="détailler">Détailler</option>
              <option value="reformuler">Reformuler</option>
              <option value="langue:ar">Traduire en arabe</option>
              <option value="langue:fr">Traduire en français</option>
              <option value="langue:en">Traduire en anglais</option>
              <option value="langue:es">Traduire en espagnol</option>
              <option value="langue:ary">Traduire en darija</option>
              <option value="adapter:ministere">Adapter au ministère</option>
              <option value="adapter:regional">Adapter au régional</option>
            </select>
          </label>
          <button className="w-secondary" type="submit">
            Créer une nouvelle version
          </button>
        </fieldset>
      </form>
      <div className="w-report-actions">
        <button
          className="w-primary"
          disabled={!!busy}
          onClick={() =>
            void run('Préparation du PDF…', async () => {
              const next = await api.export(report.report_id, report.version);
              onChange(next);
              setPreview(true);
            })
          }
        >
          Prévisualiser le PDF ↗
        </button>
        {report.download_path && (
          <button
            className="w-secondary"
            disabled={!!busy}
            onClick={() =>
              void run('Téléchargement…', async () =>
                api.download(report.download_path!),
              )
            }
          >
            Télécharger
          </button>
        )}
      </div>
      {busy && (
        <p role="status" className="w-loading">
          {busy}
        </p>
      )}
      {preview && report.download_path && (
        <iframe
          title={`Aperçu du rapport version ${report.version}`}
          src={`${report.download_path}&inline=true`}
          className="w-pdf"
        />
      )}
    </article>
  );
}
