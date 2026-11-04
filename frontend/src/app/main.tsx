import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ReportsPage } from '../features/reports/ReportsPage';
import '../features/reports/reports.css';

createRoot(document.getElementById('root')!).render(<StrictMode><ReportsPage /></StrictMode>);
