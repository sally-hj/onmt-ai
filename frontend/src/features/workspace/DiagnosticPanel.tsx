import { useState } from 'react';
import { formatNumber } from './AnalysisCard';
import { type Diagnostic, request } from './api';

export function DiagnosticResult({ data }: { data: Diagnostic }) {
  const [selected, setSelected] = useState('');
  const [indicator, setIndicator] = useState('arrivals');
  const rows = data.rows?.filter(
    (r) => !selected || r.destination === selected,
  );
  const points = data.points?.filter(
    (p) => !selected || (p.destination || p.market) === selected,
  );
  const labels =
    data.rows?.map((r) => r.destination) ||
    data.points?.map((p) => p.destination || p.market || '') ||
    [];
  const bcg = !!data.rows;
  const scatter = bcg || data.kind === 'value_volume';
  const plot = (rows || points || []).map((p) =>
    'indicators' in p
      ? {
          label: p.destination,
          x: p.relative_share,
          y: p.market_growth_pct,
          value: null,
        }
      : {
          label: p.destination || p.market || '',
          x: data.kind === 'map' ? p.longitude : p.volume,
          y: data.kind === 'map' ? p.latitude : p.value,
          value: p.value,
        },
  );
  const maxValue = Math.max(1, ...plot.map((p) => Math.abs(p.value ?? 0)));
  const xs = plot.map((p) => p.x).filter((n): n is number => n != null),
    ys = plot.map((p) => p.y).filter((n): n is number => n != null);
  const x0 = data.kind === 'map' ? -10 : 0,
    x1 = data.kind === 'map' ? -4 : Math.max(...xs, bcg ? 2 : 1) * 1.1;
  const y0 = data.kind === 'map' ? 30 : Math.min(0, ...ys) - 1,
    y1 = data.kind === 'map' ? 36.5 : Math.max(...ys, bcg ? 10 : 1) * 1.1;
  const x = (v: number) => 65 + ((v - x0) / (x1 - x0 || 1)) * 490,
    y = (v: number) => 285 - ((v - y0) / (y1 - y0 || 1)) * 235;
  const thresholdX = bcg ? 1 : data.thresholds?.volume_arrivals,
    thresholdY = bcg
      ? data.bcg?.growth_threshold_pct
      : data.thresholds?.value_mad_per_arrival;
  return (
    <section className="w-panel">
      <p className="w-synthetic">
        {data.synthetic
          ? 'Données synthétiques · simulation pédagogique'
          : 'Sources configurées'}
      </p>
      {labels.length > 0 && (
        <label>
          Afficher un périmètre
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">Tous</option>
            {labels.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      )}
      {(scatter || data.kind === 'map') && plot.length > 0 && (
        <figure>
          <div className="w-table-scroll">
            <svg
              className="w-diagnostic-chart"
              viewBox="0 0 620 350"
              role="img"
              aria-label={
                data.kind === 'map'
                  ? 'Carte ponctuelle, sans frontières administratives'
                  : 'Matrice analytique'
              }
            >
              <path d="M65 35V285H570" fill="none" stroke="#71897e" />
              {thresholdX !== undefined && (
                <line
                  x1={x(thresholdX)}
                  x2={x(thresholdX)}
                  y1="35"
                  y2="285"
                  stroke="#b65b42"
                  strokeDasharray="4 4"
                />
              )}
              {thresholdY !== undefined && (
                <line
                  x1="65"
                  x2="570"
                  y1={y(thresholdY)}
                  y2={y(thresholdY)}
                  stroke="#b65b42"
                  strokeDasharray="4 4"
                />
              )}
              {plot
                .filter((p) => p.x != null && p.y != null)
                .map((p) => (
                  <g key={p.label}>
                    <circle
                      tabIndex={0}
                      cx={x(p.x!)}
                      cy={y(p.y!)}
                      r={
                        data.kind === 'map'
                          ? Math.max(
                              3,
                              16 * Math.sqrt(Math.abs(p.value ?? 0) / maxValue),
                            )
                          : 8
                      }
                      fill="#226556"
                    >
                      <title>
                        {p.label} · x : {formatNumber(p.x)} · y :{' '}
                        {formatNumber(p.y)}
                        {data.kind === 'map'
                          ? ` · nuitées : ${formatNumber(p.value)}`
                          : ''}
                      </title>
                    </circle>
                    <text x={x(p.x!) + 11} y={y(p.y!) - 8} fontSize="12">
                      {p.label}
                    </text>
                  </g>
                ))}
              <text x="65" y="320" fontSize="12">
                {data.kind === 'map'
                  ? 'Longitude (°) / latitude (°) · coordonnées réelles'
                  : bcg
                    ? 'Part relative / croissance du marché (%)'
                    : 'Volume (arrivées) / valeur (MAD par arrivée)'}
              </text>
            </svg>
          </div>
          <figcaption>
            {data.kind === 'map'
              ? 'Positions urbaines réelles, indicateurs fictifs. Aucun fond de carte ni appel réseau.'
              : data.formula || data.bcg?.x + ' ; ' + data.bcg?.y}
          </figcaption>
        </figure>
      )}
      {data.rows && (
        <>
          <label>
            Indicateur du benchmark
            <select
              value={indicator}
              onChange={(e) => setIndicator(e.target.value)}
            >
              {Object.keys(data.units || {}).map((k) => (
                <option key={k}>{k}</option>
              ))}
            </select>
          </label>
          <div className="w-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Destination · données fictives</th>
                  <th>
                    {indicator} ({data.units?.[indicator]})
                  </th>
                  <th>Part relative</th>
                  <th>Croissance marché (%)</th>
                  <th>Quadrant</th>
                </tr>
              </thead>
              <tbody>
                {rows?.map((r) => (
                  <tr key={r.destination}>
                    <td>{r.destination}</td>
                    <td>{formatNumber(r.indicators[indicator])}</td>
                    <td>{formatNumber(r.relative_share)}</td>
                    <td>{formatNumber(r.market_growth_pct)}</td>
                    <td>{r.quadrant}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {data.points && (
        <div className="w-table-scroll">
          <table>
            <thead>
              <tr>
                <th>Périmètre</th>
                <th>Valeur</th>
                <th>Volume / coordonnées</th>
              </tr>
            </thead>
            <tbody>
              {points?.map((p) => (
                <tr key={p.destination || p.market}>
                  <td>{p.destination || p.market}</td>
                  <td>
                    {formatNumber(p.value)} {p.unit}
                  </td>
                  <td>
                    {p.volume ?? `${p.latitude ?? ''} / ${p.longitude ?? ''}`}{' '}
                    {p.quadrant}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data.stage && (
        <p>
          <strong>{data.stage}</strong> · {data.rule}
        </p>
      )}
      {data.kind === 'scenario' && (
        <p>
          Scénario : {formatNumber(data.baseline)} →{' '}
          <strong>
            {formatNumber(data.scenario_value)} {data.unit}
          </strong>{' '}
          · hypothèse {data.shock_pct} %. {data.formula}
        </p>
      )}
      <p>{data.comparability || data.interpretation}</p>
      <p>{data.warning || data.limit}</p>
    </section>
  );
}

export function DiagnosticPanel({ destinations }: { destinations: string[] }) {
  const [kind, setKind] = useState('bcg'),
    [destination, setDestination] = useState(''),
    [start, setStart] = useState('2025-02'),
    [end, setEnd] = useState('2025-02');
  const [threshold, setThreshold] = useState('5'),
    [value, setValue] = useState('2500'),
    [volume, setVolume] = useState('10000'),
    [shock, setShock] = useState('-10');
  const [data, setData] = useState<Diagnostic>(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const period = (s: string, e: string) => ({
    start: s + '-01',
    end: new Date(Date.UTC(Number(e.slice(0, 4)), Number(e.slice(5, 7)), 0))
      .toISOString()
      .slice(0, 10),
  });
  async function run() {
    setBusy(true);
    setError('');
    try {
      const p = period(start, end),
        comparison = period(
          String(Number(start.slice(0, 4)) - 1) + start.slice(4),
          String(Number(end.slice(0, 4)) - 1) + end.slice(4),
        );
      setData(
        await request<Diagnostic>(
          '/api/diagnostics',
          {
            kind,
            analysis: {
              request_id: crypto.randomUUID(),
              operation: 'value',
              metric_id: 'overnight_stays',
              period: p,
              comparison_period: comparison,
              filters: destination ? { destination } : {},
              language: 'fr',
              forecast_horizon: null,
              forecast_frequency: null,
            },
            growth_threshold: Number(threshold),
            value_threshold: Number(value),
            volume_threshold: Number(volume),
            shock_pct: Number(shock),
          },
          'POST',
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Diagnostic indisponible.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div>
      <form
        className="w-panel w-diagnostic-form"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <fieldset disabled={busy}>
          <legend>Diagnostics et comparaisons</legend>
          <label>
            Outil
            <select
              aria-label="Outil"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="bcg">BCG et benchmark international</option>
              <option value="bcg_regions">BCG des douze régions</option>
              <option value="value_volume">Valeur–Volume par marché</option>
              <option value="butler">
                Aide Butler (cinq années complètes)
              </option>
              <option value="map">Carte des nuitées</option>
              <option value="scenario">
                Scénario proportionnel sur les nuitées
              </option>
            </select>
          </label>
          <label>
            Destination interne
            <select
              aria-label="Destination interne"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            >
              <option value="">Tous les territoires autorisés</option>
              {destinations.map((d) => (
                <option key={d}>{d}</option>
              ))}
            </select>
          </label>
          <label>
            Premier mois
            <input
              type="month"
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            Dernier mois
            <input
              type="month"
              required
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
          {(kind === 'bcg' || kind === 'bcg_regions') && (
            <p>
              La BCG compare les mêmes mois de l’année précédente. Ses
              comparateurs partagés sont distincts des territoires internes.
            </p>
          )}
          {(kind === 'bcg' || kind === 'bcg_regions') && (
            <label>
              Seuil de croissance BCG (%)
              <input
                type="number"
                step="0.1"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
            </label>
          )}
          {kind === 'value_volume' && (
            <label>
              Seuil de valeur (MAD/arrivée)
              <input
                type="number"
                min="1"
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
            </label>
          )}
          {kind === 'value_volume' && (
            <label>
              Seuil de volume (arrivées)
              <input
                type="number"
                min="1"
                value={volume}
                onChange={(e) => setVolume(e.target.value)}
              />
            </label>
          )}
          {kind === 'scenario' && (
            <label>
              Hypothèse de variation (%)
              <input
                type="number"
                min="-90"
                max="100"
                step="0.1"
                required
                value={shock}
                onChange={(e) => setShock(e.target.value)}
              />
            </label>
          )}
          <button className="w-primary">
            {busy ? 'Calcul des sources…' : 'Calculer'}
          </button>
        </fieldset>
      </form>
      {error && (
        <p role="alert" className="w-error">
          {error}
        </p>
      )}
      {data && <DiagnosticResult data={data} />}
    </div>
  );
}
