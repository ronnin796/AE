import React from "react";
import { Node, TelemetryStats } from "../types";

interface NodeCardProps {
  node: Node;
  stats?: TelemetryStats | null;
  isLoadingStats?: boolean;
  onSelect: (nodeId: string) => void;
}

const formatBytes = (bytes?: number) => {
  if (!bytes) return "N/A";
  const gb = bytes / 1024 / 1024 / 1024;
  return `${gb.toFixed(2)} GB`;
};

const formatRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

const getTelemetryState = (node: Node, stats: TelemetryStats | null | undefined) => {
  const isOnline = node.status === "online";

  // No stats available (not loaded or no telemetry in DB)
  if (!stats || stats.count === 0) {
    if (isOnline) {
      return { state: 'waiting', label: 'WAITING', details: '' };
    } else {
      return { state: 'offline', label: 'OFFLINE', details: `Last seen: ${formatRelativeTime(node.last_seen)}` };
    }
  }

  // Has telemetry data - check freshness
  if (stats.latest_timestamp) {
    const latestTs = stats.latest_timestamp * 1000; // Convert to ms
    const now = Date.now();
    const ageMs = now - latestTs;
    const ageSecs = Math.floor(ageMs / 1000);

    // Consider telemetry stale if older than 3x telemetry interval (default 2s -> 6s threshold)
    const telemetryInterval = node.telemetry_interval || 2;
    const staleThreshold = telemetryInterval * 3 * 1000; // ms

    if (ageMs > staleThreshold) {
      return {
        state: 'stale',
        label: 'STALE',
        details: `Last update: ${formatRelativeTimeFromSeconds(ageSecs)} ago`,
        ageSecs
      };
    }

    return {
      state: 'live',
      label: 'LIVE',
      details: `Updated ${formatRelativeTimeFromSeconds(ageSecs)} ago`,
      ageSecs
    };
  }

  // Has stats but no timestamp (edge case)
  return { state: 'live', label: 'LIVE', details: 'Data available' };
};

const formatRelativeTimeFromSeconds = (seconds: number) => {
  if (seconds < 60) return `${seconds}s ago`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

export default function NodeCard({ node, stats, isLoadingStats, onSelect }: NodeCardProps) {
  const telemetryState = getTelemetryState(node, stats);

  return (
    <article
      className={`panel node-card ${node.status}`}
      onClick={() => onSelect(node.node_id)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(node.node_id); } }}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${node.hostname || node.node_id}`}
      data-node-id={node.node_id}
    >
      <header className="node-card-header">
        <h3 className="node-card-name" title={node.hostname || node.node_id}>
          {node.hostname || node.node_id}
        </h3>
        <span className={`status-label status-${node.status}`} style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginLeft: '0.75rem' }}>
          {telemetryState.label}
        </span>
      </header>

      <div className="node-card-body">
        <div className="node-card-field">
          <span className="node-card-field-label">Node ID</span>
          <span className="node-card-field-value truncate" title={node.node_id}>{node.node_id}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">OS</span>
          <span className="node-card-field-value">{node.os} {node.os_version || ""}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Kernel</span>
          <span className="node-card-field-value">{node.kernel_version || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Architecture</span>
          <span className="node-card-field-value">{node.arch || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">CPU</span>
          <span className="node-card-field-value">
            {node.cpu_brand || "Unknown"} ({node.cpu_cores || "?"} cores)
          </span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Total Memory</span>
          <span className="node-card-field-value">{formatBytes(node.total_memory)}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">AetherEdge Version</span>
          <span className="node-card-field-value">{node.version || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Status Since</span>
          <span className="node-card-field-value">
            {formatRelativeTime(node.last_seen)}
          </span>
        </div>
      </div>

      {!isLoadingStats && (
        <section className="node-card-telemetry" aria-label="Telemetry summary">
          <h4 className="node-card-telemetry-title">Telemetry</h4>

          {telemetryState.state === 'live' && stats && (
            <div className="node-card-metrics" role="list" aria-label="Key metrics">
              <div className="node-card-metric" role="listitem">
                <div className="node-card-metric-value">
                  {stats.avg_cpu !== undefined ? `${stats.avg_cpu.toFixed(1)}%` : "—"}
                </div>
                <div className="node-card-metric-label">Avg CPU</div>
              </div>
              <div className="node-card-metric" role="listitem">
                <div className="node-card-metric-value">
                  {stats.avg_memory !== undefined ? `${stats.avg_memory.toFixed(1)}%` : "—"}
                </div>
                <div className="node-card-metric-label">Avg Memory</div>
              </div>
              <div className="node-card-metric" role="listitem">
                <div className="node-card-metric-value">
                  {stats.avg_temperature !== undefined ? `${stats.avg_temperature.toFixed(1)}°C` : "—"}
                </div>
                <div className="node-card-metric-label">Avg Temp</div>
              </div>
              <div className="node-card-metric" role="listitem">
                <div className="node-card-metric-value">
                  {stats.latest_timestamp !== undefined ? `${(Date.now() / 1000 - stats.latest_timestamp).toFixed(0)}s ago` : "—"}
                </div>
                <div className="node-card-metric-label">Last Update</div>
              </div>
            </div>
          )}

          {telemetryState.state === 'stale' && stats && (
            <p className="node-card-stale-notice" style={{ fontSize: '0.7rem', color: 'var(--accent-warning)', textAlign: 'center', marginTop: '0.5rem' }}>
              STALE - {telemetryState.details}
            </p>
          )}

          {telemetryState.state === 'waiting' && (
            <p className="node-card-waiting" style={{ fontSize: '0.75rem', color: 'var(--accent-info)', textAlign: 'center' }}>
              WAITING for first telemetry data
            </p>
          )}

          {telemetryState.state === 'offline' && (
            <p className="node-card-offline" style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textAlign: 'center' }}>
              OFFLINE
            </p>
          )}
        </section>
      )}

      <footer className="node-card-footer">
        <div className="node-card-last-seen">
          <span className={`status-label status-${node.status}`} style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginRight: '0.5rem' }}>
            {telemetryState.state === 'offline' ? 'OFFLINE' : 'ONLINE'}
          </span>
          <span>Last seen: {formatRelativeTime(node.last_seen)}</span>
        </div>
      </footer>
    </article>
  );
}