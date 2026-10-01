import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getNodes(page = 1, pageSize = 20) {
  const response = await api.get('/nodes', {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function getNode(nodeId: string) {
  const response = await api.get(`/nodes/${nodeId}`);
  return response.data;
}

export async function getOnlineNodes() {
  const response = await api.get('/nodes/status/online');
  return response.data;
}

export async function getOfflineNodes() {
  const response = await api.get('/nodes/status/offline');
  return response.data;
}

export async function getTelemetry(nodeId: string, limit = 100) {
  const response = await api.get(`/telemetry/node/${nodeId}`, {
    params: { limit },
  });
  return response.data;
}

export async function getAggregatedTelemetry(nodeId: string, points = 50) {
  const response = await api.get(`/telemetry/aggregated/${nodeId}`, {
    params: { points },
  });
  return response.data;
}

export async function getTelemetryStats(nodeId: string) {
  const response = await api.get(`/telemetry/stats/${nodeId}`);
  return response.data;
}