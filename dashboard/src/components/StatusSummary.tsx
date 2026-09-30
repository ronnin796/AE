import React from "react";
import { TelemetryStats } from "../types";

interface StatusSummaryProps {
  nodeId: string;
  stats?: TelemetryStats | null;
  isLoading: boolean;
}

export default function StatusSummary({ nodeId, stats, isLoading }: StatusSummaryProps) {
  if (!stats) {
    return (
      <div className="status-summary">
        <h3>Node {nodeId} Status</h3>
        <p>No telemetry data available yet.</p>
      </div>
    );
  }

  const status = stats.latest_timestamp
    ? "online"
    : "offline";

  return (
    <div className="status-summary">
      <h3>Node {nodeId} Status</h3>
      <div className="status-indicator">
        <span className={`status-dot ${status}`}></span>
        <span>{status.toUpperCase()}</span>
      </div>

      <div className="status-details">
        <div className="stat-item">
          <label>Data Points</label>
          <span>{stats.count}</span>
        </div>
        <div className="stat-item">
          <label>Latest Update</label>
          <span>
            {stats.latest_timestamp
              ? new Date(stats.latest_timestamp * 1000).toLocaleString()
              : "Never"}
          </span>
        </div>
      </div>

      {stats.avg_cpu || stats.avg_memory || stats.avg_temperature && (
        <div className="avg-metrics">
          <h4>Average Metrics</h4>
          <div className="metrics-grid">
            <div className="metric">
              <label>CPU Usage</label>
              <span>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}</span>
            </div>
            <div className="metric">
              <label>Memory Usage</span>
              <span>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}</span>
            </div>
            <div className="metric">
              <label>Temperature</label>
              <span>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}