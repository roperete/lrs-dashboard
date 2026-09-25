import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DataProvider } from './context/DataContext';
import App from './App.tsx';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import './index.css';

// A page opened before a new version was deployed asks for code files that no longer exist
// (each deploy renames them). Vite reports that as vite:preloadError: reload once to get the new
// version, at most once a minute, so a real outage does not loop.
window.addEventListener('vite:preloadError', (event) => {
  let last = 0;
  try { last = Number(sessionStorage.getItem('lrs-reloaded-at') || 0); } catch { /* storage blocked */ }
  if (Date.now() - last < 60_000) return;
  try { sessionStorage.setItem('lrs-reloaded-at', String(Date.now())); } catch { /* storage blocked */ }
  event.preventDefault();
  window.location.reload();
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary scope="the database">
      <DataProvider>
        <App />
      </DataProvider>
    </ErrorBoundary>
  </StrictMode>,
);
