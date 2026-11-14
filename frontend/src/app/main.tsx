import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ReportsPage } from '../features/reports/ReportsPage';
import { Workspace } from '../features/workspace/Workspace';

const legacy =
  new URLSearchParams(window.location.search).get('legacy') === '1';
if (legacy) void import('../features/reports/reports.css');
createRoot(document.getElementById('root')!).render(
  <StrictMode>{legacy ? <ReportsPage /> : <Workspace />}</StrictMode>,
);
