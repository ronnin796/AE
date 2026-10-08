import { TelemetryAggregated, TelemetryStats } from "../types";

interface TelemetryDashboardProps {
  nodeId: string;
  aggregatedTelemetry: TelemetryAggregated | undefined;
  stats?: TelemetryStats | null;
}

const getFirstValue = (arr: (number | null)[] | undefined): number | null => {
  if (!arr || arr.length === 0) return null;
  return arr[0] ?? null;
};

const formatTimeAgo = (dateString: string) => {
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

const formatRelativeTimeFromSeconds = (seconds: number) => {
  if (seconds < 60) return `${seconds}s ago`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

// Determine telemetry state using the best available timestamp source
const getTelemetryState = (
  stats: TelemetryStats | null | undefined,
  aggregatedTelemetry?: TelemetryAggregated,
  telemetryInterval: number = 2
) => {
  // Priority: aggregatedTelemetry (refetches every 5s, confirmed real-time) > stats (refetches every 10s)
  let latestTelemetryAt: number | undefined;

  if (aggregatedTelemetry && aggregatedTelemetry.timestamps.length > 0) {
    // timestamps are ordered DESC (newest first), so [0] is the latest
    latestTelemetryAt = aggregatedTelemetry.timestamps[0];
  } else if (stats?.latest_timestamp) {
    latestTelemetryAt = stats.latest_timestamp;
  }

  // No telemetry data at all
  if (!latestTelemetryAt) {
    return { state: 'waiting' as const, label: 'WAITING FOR TELEMETRY', details: 'Waiting for first telemetry...' };
  }

  // Has telemetry data - check freshness
  const latestTs = latestTelemetryAt * 1000; // Convert to ms
  const now = Date.now();
  const ageMs = now - latestTs;
  const ageSecs = Math.floor(ageMs / 1000);

  // Consider telemetry stale if older than 3x telemetry interval (default 2s -> 6s threshold)
  const staleThreshold = telemetryInterval * 3 * 1000; // ms

  if (ageMs > staleThreshold) {
    return {
      state: 'stale' as const,
      label: 'STALE TELEMETRY',
      details: `Last update: ${formatRelativeTimeFromSeconds(ageSecs)}`,
      ageSecs,
      latestTelemetryAt
    };
  }

  return {
    state: 'live' as const,
    label: 'LIVE TELEMETRY',
    details: `Updated ${formatRelativeTimeFromSeconds(ageSecs)}`,
    ageSecs,
    latestTelemetryAt
  };
};

export default function TelemetryDashboard({ nodeId, aggregatedTelemetry, stats }: TelemetryDashboardProps) {
  const telemetryStats = stats;

  if (!telemetryStats || telemetryStats.count === 0) {
    return (
      <div className="panel telemetry-dashboard">
        <h3 className="panel-title">Telemetry</h3>
        <div className="empty-state" style={{ padding: '1.5rem' }}>
          <h4 className="empty-state-title">No Telemetry Data</h4>
          <p className="empty-state-text">Select a node to view telemetry statistics.</p>
        </div>
      </div>
    );
  }

  // Get telemetry state using the best available timestamp
  const telemetryState = getTelemetryState(stats, aggregatedTelemetry);

  return (
    <div className="panel telemetry-dashboard">
      <header className="panel-header">
        <h3 className="panel-title">Telemetry Summary</h3>
      </header>

      {/* Telemetry status banner */}
      <div style={{
        marginBottom: '0.875rem',
        padding: '0.5rem 0.75rem',
        borderRadius: 'var(--radius)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        fontSize: '0.75rem',
        background: telemetryState.state === 'live' ? 'var(--accent-success-light)' :
                   telemetryState.state === 'stale' ? 'var(--accent-warning-light)' :
                   'var(--accent-info-light)',
        border: `1px solid ${telemetryState.state === 'live' ? 'var(--accent-success)' :
                                      telemetryState.state === 'stale' ? 'var(--accent-warning)' :
                                      'var(--accent-info)'}`
      }}>
        <span className={telemetryState.state === 'live' ? "status-dot online" :
                             telemetryState.state === 'stale' ? "status-dot degraded" :
                             "status-dot online"}
              style={{ width: '8px', height: '8px' }} />
        <span style={{ fontWeight: 600,
          color: telemetryState.state === 'live' ? 'var(--accent-success)' :
                 telemetryState.state === 'stale' ? 'var(--accent-warning)' :
                 'var(--accent-info)' }}>
          {telemetryState.label}
        </span>
        <span style={{ color: 'var(--text-secondary)' }}>
          {telemetryState.latestTelemetryAt ? (
            <>
              {telemetryState.details}
              {' | '}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                {new Date(telemetryState.latestTelemetryAt * 1000).toLocaleTimeString()}
              </span>
            </>
          ) : (
            telemetryState.details
          )}
        </span>
      </div>

      <div className="stats-grid" style={{ marginBottom: '0.875rem' }}>
        <div className="stat-card">
          <div className="stat-label">Data Points</div>
          <div className="stat-value">{telemetryStats.count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg CPU</div>
          <div className="stat-value">{telemetryStats.avg_cpu ? `${telemetryStats.avg_cpu.toFixed(1)}%` : "N/A"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Memory</div>
          <div className="stat-value">{telemetryStats.avg_memory ? `${telemetryStats.avg_memory.toFixed(1)}%` : "N/A"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Temp</div>
          <div className="stat-value">{telemetryStats.avg_temperature ? `${telemetryStats.avg_temperature.toFixed(1)}°C` : "N/A"}</div>
        </div>
      </div>

      {aggregatedTelemetry && aggregatedTelemetry.timestamps.length > 0 && (
        <div className="chart-summary" style={{ paddingTop: '0.875rem', borderTop: '1px solid var(--border-primary)' }}>
          <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.625rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Latest Measurements
          </h4>
          <div className="latest-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '0.5rem' }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', textAlign: 'center', border: '1px solid var(--border-primary)', minWidth: 0 }}>
              <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>CPU</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                {getFirstValue(aggregatedTelemetry.cpu_usage) !== null ? `${getFirstValue(aggregatedTelemetry.cpu_usage)!.toFixed(1)}%` : "N/A"}
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', textAlign: 'center', border: '1px solid var(--border-primary)', minWidth: 0 }}>
              <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Memory</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--accent-success)' }}>
                {getFirstValue(aggregatedTelemetry.memory_usage) !== null ? `${getFirstValue(aggregatedTelemetry.memory_usage)!.toFixed(1)}%` : "N/A"}
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', textAlign: 'center', border: '1px solid var(--border-primary)', minWidth: 0 }}>
              <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Temp</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--accent-warning)' }}>
                {getFirstValue(aggregatedTelemetry.temperature) !== null ? `${getFirstValue(aggregatedTelemetry.temperature)!.toFixed(1)}°C` : "N/A"}
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: 'var(--radius)', textAlign: 'center', border: '1px solid var(--border-primary)', minWidth: 0 }}>
              <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Load</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--accent-info)' }}>
                {getFirstValue(aggregatedTelemetry.load_1) !== null ? `${getFirstValue(aggregatedTelemetry.load_1)!.toFixed(2)}` : "N/A"}
              </div>
            </div>
          </div>
          <p className="chart-hint" style={{ marginTop: '0.5rem', textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
            Click node for full charts
          </p>
        </div>
      )}

    </div>
  );
}