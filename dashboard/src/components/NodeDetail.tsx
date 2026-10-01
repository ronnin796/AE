import { useState } from "react";
import { Node, TelemetryStats } from "../types";
import { shutdownNode, sendNodeCommand } from "../api/client";

interface NodeDetailProps {
  node: Node;
  stats?: TelemetryStats | null;
}

const statusColor = {
  online: "bg-green-500",
  offline: "bg-red-500",
  degraded: "bg-yellow-500",
  maintenance: "bg-blue-500",
};

const statusDotClass = {
  online: "online",
  offline: "offline",
  degraded: "degraded",
  maintenance: "maintenance",
};

const formatBytes = (bytes?: number) => {
  if (!bytes) return "Not available";
  const gb = bytes / 1024 / 1024 / 1024;
  return `${gb.toFixed(2)} GB`;
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

export default function NodeDetail({ node, stats }: NodeDetailProps) {
  const statusClass = statusColor[node.status] || "bg-gray-500";
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleAction = async (command: string, params: Record<string, any> = {}) => {
    setActionLoading(command);
    setActionResult(null);
    try {
      let result;
      if (command === "shutdown") {
        result = await shutdownNode(node.node_id);
      } else {
        result = await sendNodeCommand(node.node_id, command, params);
      }
      setActionResult({ success: true, message: result.message || `Command ${command} sent successfully` });
    } catch (error: any) {
      setActionResult({ 
        success: false, 
        message: error.response?.data?.detail || error.message || "Failed to send command" 
      });
    } finally {
      setActionLoading(null);
    }
  };

  const canControl = node.status === "online";

  return (
    <div className="node-detail">
      <div className="detail-header">
        <div className="detail-header-main">
          <h2>{node.hostname}</h2>
          <span className={`status-badge ${statusClass}`}>
            {node.status.toUpperCase()}
          </span>
        </div>
        <div className="detail-header-meta">
          <span className="node-id">{node.node_id}</span>
          <span className="last-seen">
            Last heartbeat: {formatTimeAgo(node.last_seen)}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="detail-actions">
        <button 
          className={`action-btn ${canControl ? "btn-danger" : "btn-disabled"}`}
          onClick={() => handleAction("shutdown")}
          disabled={!canControl || actionLoading === "shutdown"}
        >
          {actionLoading === "shutdown" ? "Sending..." : "⏻ Shutdown Node"}
        </button>
        <button 
          className={`action-btn ${canControl ? "btn-warning" : "btn-disabled"}`}
          onClick={() => handleAction("reboot")}
          disabled={!canControl || actionLoading === "reboot"}
        >
          {actionLoading === "reboot" ? "Sending..." : "⟳ Reboot Node"}
        </button>
        <button 
          className={`action-btn ${canControl ? "btn-info" : "btn-disabled"}`}
          onClick={() => handleAction("update_telemetry_interval", { interval: 5 })}
          disabled={!canControl || actionLoading === "update_telemetry_interval"}
        >
          {actionLoading === "update_telemetry_interval" ? "Sending..." : "📊 Telemetry: 5s"}
        </button>
        <button 
          className={`action-btn ${canControl ? "btn-info" : "btn-disabled"}`}
          onClick={() => handleAction("update_heartbeat_interval", { interval: 30 })}
          disabled={!canControl || actionLoading === "update_heartbeat_interval"}
        >
          {actionLoading === "update_heartbeat_interval" ? "Sending..." : "💓 Heartbeat: 30s"}
        </button>
      </div>

      {actionResult && (
        <div className={`action-result ${actionResult.success ? "success" : "error"}`}>
          {actionResult.message}
        </div>
      )}

      <div className="detail-sections">
        <section className="detail-section">
          <h3>System Information</h3>
          <dl className="detail-grid">
            <div><dt>Hostname</dt><dd>{node.hostname}</dd></div>
            <div><dt>Operating System</dt><dd>{node.os} {node.os_version || ""}</dd></div>
            <div><dt>Kernel Version</dt><dd>{node.kernel_version || "Not available"}</dd></div>
            <div><dt>Architecture</dt><dd>{node.arch || "Not available"}</dd></div>
            <div><dt>CPU</dt><dd>{node.cpu_brand || "Not available"} ({node.cpu_cores || "?"} cores)</dd></div>
            <div><dt>Total Memory</dt><dd>{formatBytes(node.total_memory)}</dd></div>
            <div><dt>AetherEdge Version</dt><dd>{node.version || "Not available"}</dd></div>
            <div><dt>Node ID</dt><dd className="monospace">{node.node_id}</dd></div>
            <div><dt>Database ID</dt><dd>#{node.id}</dd></div>
          </dl>
        </section>

        <section className="detail-section">
          <h3>Communication</h3>
          <dl className="detail-grid">
            <div>
              <dt>Connection Status</dt>
              <dd>
                <span className="status-indicator">
                  <span className={`status-dot ${statusDotClass[node.status] || "offline"}`}></span>
                  <span className="status-text">{node.status.toUpperCase()}</span>
                </span>
              </dd>
            </div>
            <div><dt>Last Heartbeat</dt><dd>{new Date(node.last_seen).toLocaleString()} ({formatTimeAgo(node.last_seen)})</dd></div>
            <div><dt>Registered</dt><dd>{new Date(node.created_at).toLocaleString()}</dd></div>
            <div><dt>Last Updated</dt><dd>{new Date(node.updated_at).toLocaleString()}</dd></div>
          </dl>
        </section>

        <section className="detail-section">
          <h3>Telemetry</h3>
          {stats && stats.count > 0 ? (
            <dl className="detail-grid">
              <div><dt>Data Points Collected</dt><dd>{stats.count}</dd></div>
              <div><dt>Avg CPU Usage</dt><dd>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "Not available"}</dd></div>
              <div><dt>Max CPU Usage</dt><dd>{stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "Not available"}</dd></div>
              <div><dt>Avg Memory Usage</dt><dd>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "Not available"}</dd></div>
              <div><dt>Max Memory Usage</dt><dd>{stats.max_memory ? `${stats.max_memory.toFixed(1)}%` : "Not available"}</dd></div>
              <div><dt>Avg Temperature</dt><dd>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "Not available"}</dd></div>
              <div><dt>Max Temperature</dt><dd>{stats.max_temperature ? `${stats.max_temperature.toFixed(1)}°C` : "Not available"}</dd></div>
              <div><dt>Latest Reading</dt><dd>{stats.latest_timestamp ? new Date(stats.latest_timestamp * 1000).toLocaleString() : "Not available"}</dd></div>
            </dl>
          ) : (
            <div className="empty-state">
              <h3>No Telemetry Data</h3>
              <p>Telemetry not available yet.</p>
              <p className="empty-hint">Node must send telemetry data first. This will be expanded in Part II.</p>
            </div>
          )}
        </section>

        {node.capabilities && node.capabilities.length > 0 && (
          <section className="detail-section">
            <h3>Capabilities</h3>
            <ul className="capabilities-list">
              {node.capabilities.map((cap) => (
                <li key={cap}>{cap}</li>
              ))}
            </ul>
          </section>
        )}

        <section className="detail-section">
          <h3>Available Commands</h3>
          <div className="commands-help">
            <div className="command-item">
              <span className="cmd-badge">shutdown</span>
              <span>Gracefully stops the edge node process</span>
            </div>
            <div className="command-item">
              <span className="cmd-badge">reboot</span>
              <span>Requests node to reboot (requires node support)</span>
            </div>
            <div className="command-item">
              <span className="cmd-badge">update_telemetry_interval</span>
              <span>Changes telemetry collection interval (seconds)</span>
            </div>
            <div className="command-item">
              <span className="cmd-badge">update_heartbeat_interval</span>
              <span>Changes heartbeat interval (seconds)</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}