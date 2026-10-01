import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { TelemetryAggregated } from "../types";

interface TelemetryChartsProps {
  aggregatedTelemetry: TelemetryAggregated | undefined;
}

export default function TelemetryCharts({ aggregatedTelemetry }: TelemetryChartsProps) {
  if (!aggregatedTelemetry || !aggregatedTelemetry.timestamps || aggregatedTelemetry.timestamps.length === 0) {
    return <div className="charts-placeholder">No telemetry data available yet.</div>;
  }

  // Format data for recharts
  const chartData = aggregatedTelemetry.timestamps.map((timestamp, index) => ({
    time: new Date(timestamp * 1000).toLocaleTimeString(),
    cpu: aggregatedTelemetry.cpu_usage[index] || 0,
    memory: aggregatedTelemetry.memory_usage[index] || 0,
    temperature: aggregatedTelemetry.temperature[index] || 0,
    load: aggregatedTelemetry.load_1[index] || 0,
  }));

  return (
    <div className="telemetry-charts">
      <h2>Telemetry Data</h2>

      <div className="chart-row">
        <div className="chart-container">
          <h3>CPU Usage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Memory Usage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="memory" stroke="#10b981" strokeWidth={2} dot={false} />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-row">
        <div className="chart-container">
          <h3>Temperature</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={2} dot={false} />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Load Average (1min)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 'dataMax']} />
              <Tooltip />
              <Line type="monotone" dataKey="load" stroke="#a855f7" strokeWidth={2} dot={false} />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
