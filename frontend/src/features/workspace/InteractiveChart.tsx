import { useState } from 'react';
import type { AnalysisResult } from '../reports/types';

const number = (value: number | null | undefined) =>
  value == null
    ? 'Indisponible'
    : new Intl.NumberFormat('fr-MA', { maximumFractionDigits: 2 }).format(
        value,
      );
export function InteractiveChart({
  analysis,
  label,
}: {
  analysis: AnalysisResult;
  label?: string;
}) {
  const [kind, setKind] = useState('all'),
    [from, setFrom] = useState(''),
    [to, setTo] = useState(''),
    [focus, setFocus] = useState('');
  const compare = analysis.values.current !== undefined;
  const all = compare
    ? [
        {
          date: analysis.comparison_period?.start || 'Référence',
          value: analysis.values.previous,
          kind: 'observed',
        },
        {
          date: analysis.period.start,
          value: analysis.values.current,
          kind: 'observed',
        },
      ]
    : analysis.series;
  const points = all.filter(
    (p) =>
      p.value != null &&
      (kind === 'all' || p.kind === kind) &&
      (!from || p.date.slice(0, 7) >= from) &&
      (!to || p.date.slice(0, 7) <= to),
  );
  const values = points.map((p) => p.value as number),
    low = Math.min(0, ...values),
    high = Math.max(0, ...values),
    span = high - low || 1;
  const y = (v: number) => 170 - ((v - low) / span) * 130,
    x = (i: number) => 65 + (i * 510) / Math.max(1, points.length - 1);
  const note = (p: (typeof all)[number]) =>
    `${p.date} : ${number(p.value)} ${analysis.unit} · ${p.kind === 'forecast' ? 'prévision' : 'observation'}`;
  return (
    <figure className="w-chart">
      <div className="w-chart-filters">
        <label>
          Séries
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="all">Observations et prévisions</option>
            <option value="observed">Observations</option>
            <option value="forecast">Prévisions</option>
          </select>
        </label>
        <label>
          Depuis
          <input
            type="month"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label>
          Jusqu’à
          <input
            type="month"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
      </div>
      {!points.length ? (
        <p>Aucune donnée pour cette sélection.</p>
      ) : (
        <svg
          viewBox="0 0 620 215"
          role="img"
          aria-label={`${label || analysis.metric_id}, ${analysis.unit}, ${points.length} points calculés`}
        >
          <line x1="45" x2="605" y1={y(0)} y2={y(0)} stroke="#71897e" />
          {[low, high].map((v, i) => (
            <text key={i} x="4" y={y(v) - 5} fontSize="11" fill="#556c63">
              {number(v)}
            </text>
          ))}
          {['observed', 'forecast'].map((series) => (
            <polyline
              key={series}
              fill="none"
              stroke={series === 'forecast' ? '#b65b42' : '#226556'}
              strokeDasharray={series === 'forecast' ? '5 4' : undefined}
              strokeWidth="2"
              points={points
                .map((p, i) => ({ p, i }))
                .filter(({ p }) => p.kind === series)
                .map(({ p, i }) => `${x(i)},${y(p.value!)}`)
                .join(' ')}
            />
          ))}
          {points.map((p, i) => (
            <g key={p.date + p.kind}>
              <circle
                tabIndex={0}
                role="img"
                aria-label={note(p)}
                onFocus={() => setFocus(note(p))}
                onMouseEnter={() => setFocus(note(p))}
                cx={x(i)}
                cy={y(p.value!)}
                r="5"
                fill={p.kind === 'forecast' ? '#b65b42' : '#226556'}
              >
                <title>{note(p)}</title>
              </circle>
              {(i === 0 || i === points.length - 1) && (
                <text x={x(i)} y="198" textAnchor="middle" fontSize="11">
                  {p.date.slice(0, 7)}
                </text>
              )}
            </g>
          ))}
        </svg>
      )}
      <figcaption>
        {compare ? 'Comparaison des périodes' : 'Évolution mensuelle'} ·{' '}
        {analysis.unit} · vert : observations ; terre cuite pointillée :
        prévisions.
      </figcaption>
      <p role="status">
        {focus || 'Survolez un point ou utilisez Tab pour consulter sa valeur.'}
      </p>
      <details className="w-proof">
        <summary>Valeurs et bornes accessibles</summary>
        <div className="w-table-scroll">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Nature</th>
                <th>Valeur</th>
                <th>Borne basse</th>
                <th>Borne haute</th>
              </tr>
            </thead>
            <tbody>
              {analysis.series.map((p) => (
                <tr key={p.date + p.kind}>
                  <td>{p.date}</td>
                  <td>{p.kind}</td>
                  <td>
                    {number(p.value)} {analysis.unit}
                  </td>
                  <td>{number(p.lower)}</td>
                  <td>{number(p.upper)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>Bornes empiriques des prévisions : couverture non garantie.</p>
      </details>
    </figure>
  );
}
