import { useState } from "react";
import { Node, TelemetryStats } from "../types";
import { shutdownNode, sendNodeCommand, disconnectNode, reconnectNode } from "../api/client";
import { TelemetryCharts } from "./TelemetryCharts";
import { TelemetryAggregated } from "../types";
import { useAggregatedTelemetry } from "../hooks/useTelemetry";
import { useDebug } from "../context/DebugContext";

interface NodeDetailProps {
  node: Node;
  stats?: TelemetryStats | null;
}

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

const formatTimestamp = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString();
};

type TabId = "overview" | "telemetry" | "system" | "commands";

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6v6H9z"/></svg> },
  { id: "telemetry", label: "Telemetry", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M18 20V10M12 20V4M6 20v-6"/><path d="M2 20h20"/></svg> },
  { id: "system", label: "System", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg> },
  { id: "commands", label: "Commands", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg> },
];

export default function NodeDetail({ node, stats }: NodeDetailProps) {
  const statusKey = node.status;
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<{ success: boolean; message: string } | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [telemetryPoints, setTelemetryPoints] = useState(50);

  const { data: aggregatedTelemetry, refetch: refetchTelemetry } = useAggregatedTelemetry(node.node_id, telemetryPoints);
  const { addEvent } = useDebug();

  const canControl = node.status === "online";

  const handleAction = async (command: string, params: Record<string, any> = {}) => {
    setActionLoading(command);
    setActionResult(null);
    addEvent({ type: "command", node_id: node.node_id, message: `Sending command: ${command} ${JSON.stringify(params)}` });
    try {
      let result;
      if (command === "shutdown") {
        result = await shutdownNode(node.node_id);
      } else if (command === "disconnect") {
        result = await disconnectNode(node.node_id);
      } else if (command === "reconnect") {
        result = await reconnectNode(node.node_id);
      } else {
        result = await sendNodeCommand(node.node_id, command, params);
      }
      addEvent({ type: "command", node_id: node.node_id, message: `Command ${command} succeeded: ${result.message}` });
      setActionResult({ success: true, message: result.message || `Command ${command} sent successfully` });
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || "Failed to send command";
      addEvent({ type: "error", node_id: node.node_id, message: `Command ${command} failed: ${msg}` });
      setActionResult({
        success: false,
        message: msg,
      });
    } finally {
      setActionLoading(null);
    }
  };

  const commands = [
    { id: "shutdown", label: "Shutdown Node", icon: "⏻", variant: "danger" as const, confirm: true },
    { id: "reboot", label: "Reboot Node", icon: "⟳", variant: "warning" as const, confirm: true },
    { id: "disconnect", label: "Disconnect Node", icon: "🔌", variant: "danger" as const, confirm: true },
    { id: "reconnect", label: "Reconnect Node", icon: "🔄", variant: "info" as const, confirm: false },
    { id: "update_telemetry_interval", label: "Telemetry: 5s", icon: "📊", variant: "info" as const, params: { interval: 5 } },
    { id: "update_telemetry_interval", label: "Telemetry: 10s", icon: "📊", variant: "info" as const, params: { interval: 10 } },
    { id: "update_telemetry_interval", label: "Telemetry: 30s", icon: "📊", variant: "info" as const, params: { interval: 30 } },
    { id: "update_heartbeat_interval", label: "Heartbeat: 10s", icon: "💓", variant: "info" as const, params: { interval: 10 } },
    { id: "update_heartbeat_interval", label: "Heartbeat: 30s", icon: "💓", variant: "info" as const, params: { interval: 30 } },
    { id: "update_heartbeat_interval", label: "Heartbeat: 60s", icon: "💓", variant: "info" as const, params: { interval: 60 } },
  ];

  return (
    <div className="node-detail" role="main" aria-label={`Node details: ${node.hostname}`}>
      <header className="node-detail-header">
        <div className="node-detail-main">
          <h2 className="node-detail-name">{node.hostname}</h2>
          <span className={`status-badge status-${statusKey}`}>
            {statusKey.toUpperCase()}
          </span>
        </div>
        <div className="node-detail-meta">
          <span className="node-detail-id">{node.node_id}</span>
          <span className="last-seen">Last heartbeat: {formatTimeAgo(node.last_seen)}</span>
        </div>
      </header>

      <div className="node-detail-actions" role="group" aria-label="Node commands">
        {commands.map((cmd, idx) => (
          <button
            key={`${cmd.id}-${idx}`}
            className={`btn btn-${cmd.variant} ${!canControl ? "btn-disabled" : ""}`}
            onClick={() => {
              if (cmd.confirm && !window.confirm(`Are you sure you want to ${cmd.label.toLowerCase()}?`)) return;
              handleAction(cmd.id, cmd.params || {});
            }}
            disabled={!canControl || actionLoading === cmd.id}
            aria-disabled={!canControl || actionLoading === cmd.id}
          >
            {actionLoading === cmd.id ? (
              <span className="animate-pulse">Sending...</span>
            ) : (
              <>
                <span aria-hidden="true">{cmd.icon}</span>
                <span>{cmd.label}</span>
              </>
            )}
          </button>
        ))}
      </div>

      {actionResult && (
        <div className={`alert ${actionResult.success ? "alert-success" : "alert-danger"}`} role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            {actionResult.success ? (
              <>
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <path d="M22 4L12 14.01l-3-3" />
              </>
            ) : (
              <>
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </>
            )}
          </svg>
          <span>{actionResult.message}</span>
        </div>
      )}

      <nav className="node-detail-tabs" role="tablist" aria-label="Node detail sections">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            id={`tab-${tab.id}`}
            className={`node-detail-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
            disabled={!canControl && tab.id === "commands"}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
              {tab.icon}
              {tab.label}
            </span>
          </button>
        ))}
      </nav>

      <div className="tab-panels">
        <div
          role="tabpanel"
          id="panel-overview"
          aria-labelledby="tab-overview"
          hidden={activeTab !== "overview"}
          className="animate-fade-in"
        >
          <section className="node-detail-section" aria-labelledby="overview-title">
            <h3 id="overview-title" className="node-detail-section-title">Node Overview</h3>
            <dl className="detail-grid">
              <div><dt>Hostname</dt><dd>{node.hostname}</dd></div>
              <div><dt>Node ID</dt><dd className="monospace">{node.node_id}</dd></div>
              <div><dt>Database ID</dt><dd>#{node.id}</dd></div>
              <div><dt>Status</dt><dd>
                <span className={`status-badge status-${node.status}`}>{node.status.toUpperCase()}</span>
              </dd></div>
              <div><dt>Last Heartbeat</dt><dd>{new Date(node.last_seen).toLocaleString()} ({formatTimeAgo(node.last_seen)})</dd></div>
              <div><dt>Registered</dt><dd>{new Date(node.created_at).toLocaleString()}</dd></div>
              <div><dt>Last Updated</dt><dd>{new Date(node.updated_at).toLocaleString()}</dd></div>
            </dl>
          </section>

          {stats && stats.count > 0 && (
            <section className="node-detail-section" aria-labelledby="telemetry-summary-title">
              <h3 id="telemetry-summary-title" className="node-detail-section-title">Telemetry Summary</h3>
              <dl className="detail-grid">
                <div><dt>Data Points Collected</dt><dd>{stats.count}</dd></div>
                <div><dt>Avg CPU Usage</dt><dd>{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}</dd></div>
                <div><dt>Max CPU Usage</dt><dd>{stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "N/A"}</dd></div>
                <div><dt>Avg Memory Usage</dt><dd>{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}</dd></div>
                <div><dt>Max Memory Usage</dt><dd>{stats.max_memory ? `${stats.max_memory.toFixed(1)}%` : "N/A"}</dd></div>
                <div><dt>Avg Temperature</dt><dd>{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}</dd></div>
                <div><dt>Max Temperature</dt><dd>{stats.max_temperature ? `${stats.max_temperature.toFixed(1)}°C` : "N/A"}</dd></div>
                <div><dt>Latest Reading</dt><dd>{stats.latest_timestamp ? formatTimestamp(stats.latest_timestamp) : "N/A"}</dd></div>
              </dl>
            </section>
          )}

          {node.capabilities && node.capabilities.length > 0 && (
            <section className="node-detail-section" aria-labelledby="capabilities-title">
              <h3 id="capabilities-title" className="node-detail-section-title">Capabilities</h3>
              <ul className="capabilities-list" role="list">
                {node.capabilities.map((cap) => (
                  <li key={cap}><span className="badge badge-primary">{cap}</span></li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <div
          role="tabpanel"
          id="panel-telemetry"
          aria-labelledby="tab-telemetry"
          hidden={activeTab !== "telemetry"}
          className="animate-fade-in"
        >
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              Data Points:
              <select
                className="input select"
                style={{ width: 'auto', minWidth: '100px' }}
                value={telemetryPoints}
                onChange={(e) => setTelemetryPoints(Number(e.target.value))}
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </label>
            <button className="btn btn-secondary btn-sm" onClick={() => refetchTelemetry()} disabled={aggregatedTelemetry?.timestamps?.length === 0}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M23 4v6h-6" />
                <path d="M1 20v-6h6" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              Refresh
            </button>
          </div>

          {stats && stats.count > 0 ? (
            <>
              <div className="stats-grid" style={{ marginBottom: '1.5rem' }} role="region" aria-label="Telemetry statistics">
                <div className="stat-card">
                  <div className="stat-label">Data Points</div>
                  <div className="stat-value">{stats.count}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Avg CPU</div>
                  <div className="stat-value">{stats.avg_cpu ? `${stats.avg_cpu.toFixed(1)}%` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Peak CPU</div>
                  <div className="stat-value">{stats.max_cpu ? `${stats.max_cpu.toFixed(1)}%` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Avg Memory</div>
                  <div className="stat-value">{stats.avg_memory ? `${stats.avg_memory.toFixed(1)}%` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Peak Memory</div>
                  <div className="stat-value">{stats.max_memory ? `${stats.max_memory.toFixed(1)}%` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Avg Temp</div>
                  <div className="stat-value">{stats.avg_temperature ? `${stats.avg_temperature.toFixed(1)}°C` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Peak Temp</div>
                  <div className="stat-value">{stats.max_temperature ? `${stats.max_temperature.toFixed(1)}°C` : "N/A"}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Latest</div>
                  <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                    {stats.latest_timestamp ? formatTimeAgo(new Date(stats.latest_timestamp * 1000).toISOString()) : "Never"}
                  </div>
                </div>
              </div>

              {aggregatedTelemetry && aggregatedTelemetry.timestamps.length > 0 ? (
                <TelemetryCharts aggregatedTelemetry={aggregatedTelemetry} />
              ) : (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                    <path d="M18 20V10M12 20V4M6 20v-6" />
                    <path d="M2 20h20" />
                  </svg>
                  <h3 className="empty-state-title">Loading chart data...</h3>
                  <p className="empty-state-title">Fetching telemetry history for charts</p>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
              <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path d="M18 20V10M12 20V4M6 20v-6" />
                <path d="M2 20h20" />
              </svg>
              <h3 className="empty-state-title">No Telemetry Data</h3>
              <p className="empty-state-text">This node has not sent any telemetry data yet. Data will appear here once the node starts reporting.</p>
            </div>
          )}
        </div>

        <div
          role="tabpanel"
          id="panel-system"
          aria-labelledby="tab-system"
          hidden={activeTab !== "system"}
          className="animate-fade-in"
        >
          <section className="node-detail-section" aria-labelledby="system-info-title">
            <h3 id="system-info-title" className="node-detail-section-title">System Information</h3>
            <dl className="detail-grid">
              <div><dt>Operating System</dt><dd>{node.os} {node.os_version || ""}</dd></div>
              <div><dt>Kernel Version</dt><dd>{node.kernel_version || "Not available"}</dd></div>
              <div><dt>Architecture</dt><dd>{node.arch || "Not available"}</dd></div>
              <div><dt>CPU Model</dt><dd>{node.cpu_brand || "Not available"}</dd></div>
              <div><dt>CPU Cores</dt><dd>{node.cpu_cores || "Not available"}</dd></div>
              <div><dt>Total Memory</dt><dd>{formatBytes(node.total_memory)}</dd></div>
              <div><dt>AetherEdge Version</dt><dd>{node.version || "Not available"}</dd></div>
            </dl>
          </section>

          <section className="node-detail-section" aria-labelledby="comm-title">
            <h3 id="comm-title" className="node-detail-section-title">Communication</h3>
            <dl className="detail-grid">
              <div>
                <dt>Connection Status</dt>
                <dd>
                  <span className="connection-quality">
                    <span className={`status-dot ${statusKey}`} aria-hidden="true" />
                    <span className="status-text" style={{ textTransform: 'capitalize' }}>{statusKey}</span>
                  </span>
                </dd>
              </div>
              <div><dt>Last Heartbeat</dt><dd>{new Date(node.last_seen).toLocaleString()} ({formatTimeAgo(node.last_seen)})</dd></div>
              <div><dt>Registered At</dt><dd>{new Date(node.created_at).toLocaleString()}</dd></div>
              <div><dt>Last Updated</dt><dd>{new Date(node.updated_at).toLocaleString()}</dd></div>
            </dl>
          </section>
        </div>

        <div
          role="tabpanel"
          id="panel-commands"
          aria-labelledby="tab-commands"
          hidden={activeTab !== "commands"}
          className="animate-fade-in"
        >
          <section className="node-detail-section" aria-labelledby="available-commands-title">
            <h3 id="available-commands-title" className="node-detail-section-title">Available Commands</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.875rem' }}>
              Send commands to the edge node via the TCP control channel. Commands are queued and delivered on the next connection.
            </p>

            <div className="commands-help" role="list" aria-label="Available commands">
              <div className="command-item" role="listitem">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="cmd-badge">shutdown</span>
                  <span>Gracefully stops the edge node process</span>
                </div>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => { if (window.confirm("Shutdown this node?")) handleAction("shutdown"); }}
                    disabled={!canControl}
                  >
                    ⏻ Shutdown
                  </button>
                </div>
              </div>

              <div className="command-item" role="listitem">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="cmd-badge">reboot</span>
                  <span>Requests node to reboot (requires node support)</span>
                </div>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-warning btn-sm"
                    onClick={() => { if (window.confirm("Reboot this node?")) handleAction("reboot"); }}
                    disabled={!canControl}
                  >
                    ⟳ Reboot
                  </button>
                </div>
              </div>

              <div className="command-item" role="listitem">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="cmd-badge">update_telemetry_interval</span>
                  <span>Changes telemetry collection interval (seconds)</span>
                </div>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_telemetry_interval", { interval: 5 })} disabled={!canControl}>5s</button>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_telemetry_interval", { interval: 10 })} disabled={!canControl}>10s</button>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_telemetry_interval", { interval: 30 })} disabled={!canControl}>30s</button>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_telemetry_interval", { interval: 60 })} disabled={!canControl}>60s</button>
                </div>
              </div>

              <div className="command-item" role="listitem">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="cmd-badge">update_heartbeat_interval</span>
                  <span>Changes heartbeat interval (seconds)</span>
                </div>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_heartbeat_interval", { interval: 10 })} disabled={!canControl}>10s</button>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_heartbeat_interval", { interval: 30 })} disabled={!canControl}>30s</button>
                  <button className="btn btn-info btn-sm" onClick={() => handleAction("update_heartbeat_interval", { interval: 60 })} disabled={!canControl}>60s</button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}