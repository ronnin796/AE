import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { TelemetryAggregated, TelemetryStats } from '../types';

export function useAggregatedTelemetry(nodeId: string, points = 50) {
  return useQuery<TelemetryAggregated>({
    queryKey: ['telemetry', 'aggregated', nodeId, points],
    queryFn: () => api.getAggregatedTelemetry(nodeId, points),
    enabled: !!nodeId,
    refetchInterval: 5000,
  });
}

export function useTelemetryStats(nodeId: string) {
  return useQuery<TelemetryStats>({
    queryKey: ['telemetry', 'stats', nodeId],
    queryFn: () => api.getTelemetryStats(nodeId),
    enabled: !!nodeId,
    refetchInterval: 10000,
  });
}