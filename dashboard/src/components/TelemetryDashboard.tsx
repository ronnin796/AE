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

  return (
    <div className="panel telemetry-dashboard">
      <header className="panel-header">
        <h3 className="panel-title">Telemetry Summary</h3>
      </header>

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