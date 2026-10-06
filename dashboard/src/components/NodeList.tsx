import React, { useState, useMemo } from "react";
import { Node, TelemetryStats } from "../types";
import { useNodes, useOnlineNodes, useOfflineNodes } from "../hooks/useNodes";
import { useAllNodesTelemetrySummary } from "../hooks/useTelemetry";
import NodeCard from "./NodeCard";

interface NodeListProps {
  onSelect: (nodeId: string) => void;
}

export default function NodeList({ onSelect }: NodeListProps) {
  const { data: nodesData, isLoading, isError, refetch } = useNodes(1, 100);
  const { data: onlineNodes = [] } = useOnlineNodes();
  const { data: offlineNodes = [] } = useOfflineNodes();
  const { data: telemetrySummary, isLoading: isLoadingStats } = useAllNodesTelemetrySummary();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "online" | "offline" | "degraded" | "maintenance">("all");
  const [sortBy, setSortBy] = useState<"name" | "status" | "lastSeen">("name");

  const nodes = useMemo(() => {
    if (!nodesData) return [];

    let filtered = nodesData.nodes;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (node) =>
          node.hostname?.toLowerCase().includes(query) ||
          node.node_id.toLowerCase().includes(query) ||
          node.os?.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((node) => node.status === statusFilter);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "name":
          return (a.hostname || a.node_id).localeCompare(b.hostname || b.node_id);
        case "status":
          return a.status.localeCompare(b.status);
        case "lastSeen":
          return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
        default:
          return 0;
      }
    });

    return filtered;
  }, [nodesData, searchQuery, statusFilter, sortBy]);

  const totalNodes = nodesData?.total || 0;
  const onlineCount = onlineNodes.length;
  const offlineCount = offlineNodes.length;
  const degradedCount = nodesData?.nodes.filter((n) => n.status === "degraded").length || 0;

  if (isLoading && !nodesData) {
    return (
      <div className="node-list-container" role="status" aria-live="polite">
        <div className="skeleton skeleton-title" style={{ marginBottom: '1rem' }} />
        <div className="node-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="node-list-container">
        <div className="alert alert-danger" role="alert">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>
            <strong>Failed to load nodes</strong>
            <p>Unable to connect to the server. Please check your connection and try again.</p>
            <button className="btn btn-primary mt-2" onClick={() => refetch()}>Retry</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="node-list-container">
      <header className="node-list-header">
        <div className="node-list-title">
          <h2>Nodes</h2>
          <span className="node-count-badge">{totalNodes} total</span>
        </div>

        <div className="node-search" style={{ flex: 1, maxWidth: '400px' }}>
          <svg className="node-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="search"
            className="node-search-input"
            placeholder="Search nodes by name, ID, or OS..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search nodes"
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            className="input select"
            style={{ width: 'auto', minWidth: '140px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            aria-label="Filter by status"
          >
            <option value="all">All Statuses</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="degraded">Degraded</option>
            <option value="maintenance">Maintenance</option>
          </select>

          <select
            className="input select"
            style={{ width: 'auto', minWidth: '140px' }}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            aria-label="Sort by"
          >
            <option value="name">Sort by Name</option>
            <option value="status">Sort by Status</option>
            <option value="lastSeen">Sort by Last Seen</option>
          </select>

          <button className="btn btn-secondary" onClick={() => refetch()} aria-label="Refresh node list">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M23 4v6h-6" />
              <path d="M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
          </button>
        </div>
      </header>

      <div className="stats-grid" style={{ marginBottom: '1.5rem' }} role="region" aria-label="Node status summary">
        <div className="stat-card stat-card-primary">
          <div className="stat-label">Total Nodes</div>
          <div className="stat-value">{totalNodes}</div>
        </div>
        <div className="stat-card stat-card-success">
          <div className="stat-label">Online</div>
          <div className="stat-value">{onlineCount}</div>
        </div>
        <div className="stat-card stat-card-danger">
          <div className="stat-label">Offline</div>
          <div className="stat-value">{offlineCount}</div>
        </div>
        <div className="stat-card stat-card-warning">
          <div className="stat-label">Degraded</div>
          <div className="stat-value">{degradedCount}</div>
        </div>
      </div>

      {nodes.length > 0 ? (
        <div className="node-grid" role="list" aria-label="Node cards">
          {nodes.map((node) => {
            // Get telemetry stats for this node
            const stats = telemetrySummary?.nodes?.[node.node_id] || null;
            return (
              <NodeCard
                key={node.node_id}
                node={node}
                stats={stats}
                isLoadingStats={isLoadingStats}
                onSelect={onSelect}
              />
            );
          })}
        </div>
      ) : (
        <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
          <h3 className="empty-state-title">{searchQuery || statusFilter !== "all" ? "No matching nodes" : "No nodes registered"}</h3>
          <p className="empty-state-text">
            {searchQuery || statusFilter !== "all"
              ? "Try adjusting your search or filter criteria."
              : "Start edge nodes to see them appear here. Nodes register automatically on first connection."}
          </p>
        </div>
      )}
    </div>
  );
}