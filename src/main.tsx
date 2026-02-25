import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DataProvider } from './context/DataContext';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <DataProvider>
      <App />
    </DataProvider>
  </StrictMode>,
);
