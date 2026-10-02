import { Node } from "../types";

interface NodeOverviewProps {
  nodes: Node[];
  onlineNodes: Node[];
  offlineNodes: Node[];
}

export default function NodeOverview({ nodes, onlineNodes, offlineNodes }: NodeOverviewProps) {
  const totalNodes = nodes.length;
  const totalOnline = onlineNodes.length;
  const totalOffline = offlineNodes.length;
  const totalDegraded = nodes.filter((n) => n.status === "degraded").length;
  const totalMaintenance = nodes.filter((n) => n.status === "maintenance").length;

  const getUptime = (lastSeen: string) => {
    const diff = Date.now() - new Date(lastSeen).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${mins}m`;
  };

  return (
    <div className="card node-overview">
      <header className="card-header">
        <h3 className="card-title">Cluster Overview</h3>
      </header>

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-label">Total Nodes</div>
          <div className="stat-value">{totalNodes}</div>
        </div>
        <div className="stat-card stat-card-success">
          <div className="stat-label">Online</div>
          <div className="stat-value">{totalOnline}</div>
        </div>
        <div className="stat-card stat-card-danger">
          <div className="stat-label">Offline</div>
          <div className="stat-value">{totalOffline}</div>
        </div>
        <div className="stat-card stat-card-warning">
          <div className="stat-label">Degraded</div>
          <div className="stat-value">{totalDegraded}</div>
        </div>
        {totalMaintenance > 0 && (
          <div className="stat-card" style={{ borderLeftColor: 'var(--accent-info)' }}>
            <div className="stat-label">Maintenance</div>
            <div className="stat-value">{totalMaintenance}</div>
          </div>
        )}
      </div>

      {totalNodes > 0 && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-primary)' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recent Activity
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {nodes
              .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
              .slice(0, 5)
              .map((node) => (
                <div key={node.node_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`status-dot ${node.status}`} />
                    <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{node.hostname || node.node_id}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                    <span className={`status-badge status-${node.status}`} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem' }}>
                      {node.status.toUpperCase()}
                    </span>
                    <span>{getUptime(node.last_seen)} ago</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {totalNodes === 0 && (
        <div className="empty-state" style={{ marginTop: '1rem' }}>
          <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <h4 className="empty-state-title">No Nodes Registered</h4>
          <p className="empty-state-text">Start edge nodes to see them appear in the cluster.</p>
        </div>
      )}
    </div>
  );
}