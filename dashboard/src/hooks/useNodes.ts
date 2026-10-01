import { useQuery } from '@tanstack/react-query';
import { getNodes, getNode, getOnlineNodes, getOfflineNodes } from '../api/client';
import { Node, NodeListResponse } from '../types';

export function useNodes(page = 1, pageSize = 20) {
  return useQuery<NodeListResponse>({
    queryKey: ['nodes', page, pageSize],
    queryFn: () => getNodes(page, pageSize),
    refetchInterval: 5000,
  });
}

export function useNode(nodeId: string) {
  return useQuery<Node>({
    queryKey: ['node', nodeId],
    queryFn: () => getNode(nodeId),
    refetchInterval: 10000,
  });
}

export function useOnlineNodes() {
  return useQuery<Node[]>({
    queryKey: ['online-nodes'],
    queryFn: () => getOnlineNodes(),
    refetchInterval: 5000,
  });
}

export function useOfflineNodes() {
  return useQuery<Node[]>({
    queryKey: ['offline-nodes'],
    queryFn: () => getOfflineNodes(),
    refetchInterval: 5000,
  });
}