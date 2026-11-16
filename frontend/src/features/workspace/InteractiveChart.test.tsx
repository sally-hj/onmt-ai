// Vérification du composant avec données d'entrée explicites ; aucune inférence IA.
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import { InteractiveChart } from './InteractiveChart';
import type { AnalysisResult } from '../reports/types';
afterEach(cleanup);
const analysis: AnalysisResult = {
  request_id: 'r',
  analysis_id: 'a',
  metric_id: 'campaign_roi',
  status: 'ok',
  period: { start: '2025-01-01', end: '2025-01-31' },
  comparison_period: null,
  filters: { destination: 'Agadir' },
  unit: '%',
  values: {},
  series: [
    {
      date: '2025-01-01',
      value: -20,
      kind: 'observed',
      lower: null,
      upper: null,
    },
    { date: '2025-02-01', value: -10, kind: 'forecast', lower: -30, upper: 10 },
  ],
  formula: 'ROI',
  sources: [],
  warnings: ['synthetic_data'],
  is_synthetic: true,
};
it('permet de sélectionner les prévisions et de lire une valeur au clavier', () => {
  render(<InteractiveChart analysis={analysis} />);
  expect(
    screen.getByRole('img', { name: /2 points calculés/ }),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Séries'), {
    target: { value: 'forecast' },
  });
  expect(
    screen.getByRole('img', { name: /1 points calculés/ }),
  ).toBeInTheDocument();
  fireEvent.focus(screen.getByRole('img', { name: /2025-02-01 : -10/ }));
  expect(screen.getByRole('status')).toHaveTextContent('2025-02-01 : -10');
});
it('signale une sélection sans points sans remplacer les valeurs absentes par zéro', () => {
  render(<InteractiveChart analysis={analysis} />);
  fireEvent.change(screen.getByLabelText('Depuis'), {
    target: { value: '2030-01' },
  });
  expect(
    screen.getByText('Aucune donnée pour cette sélection.'),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('img', { name: /points calculés/ }),
  ).not.toBeInTheDocument();
});
