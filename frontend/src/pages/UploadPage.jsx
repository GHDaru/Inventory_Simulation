import { useRef, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  Stack,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { uploadDataset } from '../api/api';

export default function UploadPage() {
  const inputRef = useRef(null);
  const [column, setColumn] = useState('demand');
  const [status, setStatus] = useState(null); // null | 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('');
  const [datasetMeta, setDatasetMeta] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  async function handleFile(file) {
    if (!file) return;

    // Validate file type
    const accepted = ['.csv', '.xlsx', '.xls', '.json'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!accepted.includes(ext)) {
      setStatus('error');
      setMessage(`Tipo de arquivo não suportado: ${ext}. Aceitos: ${accepted.join(', ')}`);
      return;
    }

    setStatus('loading');
    setMessage('');
    setDatasetMeta(null);
    try {
      const result = await uploadDataset(file, column);
      setStatus('success');
      setMessage(`Dataset enviado com sucesso!`);
      setDatasetMeta(result);
      // Save as active dataset in sessionStorage for ConfigPage to pick up
      sessionStorage.setItem('activeDatasetId', result.id);
      sessionStorage.setItem('activeDatasetName', result.filename);
    } catch (err) {
      setStatus('error');
      setMessage(`Erro: ${err.message}`);
    }
  }

  function onInputChange(e) {
    handleFile(e.target.files?.[0]);
  }

  function onDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <Box sx={{ maxWidth: 640, mx: 'auto', mt: 2 }}>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Upload de Dados
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Envie um arquivo CSV, Excel (.xlsx/.xls) ou JSON com dados históricos de demanda.
        O dataset ficará disponível para uso nas simulações.
      </Typography>

      <Paper sx={{ p: 3, mb: 2 }}>
        <TextField
          label="Nome da coluna de demanda"
          value={column}
          onChange={e => setColumn(e.target.value)}
          size="small"
          sx={{ mb: 2, width: 260 }}
          placeholder="demand"
        />

        {/* Drop zone */}
        <Box
          onDrop={onDrop}
          onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onClick={() => inputRef.current?.click()}
          sx={{
            border: '2px dashed',
            borderColor: isDragging ? 'primary.main' : 'grey.400',
            borderRadius: 2,
            p: 5,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragging ? 'action.hover' : 'background.default',
            transition: 'all 0.15s',
            '&:hover': { bgcolor: 'action.hover', borderColor: 'primary.light' },
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            style={{ display: 'none' }}
            onChange={onInputChange}
          />
          {status === 'loading' ? (
            <CircularProgress size={32} />
          ) : (
            <>
              <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="body1" gutterBottom>
                Arraste e solte um arquivo aqui, ou clique para selecionar
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Formatos aceitos: CSV, XLSX, XLS, JSON · Tamanho máximo: 50 MB
              </Typography>
            </>
          )}
        </Box>

        <Box mt={2} display="flex" justifyContent="flex-end">
          <Button
            variant="contained"
            startIcon={<CloudUploadIcon />}
            onClick={() => inputRef.current?.click()}
            disabled={status === 'loading'}
          >
            Selecionar arquivo
          </Button>
        </Box>
      </Paper>

      {/* Status messages */}
      {status === 'error' && (
        <Alert severity="error" sx={{ mb: 2 }}>{message}</Alert>
      )}

      {status === 'success' && datasetMeta && (
        <Paper sx={{ p: 3 }}>
          <Stack direction="row" alignItems="center" spacing={1} mb={2}>
            <CheckCircleIcon color="success" />
            <Typography variant="subtitle1" fontWeight={600}>
              {message}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip label={`ID: ${datasetMeta.id.slice(0, 8)}…`} size="small" />
            <Chip label={`Arquivo: ${datasetMeta.filename}`} size="small" />
            <Chip label={`Coluna: ${datasetMeta.column}`} size="small" />
            <Chip label={`${datasetMeta.rows} registros`} size="small" color="primary" />
            <Chip label={`Média: ${datasetMeta.mean?.toFixed(2)}`} size="small" />
            <Chip label={`Desvio: ${datasetMeta.std_dev?.toFixed(2)}`} size="small" />
          </Stack>
          <Alert severity="info" sx={{ mt: 2 }}>
            Dataset definido como ativo. Vá para{' '}
            <strong>Configuração de Simulação</strong> para usá-lo.
          </Alert>
        </Paper>
      )}
    </Box>
  );
}
