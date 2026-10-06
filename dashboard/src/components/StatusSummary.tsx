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
      <div className="panel status-summary">
        <h3 className="panel-title">Node Status</h3>
        <div className="empty-state" style={{ padding: '1.5rem' }}>
          <h4 className="empty-state-title">No Telemetry Data</h4>
          <p className="empty-state-text">Waiting for node {nodeId} to send telemetry...</p>
        </div>
      </div>
    );
  }

  const status = stats.latest_timestamp ? "online" : "offline";
  const lastUpdate = stats.latest_timestamp ? formatRelativeTime(stats.latest_timestamp) : "Never";

  return (
    <div className="panel status-summary">
      <header className="panel-header">
        <h3 className="panel-title">Node Status</h3>
      </header>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', padding: '0.75rem 1rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
        <span className={`status-dot ${status}`} style={{ width: '10px', height: '10px' }} />
        <span className="status-text" style={{ textTransform: 'uppercase', fontSize: '0.875rem' }}>{status.toUpperCase()}</span>
        <span className="last-update" style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
          Last update: {lastUpdate}
        </span>
      </div>

      <div className="stats-grid" style={{ marginBottom: '0.875rem' }}>
        <div className="stat-card">
          <div className="stat-label">Data Points</div>
          <div className="stat-value">{stats.count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Latest Reading</div>
          <div className="stat-value" style={{ fontSize: '1.125rem' }}>
            {stats.latest_timestamp ? new Date(stats.latest_timestamp * 1000).toLocaleTimeString() : "Never"}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '0.875rem' }}>
        <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Average Metrics
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.625rem' }}>
          <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
            <label style={{ display: 'block', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>CPU Usage</label>
            <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}
            </span>
          </div>
          <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
            <label style={{ display: 'block', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Peak CPU</label>
            <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "N/A"}
            </span>
          </div>
          <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
            <label style={{ display: 'block', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Memory Usage</label>
            <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}
            </span>
          </div>
          <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
            <label style={{ display: 'block', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Temperature</label>
            <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}
            </span>
          </div>
          <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-primary)' }}>
            <label style={{ display: 'block', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Peak Temp</label>
            <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.max_temperature ? `${stats.max_temperature.toFixed(1)}°C` : "N/A"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}