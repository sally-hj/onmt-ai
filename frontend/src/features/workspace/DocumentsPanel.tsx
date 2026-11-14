import { useEffect, useState } from 'react';
import { api } from '../reports/api';
import type { EvidenceResult, Language } from '../reports/types';
import { request } from './api';

interface Document {
  document_id: string;
  version: number;
  metadata: { title: string; language: string };
  warnings: string[];
}
export function DocumentsPanel() {
  const [documents, setDocuments] = useState<Document[]>([]),
    [file, setFile] = useState<File>(),
    [title, setTitle] = useState(''),
    [language, setLanguage] = useState<Language>('fr');
  const [question, setQuestion] = useState(''),
    [evidence, setEvidence] = useState<EvidenceResult>(),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(''),
    [notice, setNotice] = useState('');
  const [documentId, setDocumentId] = useState('');
  useEffect(() => {
    void request<Document[]>('/api/documents')
      .then(setDocuments)
      .catch((e) => setError(e.message));
  }, []);
  async function run(label: string, action: () => Promise<void>) {
    setError('');
    setBusy(label);
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur documentaire.');
    } finally {
      setBusy('');
    }
  }
  return (
    <div className="w-document-grid">
      <section className="w-panel">
        <span className="w-overline">ENRICHIR LES ANALYSES</span>
        <h2>Votre bibliothèque documentaire</h2>
        <p className="w-muted">
          Importez vos PDF autorisés. Les scans sont traités localement par OCR
          ; chaque extrait conserve sa page et sa version.
        </p>
        {error && (
          <p role="alert" className="w-error">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="w-success">
            {notice}
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!file) return;
            void run(
              'Extraction, OCR si nécessaire et indexation…',
              async () => {
                const result = await api.upload(
                  file,
                  title,
                  language,
                  documentId,
                );
                setNotice(
                  `Document indexé · version ${result.document.version}${result.duplicate ? ' · doublon reconnu' : ''} · ${result.document.warnings.join(', ')}`,
                );
                setDocuments(await request<Document[]>('/api/documents'));
              },
            );
          }}
        >
          <fieldset disabled={!!busy}>
            <label className="w-upload">
              Fichier PDF
              <input
                type="file"
                accept="application/pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0])}
              />
              <span>Extraction textuelle et OCR · 20 Mio maximum</span>
            </label>
            <label>
              Titre du document
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={300}
              />
            </label>
            <label>
              Langue
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
              >
                <option value="fr">Français</option>
                <option value="ar">Arabe</option>
                <option value="en">Anglais</option>
                <option value="es">Espagnol</option>
                <option value="ary">Darija</option>
              </select>
            </label>
            <label>
              Document existant à mettre à jour
              <select
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
              >
                <option value="">Nouveau document</option>
                {documents.map((d) => (
                  <option key={d.document_id} value={d.document_id}>
                    {d.metadata.title} · v{d.version}
                  </option>
                ))}
              </select>
            </label>
            <button className="w-primary" type="submit">
              Importer et indexer ↗
            </button>
          </fieldset>
        </form>
        {busy && (
          <p role="status" className="w-loading">
            {busy}
          </p>
        )}
        <div className="w-document-list">
          {!documents.length ? (
            <p className="w-muted">Aucun document dans votre périmètre.</p>
          ) : (
            documents.map((d) => (
              <article key={d.document_id}>
                <span className="w-document-icon">PDF</span>
                <div>
                  <strong>{d.metadata.title}</strong>
                  <p>
                    Version {d.version} · {d.metadata.language.toUpperCase()}
                  </p>
                  <a
                    href={`/api/documents/${encodeURIComponent(d.document_id)}/pdf?version=${d.version}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Consulter l’original ↗
                  </a>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
      <section className="w-panel">
        <span className="w-overline">RECHERCHE SÉMANTIQUE</span>
        <h2>Retrouver une preuve</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run('Recherche des passages autorisés…', async () =>
              setEvidence(await api.search(question)),
            );
          }}
        >
          <fieldset disabled={!!busy}>
            <label>
              Question documentaire
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                required
                maxLength={2000}
                placeholder="Comment les nuitées sont-elles définies ?"
              />
            </label>
            <button className="w-secondary">Rechercher</button>
          </fieldset>
        </form>
        {evidence && (
          <div className="w-evidence">
            {!evidence.evidence.length && (
              <p>Aucun passage pertinent autorisé.</p>
            )}
            {evidence.evidence.map((e) => (
              <blockquote key={e.passage.chunk_id}>
                <p>{e.passage.text}</p>
                <footer>
                  {e.source.name} · p. {e.passage.page_start} · v
                  {e.passage.version}
                  {e.passage.extraction_method === 'ocr'
                    ? ' · OCR : transcription à relire'
                    : ''}
                </footer>
              </blockquote>
            ))}
            {evidence.warnings.map((w) => (
              <p className="w-muted" key={w}>
                {w}
              </p>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
