import { useQuery } from '@tanstack/react-query';
import { getAggregatedTelemetry, getAllNodesTelemetrySummary, getTelemetryStats, getDebugEvents } from '../api/client';
import { TelemetryAggregated, TelemetryStats, TelemetrySummary, DebugEventsResponse } from '../types';

export function useAggregatedTelemetry(nodeId: string, points = 50) {
  return useQuery<TelemetryAggregated>({
    queryKey: ['telemetry', 'aggregated', nodeId, points],
    queryFn: () => getAggregatedTelemetry(nodeId, points),
    enabled: !!nodeId,
    refetchInterval: 5000,
  });
}

export function useTelemetryStats(nodeId: string) {
  return useQuery<TelemetryStats>({
    queryKey: ['telemetry', 'stats', nodeId],
    queryFn: () => getTelemetryStats(nodeId),
    enabled: !!nodeId,
    refetchInterval: 10000,
  });
}

export function useAllNodesTelemetrySummary() {
  return useQuery<TelemetrySummary>({
    queryKey: ['telemetry', 'summary', 'all'],
    queryFn: () => getAllNodesTelemetrySummary(),
    refetchInterval: 5000,
  });
}

export function useDebugEvents(limit = 100, eventTypes?: string[], nodeId?: string) {
  return useQuery<DebugEventsResponse>({
    queryKey: ['debug', 'events', limit, eventTypes, nodeId],
    queryFn: () => getDebugEvents(limit, undefined, eventTypes, nodeId),
    refetchInterval: 5000,
  });
}