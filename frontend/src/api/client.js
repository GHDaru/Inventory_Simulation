import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

export async function runSimulation(payload) {
  const { data } = await api.post('/api/simulate', payload);
  return data;
}

export async function uploadFile(file, column = 'demand') {
  const form = new FormData();
  form.append('file', file);
  form.append('column', column);
  const { data } = await api.post('/api/upload', form);
  return data;
}

export async function checkHealth() {
  const { data } = await api.get('/api/health');
  return data;
}
