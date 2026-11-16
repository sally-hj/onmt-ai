import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Workspace } from './Workspace';
import { workspaceApi } from './api';
import { api } from '../reports/api';
import type { AnalysisResult } from '../reports/types';

vi.mock('./api', () => ({
  workspaceApi: {
    me: vi.fn(),
    catalog: vi.fn(),
    status: vi.fn(),
    analyses: vi.fn(),
    alerts: vi.fn(),
    send: vi.fn(),
    conversation: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    link: vi.fn(),
  },
}));
vi.mock('../reports/api', () => ({
  api: {
    list: vi.fn(),
    create: vi.fn(),
    read: vi.fn(),
    revise: vi.fn(),
    export: vi.fn(),
    download: vi.fn(),
  },
}));
const analysis: AnalysisResult = {
  request_id: 'r',
  analysis_id: 'ana_qvd',
  metric_id: 'overnight_stays',
  status: 'ok',
  period: { start: '2025-02-01', end: '2025-02-28' },
  comparison_period: { start: '2024-02-01', end: '2024-02-29' },
  filters: { destination: 'Agadir' },
  unit: 'nuitees',
  values: { current: 80000, previous: 100000, change_pct: -20 },
  series: [
    {
      date: '2025-02-01',
      value: 80000,
      kind: 'observed',
      lower: null,
      upper: null,
    },
  ],
  formula: 'SUM(nights)',
  sources: [
    {
      source_id: 'commercial',
      source_type: 'qvd',
      name: 'commercial.qvd',
      version: 'v1',
      fields: ['nights'],
      pages: [],
    },
  ],
  warnings: ['synthetic_data'],
  is_synthetic: true,
};

beforeEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
  vi.mocked(workspaceApi.me).mockResolvedValue({
    user_id: 'direction',
    roles: ['report_editor'],
    allowed_modules: ['reports', 'commercial'],
    allowed_territories: ['Agadir', 'Marrakech'],
  });
  vi.mocked(workspaceApi.catalog).mockResolvedValue({
    label: 'Données synthétiques',
    synthetic: true,
    sources: [],
    relations: [],
  });
  vi.mocked(workspaceApi.status).mockResolvedValue({
    ollama_available: true,
    configured_model_available: true,
    generation_mode: 'ollama',
    ocr_enabled: true,
    tesseract_available: true,
    synthetic: true,
  });
  vi.mocked(workspaceApi.analyses).mockResolvedValue([]);
  vi.mocked(workspaceApi.alerts).mockResolvedValue([]);
  vi.mocked(api.list).mockResolvedValue([]);
});
afterEach(cleanup);

describe('Espace intégré', () => {
  it('conserve une question après une erreur du modèle sans afficher de résultat inventé', async () => {
    vi.mocked(workspaceApi.send).mockRejectedValue(
      new Error('Service Ollama inaccessible'),
    );
    render(<Workspace />);
    const input = await screen.findByLabelText('Votre question');
    fireEvent.change(input, {
      target: { value: 'Compare les nuitées à Agadir' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Envoyer la question' }),
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Service Ollama inaccessible',
    );
    expect(input).toHaveValue('Compare les nuitées à Agadir');
    expect(screen.queryByText('RÉSULTAT CALCULÉ')).not.toBeInTheDocument();
  });
  it('envoie la relance avec le bon identifiant et la version du contexte', async () => {
    vi.mocked(workspaceApi.send)
      .mockResolvedValueOnce({
        conversation_id: 'chat_qvd',
        version: 1,
        message: 'Analyse calculée',
        analysis,
      })
      .mockResolvedValueOnce({
        conversation_id: 'chat_qvd',
        version: 2,
        message: 'Marrakech calculé',
        analysis: {
          ...analysis,
          analysis_id: 'ana_marrakech',
          filters: { destination: 'Marrakech' },
        },
      });
    render(<Workspace />);
    const input = await screen.findByLabelText('Votre question');
    fireEvent.change(input, { target: { value: 'Compare Agadir' } });
    fireEvent.click(
      screen.getByRole('button', { name: 'Envoyer la question' }),
    );
    await screen.findByText('Analyse calculée');
    fireEvent.change(input, { target: { value: 'Et pour Marrakech ?' } });
    fireEvent.click(
      screen.getByRole('button', { name: 'Envoyer la question' }),
    );
    await screen.findByText('Marrakech calculé');
    expect(workspaceApi.send).toHaveBeenLastCalledWith(
      'Et pour Marrakech ?',
      'chat_qvd',
      1,
      'fr',
      expect.any(Function),
    );
    expect(localStorage.getItem('onmt-chat:direction')).toBe('chat_qvd');
    expect(screen.getAllByRole('img')[0]).toHaveAccessibleName(
      /Nuitées touristiques/,
    );
  });
  it('ne restaure pas une conversation que le serveur refuse', async () => {
    localStorage.setItem('onmt-chat:direction', 'chat_forbidden');
    vi.mocked(workspaceApi.conversation).mockRejectedValue(
      new Error('forbidden'),
    );
    render(<Workspace />);
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'ne peut plus être restaurée',
    );
    await waitFor(() =>
      expect(localStorage.getItem('onmt-chat:direction')).toBeNull(),
    );
  });
  it('affiche chaque périmètre d’une comparaison territoriale retournée par le serveur', async () => {
    vi.mocked(workspaceApi.send).mockResolvedValue({
      conversation_id: 'chat_bench',
      version: 1,
      message: 'Comparaison calculée',
      benchmark: [
        analysis,
        {
          ...analysis,
          analysis_id: 'ana_marrakech',
          filters: { destination: 'Marrakech' },
          values: { current: 165000, previous: 150000, change_pct: 10 },
        },
      ],
    });
    render(<Workspace />);
    const input = await screen.findByLabelText('Votre question');
    fireEvent.change(input, {
      target: { value: 'Compare Agadir et Marrakech' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Envoyer la question' }),
    );
    await screen.findByText('Comparaison calculée');
    expect(screen.getAllByText('RÉSULTAT CALCULÉ')).toHaveLength(2);
    expect(
      screen.getByText('Agadir', { selector: '.w-tag' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Marrakech', { selector: '.w-tag' }),
    ).toBeInTheDocument();
  });
});
