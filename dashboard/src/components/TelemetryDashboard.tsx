import React from "react";
import { TelemetryAggregated, TelemetryStats } from "../types";
import { useTelemetryStats } from "../hooks";

interface TelemetryDashboardProps {
  nodeId: string;
  aggregatedTelemetry: TelemetryAggregated | undefined;
}

export default function TelemetryDashboard({ nodeId, aggregatedTelemetry }: TelemetryDashboardProps) {
  const { data: stats, isLoading: statsLoading } = useTelemetryStats(nodeId);

  return (
    <div className="telemetry-dashboard">
      <h2>Node {nodeId} Telemetry</h2>

      <div className="dashboard-stats">
        <div className="stat-box">
          <h3>Node Telemetry Summary</h3>
          {stats && (
            <div className="stat-grid">
              <div>
                <span>Avg CPU</span>
                <strong>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}</strong>
              </div>
              <div>
                <span>Avg Memory</span>
                <strong>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}</strong>
              </div>
              <div>
                <span>Avg Temperature</span>
                <strong>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}</strong>
              </div>
              <div>
                <span>Data Points</span>
                <strong>{stats.count}</strong>
              </div>
            </div>
          )}
        </div>

        {aggregatedTelemetry && (
          <div className="chart-summary">
            <h4>Latest Measurements</h4>
            <div className="latest-grid">
              <div>
                <span>CPU</span>
                <strong>{aggregatedTelemetry.cpu_usage?.[0] ? `${aggregatedTelemetry.cpu_usage[0].toFixed(1)}%` : "N/A"}</strong>
              </div>
              <div>
                <span>Memory</span>
                <strong>{aggregatedTelemetry.memory_usage?.[0] ? `${aggregatedTelemetry.memory_usage[0].toFixed(1)}%` : "N/A"}</strong>
              </div>
              <div>
                <span>Temp</span>
                <strong>{aggregatedTelemetry.temperature?.[0] ? `${aggregatedTelemetry.temperature[0].toFixed(1)}°C` : "N/A"}</strong>
              </div>
              <div>
                <span>Load</span>
                <strong>{aggregatedTelemetry.load_1?.[0] ? `${aggregatedTelemetry.load_1[0].toFixed(2)}` : "N/A"}</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {isLoadingStats && (
        <p>Loading telemetry statistics...</p>
      )}
    </div>
  );
}