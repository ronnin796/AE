import React from "react";
import { Node, TelemetryStats } from "../types";

interface NodeCardProps {
  node: Node;
  stats?: TelemetryStats | null;
  isLoadingStats?: boolean;
  onSelect: (nodeId: string) => void;
}

const statusColor = {
  online: "bg-green-500",
  offline: "bg-red-500",
  degraded: "bg-yellow-500",
  maintenance: "bg-blue-500",
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

const formatBytes = (bytes?: number) => {
  if (!bytes) return "Not available";
  const gb = bytes / 1024 / 1024 / 1024;
  return `${gb.toFixed(2)} GB`;
};

export default function NodeCard({ node, stats, isLoadingStats, onSelect }: NodeCardProps) {
  const statusClass = statusColor[node.status] || "bg-gray-500";
  const dotClass = statusClass.replace("bg-", "");

  return (
    <div className="node-card" onClick={() => onSelect(node.node_id)}>
      <div className="card-header">
        <h3>{node.hostname || node.node_id}</h3>
        <div className="card-status">
          <span className={`status-dot ${dotClass}`}></span>
          <span className="card-status-text">{node.status.toUpperCase()}</span>
        </div>
      </div>

      <dl className="node-info">
        <div>
          <dt>Node ID</dt>
          <dd>{node.node_id}</dd>
        </div>
        <div>
          <dt>OS</dt>
          <dd>{node.os} {node.os_version || ""}</dd>
        </div>
        <div>
          <dt>Kernel</dt>
          <dd>{node.kernel_version || "Not available"}</dd>
        </div>
        <div>
          <dt>CPU</dt>
          <dd>{node.cpu_brand || "Not available"} ({node.cpu_cores || "?"} cores)</dd>
        </div>
        <div>
          <dt>Total Memory</dt>
          <dd>{formatBytes(node.total_memory)}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{node.version || "Not available"}</dd>
        </div>
      </dl>

      {stats && stats.count > 0 && (
        <div className="telemetry-stats">
          <h4>Telemetry Summary</h4>
          <div className="stats-grid">
            <div>
              <span>Avg CPU</span>
              <strong>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}</strong>
            </div>
            <div>
              <span>Avg Memory</span>
              <strong>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}</strong>
            </div>
            <div>
              <span>Avg Temp</span>
              <strong>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}</strong>
            </div>
            <div>
              <span>Data Points</span>
              <strong>{stats.count}</strong>
            </div>
          </div>
        </div>
      )}

      {isLoadingStats && (
        <div className="loading-stats">Loading telemetry stats...</div>
      )}

      <div className="card-footer">
        <div className="heartbeat-info">
          <span className={`status-dot ${dotClass}`}></span>
          <span>Last heartbeat: {formatRelativeTime(node.last_seen)}</span>
        </div>
        <span className="view-hint">Click to view details →</span>
      </div>
    </div>
  );
}