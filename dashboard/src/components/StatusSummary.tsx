import { TelemetryStats } from "../types";

interface StatusSummaryProps {
  nodeId: string;
  stats?: TelemetryStats | null;
}

const formatRelativeTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000);
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

export default function StatusSummary({ nodeId, stats }: StatusSummaryProps) {
  if (!stats || stats.count === 0) {
    return (
      <div className="status-summary">
        <h3>Node {nodeId} Status</h3>
        <div className="empty-state">
          <p>Telemetry not available yet.</p>
          <p className="empty-hint">Waiting for node telemetry...</p>
        </div>
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
        <span className="status-text">{status.toUpperCase()}</span>
        {stats.latest_timestamp && (
          <span className="last-update">Last update: {formatRelativeTime(stats.latest_timestamp)}</span>
        )}
      </div>

      <div className="status-details">
        <div className="stat-item">
          <label>Data Points Collected</label>
          <span>{stats.count}</span>
        </div>
        <div className="stat-item">
          <label>Latest Reading</label>
          <span>
            {stats.latest_timestamp
              ? `${new Date(stats.latest_timestamp * 1000).toLocaleString()} ({formatRelativeTime(stats.latest_timestamp)})`
              : "Never"}
          </span>
        </div>
      </div>

      <div className="avg-metrics">
        <h4>Average Metrics</h4>
        <div className="metrics-grid">
          <div className="metric">
            <label>CPU Usage</label>
            <span>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "Not available"}</span>
          </div>
          <div className="metric">
            <label>Max CPU</label>
            <span>{stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "Not available"}</span>
          </div>
          <div className="metric">
            <label>Memory Usage</label>
            <span>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "Not available"}</span>
          </div>
          <div className="metric">
            <label>Max Memory</label>
            <span>{stats.max_memory ? `${stats.max_memory.toFixed(1)}%` : "Not available"}</span>
          </div>
          <div className="metric">
            <label>Temperature</label>
            <span>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "Not available"}</span>
          </div>
          <div className="metric">
            <label>Max Temperature</label>
            <span>{stats.max_temperature ? `${stats.max_temperature.toFixed(1)}°C` : "Not available"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}