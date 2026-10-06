import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { TelemetryAggregated } from "../types";

interface TelemetryChartsProps {
  aggregatedTelemetry: TelemetryAggregated | undefined;
}

export function TelemetryCharts({ aggregatedTelemetry }: TelemetryChartsProps) {
  if (!aggregatedTelemetry || !aggregatedTelemetry.timestamps || aggregatedTelemetry.timestamps.length === 0) {
    return (
      <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
        <h3 className="empty-state-title">No Chart Data</h3>
        <p className="empty-state-text">Not enough telemetry data points to render charts.</p>
      </div>
    );
  }

  const chartData = aggregatedTelemetry.timestamps.map((timestamp, index) => ({
    time: new Date(timestamp * 1000).toLocaleTimeString(),
    timestamp,
    cpu: aggregatedTelemetry.cpu_usage[index] ?? null,
    memory: aggregatedTelemetry.memory_usage[index] ?? null,
    temperature: aggregatedTelemetry.temperature[index] ?? null,
    load: aggregatedTelemetry.load_1[index] ?? null,
  }));

  const hasCpuData = chartData.some(d => d.cpu !== null);
  const hasMemoryData = chartData.some(d => d.memory !== null);
  const hasTempData = chartData.some(d => d.temperature !== null);
  const hasLoadData = chartData.some(d => d.load !== null);

  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'var(--panel-bg)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius)',
          padding: '0.5rem 0.75rem',
          boxShadow: 'none',
          minWidth: '160px',
          fontSize: '0.75rem',
        }}>
          <p style={{ fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-primary)' }}>{label}</p>
          {payload.map((entry: any, i: number) => (
            <p key={i} style={{ color: entry.color, margin: '0.125rem 0', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: entry.color }} />
              <span>{entry.name}: </span>
              <strong>{entry.value !== null ? entry.value.toFixed(entry.name === 'load' ? 2 : 1) + (entry.name === 'temperature' ? '°C' : entry.name === 'load' ? '' : '%') : 'N/A'}</strong>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const chartColors = {
    cpu: 'var(--accent-primary)',
    memory: 'var(--accent-success)',
    temperature: 'var(--accent-warning)',
    load: 'var(--accent-info)',
  };

  return (
    <div className="telemetry-charts" role="region" aria-label="Telemetry charts">
      <div className="chart-row">
        {hasCpuData && (
          <div className="chart-container">
            <h3 className="chart-title">CPU Usage</h3>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  interval={Math.max(1, Math.floor(chartData.length / 8))}
                />
                <YAxis
                  domain={[0, 100]}
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}%`}
                  width={35}
                />
                <Tooltip content={customTooltip} />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke={chartColors.cpu}
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 1.5 }}
                  connectNulls={true}
                  name="CPU %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {hasMemoryData && (
          <div className="chart-container">
            <h3 className="chart-title">Memory Usage</h3>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  interval={Math.max(1, Math.floor(chartData.length / 8))}
                />
                <YAxis
                  domain={[0, 100]}
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}%`}
                  width={35}
                />
                <Tooltip content={customTooltip} />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke={chartColors.memory}
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 1.5 }}
                  connectNulls={true}
                  name="Memory %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="chart-row">
        {hasTempData && (
          <div className="chart-container">
            <h3 className="chart-title">Temperature</h3>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  interval={Math.max(1, Math.floor(chartData.length / 8))}
                />
                <YAxis
                  domain={[0, 'dataMax']}
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}°C`}
                  width={40}
                />
                <Tooltip content={customTooltip} />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke={chartColors.temperature}
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 1.5 }}
                  connectNulls={true}
                  name="Temperature"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {hasLoadData && (
          <div className="chart-container">
            <h3 className="chart-title">Load Average (1 min)</h3>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  interval={Math.max(1, Math.floor(chartData.length / 8))}
                />
                <YAxis
                  domain={[0, 'dataMax']}
                  stroke="var(--text-tertiary)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => value.toFixed(2)}
                  width={40}
                />
                <Tooltip content={customTooltip} />
                <Line
                  type="monotone"
                  dataKey="load"
                  stroke={chartColors.load}
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 1.5 }}
                  connectNulls={true}
                  name="Load (1m)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {(hasCpuData || hasMemoryData || hasTempData || hasLoadData) && (
        <p className="chart-hint" style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
          Showing {chartData.length} data points • Hover for details • Data from real /proc and /sys readings
        </p>
      )}
    </div>
  );
}