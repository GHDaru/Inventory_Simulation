import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Button,
  Stack,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getRun, getRunResults } from '../api/api';
import ResultsView from '../components/ResultsView';

const POLL_INTERVAL_MS = 4000;

const STATUS_COLOR = {
  done: 'success',
  running: 'warning',
  created: 'default',
  failed: 'error',
};

function MetricCard({ label, value, unit = '' }) {
  return (
    <Card variant="outlined" sx={{ minWidth: 150, flex: 1 }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
          {label}
        </Typography>
        <Typography variant="h6" fontWeight={700}>
          {value}
          {unit && (
            <Typography component="span" variant="body2" color="text.secondary" ml={0.5}>
              {unit}
            </Typography>
          )}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function ResultsPage() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [results, setResults] = useState(null);
  const [loadError, setLoadError] = useState(null);

  // polling is derived from run status — no extra state needed
  const polling = run != null && (run.status === 'running' || run.status === 'created');

  const fetchAll = useCallback(async () => {
    try {
      const [runData, resultsData] = await Promise.all([
        getRun(runId),
        getRunResults(runId),
      ]);
      setRun(runData);
      setResults(resultsData);
      setLoadError(null);
      return runData.status;
    } catch (err) {
      setLoadError(err.message);
      return 'failed';
    }
  }, [runId]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Poll while running / created
  useEffect(() => {
    if (!run || (run.status !== 'running' && run.status !== 'created')) return;

    const id = setInterval(async () => {
      const status = await fetchAll();
      if (status !== 'running' && status !== 'created') {
        clearInterval(id);
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(id);
  }, [run, fetchAll]);

  // Build legacy results format for existing ResultsView component
  const legacyResults =
    results?.status === 'done' && results.charts_data
      ? {
          days: run?.config?.days,
          stock_history: results.charts_data.stock_history,
          daily_records: results.charts_data.daily_records,
        }
      : null;

  function handleDownload() {
    const payload = {
      run,
      results,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `run-${runId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loadError) {
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
        <Alert severity="error">{loadError}</Alert>
      </Box>
    );
  }

  if (!run) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const isActive = run.status === 'running' || run.status === 'created';

  return (
    <Box sx={{ maxWidth: 960, mx: 'auto', mt: 2 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" flexWrap="wrap" gap={2}>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" mb={0.5}>
              <Typography variant="h5" fontWeight={700}>
                {run.name}
              </Typography>
              <Chip
                label={run.status}
                size="small"
                color={STATUS_COLOR[run.status] || 'default'}
              />
              {polling && <CircularProgress size={16} />}
            </Stack>
            <Typography variant="body2" color="text.secondary">
              Criado em: {new Date(run.created_at).toLocaleString()}
            </Typography>
            {run.dataset_id && (
              <Typography variant="body2" color="text.secondary">
                Dataset ID: {run.dataset_id.slice(0, 8)}…
              </Typography>
            )}
            {run.config && (
              <Typography variant="body2" color="text.secondary">
                Horizonte: {run.config.days} dias · Produtos:{' '}
                {run.config.products?.map(p => p.name).join(', ')}
              </Typography>
            )}
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchAll}
            >
              Atualizar
            </Button>
            {results?.status === 'done' && (
              <Button
                variant="contained"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={handleDownload}
              >
                Baixar JSON (rodada completa)
              </Button>
            )}
          </Stack>
        </Stack>
      </Paper>

      {/* Running state */}
      {isActive && (
        <Alert severity="info" icon={<CircularProgress size={16} />} sx={{ mb: 3 }}>
          Simulação em andamento… atualizando automaticamente.
        </Alert>
      )}

      {/* Failed state */}
      {run.status === 'failed' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Simulação falhou: {run.error || 'Erro desconhecido.'}
        </Alert>
      )}

      {/* Metrics cards */}
      {results?.metrics && results.metrics.length > 0 && (
        <Box mb={3}>
          <Typography variant="subtitle1" fontWeight={600} mb={1}>
            Métricas por Produto
          </Typography>
          {results.metrics.map(m => (
            <Paper key={m.product} sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                {m.product}
              </Typography>
              <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
                <MetricCard label="Demanda total" value={m.total_demand} />
                <MetricCard label="Demanda não atendida" value={m.total_unmet_demand} />
                <MetricCard label="Dias de ruptura" value={m.stockout_days} unit="dias" />
                <MetricCard label="Nível de serviço" value={m.service_level_pct} unit="%" />
              </Stack>
            </Paper>
          ))}
        </Box>
      )}

      {/* Charts (reuse existing ResultsView component) */}
      {legacyResults && (
        <Paper sx={{ p: 3 }}>
          <ResultsView results={legacyResults} />
        </Paper>
      )}
    </Box>
  );
}
