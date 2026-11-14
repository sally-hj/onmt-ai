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
  const compare = analysis.values.current !== undefined;
  const points = compare
    ? [
        {
          label: analysis.comparison_period?.start.slice(0, 7) || 'Référence',
          value: analysis.values.previous,
          kind: 'observed',
        },
        {
          label: analysis.period.start.slice(0, 7),
          value: analysis.values.current,
          kind: 'observed',
        },
      ]
    : analysis.series.map((p) => ({
        label: p.date.slice(0, 7),
        value: p.value,
        kind: p.kind,
      }));
  const valid = points.filter(
    (p): p is { label: string; value: number; kind: string } => p.value != null,
  );
  if (!valid.length)
    return (
      <p className="w-muted">Aucune série disponible pour ce périmètre.</p>
    );
  const max = Math.max(...valid.map((p) => p.value), 1),
    baseline = 172,
    width = 620,
    step = (width - 80) / Math.max(valid.length, 1);
  const y = (v: number) => baseline - (v / max) * 130;
  return (
    <figure className="w-chart">
      <svg
        viewBox="0 0 620 215"
        role="img"
        aria-label={`${metricNames[analysis.metric_id] || analysis.metric_id}, ${analysis.unit}, ${valid.length} points calculés`}
      >
        {[0, 0.5, 1].map((t) => (
          <g key={t}>
            <line
              x1="45"
              x2="610"
              y1={y(max * t)}
              y2={y(max * t)}
              stroke="#e8e5dc"
              strokeDasharray={t ? '3 5' : undefined}
            />
            <text x="4" y={y(max * t) + 4} fontSize="10" fill="#697972">
              {formatNumber(max * t)}
            </text>
          </g>
        ))}
        {valid.length <= 12 ? (
          valid.map((p, i) => (
            <g key={p.label}>
              <rect
                tabIndex={0}
                x={60 + i * step}
                y={y(p.value)}
                width={Math.max(8, step * 0.6)}
                height={baseline - y(p.value)}
                rx="5"
                fill={i === valid.length - 1 ? '#b65b42' : '#226556'}
                opacity={p.kind === 'forecast' ? 0.5 : 1}
              >
                <title>
                  {p.label} : {formatNumber(p.value)} {analysis.unit}
                  {p.kind === 'forecast' ? ' · prévision' : ''}
                </title>
              </rect>
              <text
                x={60 + i * step + step * 0.3}
                y="196"
                textAnchor="middle"
                fontSize="11"
                fill="#697972"
              >
                {p.label}
              </text>
            </g>
          ))
        ) : (
          <>
            <polyline
              fill="none"
              stroke="#226556"
              strokeWidth="2.5"
              points={valid
                .map(
                  (p, i) =>
                    `${55 + (i * 540) / (valid.length - 1)},${y(p.value)}`,
                )
                .join(' ')}
            />
            {valid.map((p, i) => (
              <circle
                key={p.label}
                tabIndex={0}
                cx={55 + (i * 540) / (valid.length - 1)}
                cy={y(p.value)}
                r={p.kind === 'forecast' ? 3 : 2}
                fill={p.kind === 'forecast' ? '#b65b42' : '#226556'}
              >
                <title>
                  {p.label} : {formatNumber(p.value)} {analysis.unit} · {p.kind}
                </title>
              </circle>
            ))}
            <text x="55" y="196" fontSize="11" fill="#697972">
              {valid[0].label}
            </text>
            <text x="535" y="196" fontSize="11" fill="#697972">
              {valid[valid.length - 1].label}
            </text>
          </>
        )}
      </svg>
      <figcaption>
        {compare ? 'Comparaison des périodes' : 'Évolution mensuelle'} ·{' '}
        {analysis.unit}
        {valid.some((p) => p.kind === 'forecast')
          ? ' · Prévisions distinguées en terre cuite'
          : ''}
      </figcaption>
      {analysis.series.some((p) => p.kind === 'forecast') && (
        <details className="w-proof">
          <summary>Prévisions et bornes empiriques</summary>
          <p>
            Ces bornes viennent des erreurs observées hors entraînement. Leur
            couverture n’est pas garantie.
          </p>
          <table className="w-forecast-table">
            <thead>
              <tr>
                <th>Mois</th>
                <th>Prévision</th>
                <th>Borne basse</th>
                <th>Borne haute</th>
              </tr>
            </thead>
            <tbody>
              {analysis.series
                .filter((p) => p.kind === 'forecast')
                .map((p) => (
                  <tr key={p.date}>
                    <td>{p.date.slice(0, 7)}</td>
                    <td>{formatNumber(p.value)}</td>
                    <td>{formatNumber(p.lower)}</td>
                    <td>{formatNumber(p.upper)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </details>
      )}
    </figure>
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
