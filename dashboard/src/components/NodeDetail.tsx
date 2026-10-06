import { useState } from "react";
import { Node, TelemetryStats } from "../types";
import { shutdownNode, sendNodeCommand, disconnectNode, reconnectNode, deleteNode } from "../api/client";
import { TelemetryCharts } from "./TelemetryCharts";
import { TelemetryAggregated } from "../types";
import { useAggregatedTelemetry } from "../hooks/useTelemetry";
import { useDebug } from "../context/DebugContext";

interface NodeDetailProps {
  node: Node;
  stats?: TelemetryStats | null;
  onNodeDeleted?: () => void;
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

const getTelemetryState = (node: Node, stats: TelemetryStats | null | undefined) => {
  const isOnline = node.status === "online";

  // No stats available (not loaded or no telemetry in DB)
  if (!stats || stats.count === 0) {
    if (isOnline) {
      return { state: 'waiting', label: 'WAITING', details: '' };
    } else {
      return { state: 'offline', label: 'OFFLINE', details: `Last seen: ${formatTimeAgo(new Date(node.last_seen).toISOString())}` };
    }
  }

  // Has telemetry data - check freshness
  if (stats.latest_timestamp) {
    const latestTs = stats.latest_timestamp * 1000; // Convert to ms
    const now = Date.now();
    const ageMs = now - latestTs;
    const ageSecs = Math.floor(ageMs / 1000);

    // Consider telemetry stale if older than 3x telemetry interval (default 2s -> 6s threshold)
    const telemetryInterval = node.telemetry_interval || 2;
    const staleThreshold = telemetryInterval * 3 * 1000; // ms

    if (ageMs > staleThreshold) {
      return {
        state: 'stale',
        label: 'STALE',
        details: `Last update: ${formatRelativeTimeFromSeconds(ageSecs)}`,
        ageSecs
      };
    }

    return {
      state: 'live',
      label: 'LIVE',
      details: `Updated ${formatRelativeTimeFromSeconds(ageSecs)}`,
      ageSecs
    };
  }

  // Has stats but no timestamp (edge case)
  return { state: 'live', label: 'LIVE', details: 'Data available' };
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

type TabId = "overview" | "telemetry" | "system";

const tabs: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "telemetry", label: "Telemetry" },
  { id: "system", label: "System" },
];

export default function NodeDetail({ node, stats, onNodeDeleted }: NodeDetailProps) {
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

  const handleDelete = async () => {
    if (!window.confirm(`Permanently delete node "${node.hostname}" (${node.node_id})?`)) return;
    setActionLoading("delete");
    setActionResult(null);
    addEvent({ type: "command", node_id: node.node_id, message: `Deleting node ${node.node_id}` });
    try {
      const result = await deleteNode(node.node_id);
      addEvent({ type: "command", node_id: node.node_id, message: `Node deleted: ${result.message}` });
      setActionResult({ success: true, message: result.message || `Node ${node.node_id} deleted` });
      if (onNodeDeleted) onNodeDeleted();
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || "Failed to delete node";
      addEvent({ type: "error", node_id: node.node_id, message: `Delete failed: ${msg}` });
      setActionResult({ success: false, message: msg });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="panel node-detail" role="main" aria-label={`Node details: ${node.hostname}`}>
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
        <button
          className={`btn btn-secondary btn-sm ${!canControl ? "btn-disabled" : ""}`}
          onClick={() => {
            if (!canControl) return;
            if (window.confirm("Shutdown this node?")) handleAction("shutdown");
          }}
          disabled={!canControl || actionLoading === "shutdown"}
          aria-disabled={!canControl || actionLoading === "shutdown"}
        >
          Shutdown
        </button>

        <button
          className={`btn btn-secondary btn-sm ${!canControl ? "btn-disabled" : ""}`}
          onClick={() => {
            if (!canControl) return;
            if (window.confirm("Disconnect this node?")) handleAction("disconnect");
          }}
          disabled={!canControl || actionLoading === "disconnect"}
          aria-disabled={!canControl || actionLoading === "disconnect"}
        >
          Disconnect
        </button>

        <button
          className={`btn btn-secondary btn-sm ${!canControl ? "btn-disabled" : ""}`}
          onClick={() => {
            if (!canControl) return;
            if (window.confirm("Reconnect this node?")) handleAction("reconnect");
          }}
          disabled={!canControl || actionLoading === "reconnect"}
          aria-disabled={!canControl || actionLoading === "reconnect"}
        >
          Reconnect
        </button>

        <button
          className={`btn btn-warning btn-sm ${!canControl ? "btn-disabled" : ""}`}
          onClick={() => {
            if (!canControl) return;
            handleAction("update_telemetry_interval", { interval: 5 });
          }}
          disabled={!canControl || actionLoading === "update_telemetry_interval"}
        >
          Telemetry: 5s
        </button>

        <button
          className={`btn btn-warning btn-sm ${!canControl ? "btn-disabled" : ""}`}
          onClick={() => {
            if (!canControl) return;
            handleAction("update_telemetry_interval", { interval: 10 });
          }}
          disabled={!canControl || actionLoading === "update_telemetry_interval"}
        >
          Telemetry: 10s
        </button>

        <button
          className={`btn btn-danger btn-sm ${actionLoading === "delete" ? "btn-disabled" : ""}`}
          onClick={handleDelete}
          disabled={actionLoading !== null}
          aria-disabled={actionLoading !== null}
          title="Permanently delete this node from the registry"
        >
          {actionLoading === "delete" ? "Deleting..." : "Delete Node"}
        </button>
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
            disabled={!canControl && tab.id === "system"}
          >
            {tab.label}
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
                  <li key={cap}><span className="badge badge-info">{cap}</span></li>
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
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem' }}>
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
              Refresh
            </button>
          </div>

          {(stats && stats.count > 0) ? (
            <>
              {(() => {
                const telemetryState = getTelemetryState(node, stats);
                if (telemetryState.state === 'live') {
                  return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', background: 'var(--accent-success-light)', border: '1px solid var(--accent-success)', marginBottom: '1rem' }}>
                      <span className={"status-dot online"} style={{ width: '10px', height: '10px' }} />
                      <span style={{ fontWeight: 600, color: 'var(--accent-success)' }}>LIVE TELEMETRY</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                        {stats.latest_timestamp ? (
                          <>
                            Last update: {formatTimeAgo(new Date(stats.latest_timestamp * 1000).toISOString())}
                            {' | '}
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                              {new Date(stats.latest_timestamp * 1000).toLocaleTimeString()}
                            </span>
                          </>
                        ) : (
                          'Waiting for first update...'
                        )}
                      </span>
                    </div>
                  );
                } else if (telemetryState.state === 'stale') {
                  return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', background: 'var(--accent-warning-light)', border: '1px solid var(--accent-warning)', marginBottom: '1rem' }}>
                      <span className={"status-dot degraded"} style={{ width: '10px', height: '10px' }} />
                      <span style={{ fontWeight: 600, color: 'var(--accent-warning)' }}>STALE TELEMETRY</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                        {telemetryState.details}
                        {' | '}
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                          {stats.latest_timestamp ? new Date(stats.latest_timestamp * 1000).toLocaleTimeString() : ''}
                        </span>
                      </span>
                    </div>
                  );
                } else if (telemetryState.state === 'waiting') {
                  return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', background: 'var(--accent-info-light)', border: '1px solid var(--accent-info)', marginBottom: '1rem' }}>
                      <span className={"status-dot online"} style={{ width: '10px', height: '10px' }} />
                      <span style={{ fontWeight: 600, color: 'var(--accent-info)' }}>WAITING FOR TELEMETRY</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>Node is online but no telemetry data received yet</span>
                    </div>
                  );
                }
                return null;
              })()}

              <div className="stats-grid" style={{ marginBottom: '1rem' }} role="region" aria-label="Telemetry statistics">
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
              </div>

              {aggregatedTelemetry && aggregatedTelemetry.timestamps.length > 0 ? (
                <TelemetryCharts aggregatedTelemetry={aggregatedTelemetry} />
              ) : (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  <h3 className="empty-state-title">Loading chart data...</h3>
                  <p className="empty-state-text">Fetching telemetry history for charts</p>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
              <h3 className="empty-state-title">No Telemetry Data</h3>
              <p className="empty-state-text">
                This node has not sent any telemetry data yet.
              </p>
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)', textAlign: 'left', maxWidth: '400px' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Node Status:</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem' }}>
                  <span className={`status-dot ${statusKey}`} />
                  <span className={`status-badge status-${statusKey}`}>{statusKey.toUpperCase()}</span>
                </div>
                <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                  <div>Node ID: <code>{node.node_id}</code></div>
                  <div>Last heartbeat: {new Date(node.last_seen).toLocaleString()} ({formatTimeAgo(node.last_seen)} ago)</div>
                  <div>Telemetry interval: {node.telemetry_interval || '2'}s (configured by server)</div>
                </div>
              </div>
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
      </div>
    </div>
  );
}