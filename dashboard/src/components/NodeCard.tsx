import React from "react";
import { Node, TelemetryStats } from "../types";

interface NodeCardProps {
  node: Node;
  stats?: TelemetryStats | null;
  isLoadingStats: boolean;
}

export default function NodeCard({ node, stats, isLoadingStats }: NodeCardProps) {
  const statusColor = {
    online: "bg-green-500",
    offline: "bg-red-500",
    degraded: "bg-yellow-500",
    maintenance: "bg-blue-500",
  };

  const statusClass = statusColor[node.status] || "bg-gray-500";

  return (
    <div className="node-card">
      <div className="card-header">
        <h3>{node.hostname || node.node_id}</h3>
        <span className={`status-indicator ${statusClass}`}>
          {node.status.toUpperCase()}
        </span>
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
          <dd>{node.kernel_version || "N/A"}</dd>
        </div>
        <div>
          <dt>CPU</dt>
          <dd>{node.cpu_brand || "N/A"} ({node.cpu_cores || "?"} cores)</dd>
        </div>
        <div>
          <dt>Total Memory</dt>
          <dd>
            {node.total_memory
              ? `${(node.total_memory / 1024 / 1024 / 1024).toFixed(2)} GB`
              : "N/A"}
          </dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{node.version || "N/A"}</dd>
        </div>
        <div>
          <dt>Last Seen</dt>
          <dd>{new Date(node.last_seen).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Registered</dt>
          <dd>{new Date(node.created_at).toLocaleString()}</dd>
        </div>
      </dl>

      {stats && (
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
    </div>
  );
}
