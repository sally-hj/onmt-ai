import { InteractiveChart } from './InteractiveChart';
import type { AnalysisResult } from '../reports/types';

export const metricNames: Record<string, string> = {
  overnight_stays: 'Nuitées touristiques',
  arrivals: 'Arrivées touristiques',
  seats: 'Sièges aériens',
  bookings: 'Réservations',
  budget: 'Budget prévu',
  spent: 'Dépenses exécutées',
  committed: 'Engagements',
  travel_receipts: 'Recettes voyages',
  room_revenue: 'Recettes des chambres',
  average_stay: 'Durée moyenne de séjour',
  occupancy: 'Taux d’occupation',
  revpar: 'RevPAR',
  average_room_price: 'Prix moyen par chambre',
  budget_execution: 'Exécution budgétaire',
  click_rate: 'Taux de clic',
  spend_per_night: 'Dépenses par nuitée',
};
export const formatNumber = (v: number | null | undefined) =>
  v == null
    ? 'Indisponible'
    : new Intl.NumberFormat('fr-MA', { maximumFractionDigits: 2 }).format(v);

export function DataChart({ analysis }: { analysis: AnalysisResult }) {
  return (
    <InteractiveChart
      analysis={analysis}
      label={metricNames[analysis.metric_id]}
    />
  );
}

export function AnalysisCard({
  analysis,
  onReport,
}: {
  analysis: AnalysisResult;
  onReport?: () => void;
}) {
  const change = analysis.values.change_pct;
  const firstForecast = analysis.series.find((p) => p.kind === 'forecast');
  return (
    <article className="w-analysis">
      <div className="w-card-heading">
        <div>
          <span className="w-overline">RÉSULTAT CALCULÉ</span>
          <h3>{metricNames[analysis.metric_id] || analysis.metric_id}</h3>
        </div>
        <span className="w-tag">
          {String(analysis.filters.destination || 'Périmètre autorisé')}
        </span>
      </div>
      <div className="w-values">
        <div>
          <span>
            {analysis.values.current !== undefined
              ? 'Période étudiée'
              : firstForecast
                ? 'Première prévision'
                : 'Valeur'}
          </span>
          <strong>
            {formatNumber(
              analysis.values.current ??
                analysis.values.value ??
                firstForecast?.value,
            )}
          </strong>
          <small>
            {analysis.unit}
            {firstForecast ? ` · ${firstForecast.date.slice(0, 7)}` : ''}
          </small>
        </div>
        {analysis.values.previous !== undefined && (
          <div>
            <span>Période de référence</span>
            <strong>{formatNumber(analysis.values.previous)}</strong>
            <small>{analysis.unit}</small>
          </div>
        )}
        {change !== undefined && (
          <div>
            <span>Évolution calculée</span>
            <strong
              className={change != null && change < 0 ? 'w-down' : 'w-up'}
            >
              {change != null && change > 0 ? '+' : ''}
              {formatNumber(change)}
              {change != null ? ' %' : ''}
            </strong>
            <small>Aucune cause déduite</small>
          </div>
        )}
      </div>
      <DataChart analysis={analysis} />
      <details className="w-proof">
        <summary>Sources, filtres et formule</summary>
        <p>
          <b>Période :</b> {analysis.period.start} → {analysis.period.end}
        </p>
        {analysis.comparison_period && (
          <p>
            <b>Référence :</b> {analysis.comparison_period.start} →{' '}
            {analysis.comparison_period.end}
          </p>
        )}
        <p>
          <b>Filtres :</b> {JSON.stringify(analysis.filters)}
        </p>
        <p>
          <b>Formule :</b> <code>{analysis.formula}</code>
        </p>
        {analysis.sources.map((s) => (
          <p key={s.source_id}>
            <b>{s.name}</b> · champs : {s.fields.join(', ')}
            <br />
            <small>Version {s.version}</small>
          </p>
        ))}
        <ul>
          {analysis.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
        <p>
          Statut : {analysis.status} ·{' '}
          {analysis.is_synthetic
            ? 'Données synthétiques'
            : 'Données configurées'}
        </p>
      </details>
      {onReport && (
        <button className="w-text-button" onClick={onReport}>
          Préparer une synthèse depuis ce résultat <span>↗</span>
        </button>
      )}
    </article>
  );
}
