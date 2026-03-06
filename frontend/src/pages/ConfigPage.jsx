import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  CircularProgress,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  Divider,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import { listDatasets, createRun } from '../api/api';
import SimulationForm from '../components/SimulationForm';

export default function ConfigPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [runName, setRunName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Retrieve active dataset from sessionStorage (set by UploadPage)
  useEffect(() => {
    const active = sessionStorage.getItem('activeDatasetId');
    if (active) setSelectedDatasetId(active);
  }, []);

  useEffect(() => {
    listDatasets()
      .then(setDatasets)
      .catch(err => console.error('Failed to load datasets:', err));
  }, []);

  // Upload-page-uploaded data for SimulationForm (optional)
  const [uploadedData, setUploadedData] = useState(null);

  useEffect(() => {
    // When a dataset is selected, simulate uploadedData shape for SimulationForm
    if (selectedDatasetId) {
      const ds = datasets.find(d => d.id === selectedDatasetId);
      if (ds) {
        setUploadedData({
          rows: ds.rows,
          mean: ds.mean,
          std_dev: ds.std_dev,
          historical_data: null, // actual data is fetched by backend
        });
      }
    } else {
      setUploadedData(null);
    }
  }, [selectedDatasetId, datasets]);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    try {
      const run = await createRun({
        name: runName || undefined,
        days: payload.days,
        products: payload.products,
        dataset_id: selectedDatasetId || undefined,
      });
      navigate(`/results/${run.id}`);
    } catch (err) {
      setError(`Falha ao criar rodada: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 2 }}>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Configuração de Simulação
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Configure os parâmetros da simulação e crie uma nova rodada.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Informações da Rodada
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <TextField
            label="Nome da rodada (opcional)"
            value={runName}
            onChange={e => setRunName(e.target.value)}
            size="small"
            sx={{ flex: 1, minWidth: 220 }}
            placeholder="Ex.: Cenário base 2025"
          />
          <FormControl size="small" sx={{ flex: 1, minWidth: 220 }}>
            <InputLabel>Dataset</InputLabel>
            <Select
              value={selectedDatasetId}
              label="Dataset"
              onChange={e => setSelectedDatasetId(e.target.value)}
            >
              <MenuItem value="">
                <em>Nenhum (usar parâmetros manuais)</em>
              </MenuItem>
              {datasets.map(ds => (
                <MenuItem key={ds.id} value={ds.id}>
                  {ds.filename} — {ds.rows} registros
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              {selectedDatasetId
                ? 'Dados históricos serão injetados automaticamente'
                : 'Configure distribuições manualmente abaixo'}
            </FormHelperText>
          </FormControl>
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Reuse existing SimulationForm (no onSubmit — we handle it here) */}
        <SimulationForm
          onSubmit={handleSubmit}
          uploadedData={uploadedData}
          loading={loading}
          submitLabel="Criar e executar rodada"
        />

        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              Criando rodada…
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
