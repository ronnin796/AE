import { TelemetryAggregated, TelemetryStats } from "../types";
import { useTelemetryStats } from "../hooks/useTelemetry";

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
  // Use passed stats or fetch if not provided
  const { data: fetchedStats, isLoading: statsLoading } = useTelemetryStats(nodeId);
  const telemetryStats = stats || fetchedStats;

  if (!telemetryStats || telemetryStats.count === 0) {
    return (
      <div className="telemetry-dashboard">
        <h2>Node {nodeId} Telemetry</h2>
        <div className="empty-state">
          <p>Telemetry not available yet.</p>
          <p className="empty-hint">This feature will be expanded in Part II.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="telemetry-dashboard">
      <h2>Node {nodeId} Telemetry</h2>

      <div className="dashboard-stats">
        <div className="stat-box">
          <h3>Telemetry Summary</h3>
          <div className="stat-grid">
            <div>
              <span>Avg CPU</span>
              <strong>{telemetryStats.avg_cpu ? `${telemetryStats.avg_cpu.toFixed(1)}%` : "Not available"}</strong>
            </div>
            <div>
              <span>Max CPU</span>
              <strong>{telemetryStats.max_cpu ? `${telemetryStats.max_cpu.toFixed(1)}%` : "Not available"}</strong>
            </div>
            <div>
              <span>Avg Memory</span>
              <strong>{telemetryStats.avg_memory ? `${telemetryStats.avg_memory.toFixed(1)}%` : "Not available"}</strong>
            </div>
            <div>
              <span>Max Memory</span>
              <strong>{telemetryStats.max_memory ? `${telemetryStats.max_memory.toFixed(1)}%` : "Not available"}</strong>
            </div>
            <div>
              <span>Avg Temperature</span>
              <strong>{telemetryStats.avg_temperature ? `${telemetryStats.avg_temperature.toFixed(1)}°C` : "Not available"}</strong>
            </div>
            <div>
              <span>Max Temperature</span>
              <strong>{telemetryStats.max_temperature ? `${telemetryStats.max_temperature.toFixed(1)}°C` : "Not available"}</strong>
            </div>
            <div>
              <span>Data Points</span>
              <strong>{telemetryStats.count}</strong>
            </div>
            <div>
              <span>Latest Reading</span>
              <strong>
                {telemetryStats.latest_timestamp
                  ? new Date(telemetryStats.latest_timestamp * 1000).toLocaleString()
                  : "Not available"}
              </strong>
            </div>
          </div>
        </div>

        {aggregatedTelemetry && aggregatedTelemetry.timestamps.length > 0 && (
          <div className="chart-summary">
            <h4>Latest Measurements</h4>
            <div className="latest-grid">
              <div>
                <span>CPU</span>
                <strong>
                  {getFirstValue(aggregatedTelemetry.cpu_usage) !== null
                    ? `${getFirstValue(aggregatedTelemetry.cpu_usage)!.toFixed(1)}%`
                    : "Not available"}
                </strong>
              </div>
              <div>
                <span>Memory</span>
                <strong>
                  {getFirstValue(aggregatedTelemetry.memory_usage) !== null
                    ? `${getFirstValue(aggregatedTelemetry.memory_usage)!.toFixed(1)}%`
                    : "Not available"}
                </strong>
              </div>
              <div>
                <span>Temp</span>
                <strong>
                  {getFirstValue(aggregatedTelemetry.temperature) !== null
                    ? `${getFirstValue(aggregatedTelemetry.temperature)!.toFixed(1)}°C`
                    : "Not available"}
                </strong>
              </div>
              <div>
                <span>Load</span>
                <strong>
                  {getFirstValue(aggregatedTelemetry.load_1) !== null
                    ? `${getFirstValue(aggregatedTelemetry.load_1)!.toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>
            </div>
            <p className="chart-hint">Charts coming in Part II</p>
          </div>
        )}
      </div>

      {statsLoading && !stats && (
        <p className="loading">Loading telemetry statistics...</p>
      )}
    </div>
  );
}