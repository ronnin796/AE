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

const getStatusColor = (status: string) => {
  switch (status) {
    case "online": return "online";
    case "offline": return "offline";
    case "degraded": return "degraded";
    case "maintenance": return "maintenance";
    default: return "offline";
  }
};

export default function NodeCard({ node, stats, isLoadingStats, onSelect }: NodeCardProps) {
  const statusKey = getStatusColor(node.status);
  const isOnline = node.status === "online";

  return (
    <article
      className={`node-card ${node.status}`}
      onClick={() => onSelect(node.node_id)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(node.node_id); } }}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${node.hostname || node.node_id}`}
      data-node-id={node.node_id}
    >
      <header className="node-card-header">
        <div className="node-card-title">
          <div
            className={`status-dot ${statusKey}`}
            aria-hidden="true"
          />
          <h3 className="node-card-name" title={node.hostname || node.node_id}>
            {node.hostname || node.node_id}
          </h3>
        </div>
        <span className={`status-badge status-${node.status}`}>
          {node.status.toUpperCase()}
        </span>
      </header>

      <div className="node-card-body">
        <div className="node-card-field">
          <span className="node-card-field-label">Node ID</span>
          <span className="node-card-field-value truncate" title={node.node_id}>{node.node_id}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">OS</span>
          <span className="node-card-field-value truncate">{node.os} {node.os_version || ""}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Kernel</span>
          <span className="node-card-field-value truncate">{node.kernel_version || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Architecture</span>
          <span className="node-card-field-value truncate">{node.arch || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">CPU</span>
          <span className="node-card-field-value truncate">
            {node.cpu_brand || "Unknown"} ({node.cpu_cores || "?"} cores)
          </span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Total Memory</span>
          <span className="node-card-field-value">{formatBytes(node.total_memory)}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">AetherEdge Version</span>
          <span className="node-card-field-value truncate">{node.version || "N/A"}</span>
        </div>
        <div className="node-card-field">
          <span className="node-card-field-label">Status Since</span>
          <span className="node-card-field-value">
            {formatRelativeTime(node.last_seen)}
          </span>
        </div>
      </div>

      {(stats && stats.count > 0) && (
        <section className="node-card-telemetry" aria-label="Telemetry summary">
          <h4 className="node-card-telemetry-title">Telemetry Summary</h4>
          <div className="node-card-metrics" role="list" aria-label="Key metrics">
            <div className="node-card-metric" role="listitem">
              <div className="node-card-metric-value">
                {stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "—"}
              </div>
              <div className="node-card-metric-label">Avg CPU</div>
            </div>
            <div className="node-card-metric" role="listitem">
              <div className="node-card-metric-value">
                {stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "—"}
              </div>
              <div className="node-card-metric-label">Peak CPU</div>
            </div>
            <div className="node-card-metric" role="listitem">
              <div className="node-card-metric-value">
                {stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "—"}
              </div>
              <div className="node-card-metric-label">Avg Memory</div>
            </div>
            <div className="node-card-metric" role="listitem">
              <div className="node-card-metric-value">
                {stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "—"}
              </div>
              <div className="node-card-metric-label">Avg Temp</div>
            </div>
          </div>
        </section>
      )}

      {isLoadingStats && (
        <section className="node-card-telemetry" aria-label="Loading telemetry">
          <div className="skeleton skeleton-text short" style={{ margin: '0 auto' }} />
        </section>
      )}

      {!stats && !isLoadingStats && (
        <section className="node-card-telemetry" aria-label="No telemetry">
          <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textAlign: 'center' }}>
            No telemetry data yet
          </p>
        </section>
      )}

      <footer className="node-card-footer">
        <div className="node-card-last-seen">
          <span className={`status-dot ${statusKey}`} aria-hidden="true" />
          <span>Last seen: {formatRelativeTime(node.last_seen)}</span>
        </div>
        <span className="node-card-view-hint">Click for details →</span>
      </footer>
    </article>
  );
}