import { Routes, Route, Navigate } from 'react-router-dom';
import AppShellLayout from './components/AppShellLayout';
import UploadPage from './pages/UploadPage';
import ConfigPage from './pages/ConfigPage';
import ResultsPage from './pages/ResultsPage';
import './App.css';

export default function App() {
  return (
    <AppShellLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/results/:runId" element={<ResultsPage />} />
      </Routes>
    </AppShellLayout>
  );
}

