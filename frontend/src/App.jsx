import { useState } from 'react';
import SimulationForm from './components/SimulationForm';
import FileUpload from './components/FileUpload';
import ResultsView from './components/ResultsView';
import { runSimulation } from './api/client';
import './App.css';

export default function App() {
  const [uploadedData, setUploadedData] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSimulate(payload) {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await runSimulation(payload);
      setResults(data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setError(`Simulation failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📦 Inventory Simulation</h1>
        <p>Configure products, demand distributions, and replenishment policies to simulate stock levels.</p>
      </header>

      <main className="app-main">
        <section className="panel">
          <FileUpload onUpload={setUploadedData} />
        </section>

        <section className="panel">
          <h2>Simulation configuration</h2>
          <SimulationForm
            onSubmit={handleSimulate}
            uploadedData={uploadedData}
            loading={loading}
          />
          {error && <p className="error-message">{error}</p>}
        </section>

        {results && (
          <section className="panel">
            <ResultsView results={results} />
          </section>
        )}
      </main>
    </div>
  );
}
