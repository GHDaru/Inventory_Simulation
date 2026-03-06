/**
 * Centralised fetch-based API client.
 * All functions throw an Error with a descriptive message on failure.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';

async function request(method, path, body, isFormData = false) {
  const headers = {};
  if (body && !isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const json = await res.json();
      detail = json.detail || JSON.stringify(json);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  // 204 No Content
  if (res.status === 204) return null;

  return res.json();
}

// ── Datasets ─────────────────────────────────────────────────────────────────

/** Upload a file as a new dataset. Returns DatasetMeta including id. */
export async function uploadDataset(file, column = 'demand') {
  const form = new FormData();
  form.append('file', file);
  form.append('column', column);
  return request('POST', '/api/datasets', form, true);
}

/** List all uploaded datasets. */
export async function listDatasets() {
  return request('GET', '/api/datasets');
}

// ── Runs ──────────────────────────────────────────────────────────────────────

/** List all simulation runs (summary). */
export async function listRuns() {
  return request('GET', '/api/runs');
}

/**
 * Create (and immediately queue) a new simulation run.
 * @param {{ name?: string, days: number, products: object[], dataset_id?: string }} payload
 */
export async function createRun(payload) {
  return request('POST', '/api/runs', payload);
}

/** Get metadata + config for a specific run. */
export async function getRun(runId) {
  return request('GET', `/api/runs/${runId}`);
}

/** Get results for a completed run. Returns { status, charts_data, metrics, ... } */
export async function getRunResults(runId) {
  return request('GET', `/api/runs/${runId}/results`);
}

// ── Legacy (kept for backward compatibility) ─────────────────────────────────

import axios from 'axios';

const _axiosApi = axios.create({ baseURL: BASE_URL || 'http://localhost:8000' });

export async function runSimulation(payload) {
  const { data } = await _axiosApi.post('/api/simulate', payload);
  return data;
}

/** @deprecated Use uploadDataset instead */
export async function uploadFile(file, column = 'demand') {
  const form = new FormData();
  form.append('file', file);
  form.append('column', column);
  const { data } = await _axiosApi.post('/api/upload', form);
  return data;
}

export async function checkHealth() {
  const { data } = await _axiosApi.get('/api/health');
  return data;
}
