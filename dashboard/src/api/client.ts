import axios from 'axios';
import { TelemetrySummary, DebugEventsResponse, DebugStats } from '../types';

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

export async function getAllNodesTelemetrySummary(): Promise<TelemetrySummary> {
  const response = await api.get('/telemetry/summary/all');
  return response.data;
}

export async function sendNodeCommand(nodeId: string, command: string, params: Record<string, any> = {}) {
  const response = await api.post(`/nodes/${nodeId}/command`, { command, params });
  return response.data;
}

export async function shutdownNode(nodeId: string) {
  const response = await api.post(`/nodes/${nodeId}/shutdown`);
  return response.data;
}

export async function disconnectNode(nodeId: string) {
  const response = await api.post(`/nodes/${nodeId}/disconnect`);
  return response.data;
}

export async function reconnectNode(nodeId: string) {
  const response = await api.post(`/nodes/${nodeId}/reconnect`);
  return response.data;
}

export async function deleteNode(nodeId: string) {
  const response = await api.delete(`/nodes/${nodeId}`);
  return response.data;
}

export async function debugNodeRegistry() {
  const response = await api.get('/nodes/debug/registry');
  return response.data;
}

// Debug API
export async function getDebugEvents(limit = 100, since?: string, eventTypes?: string[], nodeId?: string): Promise<DebugEventsResponse> {
  const params: Record<string, any> = { limit };
  if (since) params.since = since;
  if (eventTypes && eventTypes.length > 0) params.event_types = eventTypes;
  if (nodeId) params.node_id = nodeId;
  const response = await api.get('/debug/events', { params });
  return response.data;
}

export async function getDebugStats(): Promise<DebugStats> {
  const response = await api.get('/debug/stats');
  return response.data;
}

export async function getActiveConnections() {
  const response = await api.get('/debug/connections');
  return response.data;
}