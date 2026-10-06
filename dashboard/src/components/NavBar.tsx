import { useTheme } from "../context/ThemeContext";
import { Node } from "../types";
import { useNodes } from "../hooks/useNodes";

interface NavBarProps {
  selectedNode: string | null;
  onNodeSelect: (nodeId: string) => void;
  onRefresh: () => void;
}

export default function NavBar({ selectedNode, onNodeSelect, onRefresh }: NavBarProps) {
  const { theme, toggleTheme } = useTheme();
  const { data: nodesData } = useNodes(1, 100);
  const selectedNodeInfo = nodesData?.nodes.find((n: Node) => n.node_id === selectedNode);

  const totalNodes = nodesData?.total || 0;
  const onlineCount = nodesData?.nodes.filter((n: Node) => n.status === 'online').length || 0;

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-brand">
        <div className="navbar-logo" aria-hidden="true">AE</div>
        <div>
          <h1 className="navbar-title">AetherEdge</h1>
          <span className="navbar-subtitle">Edge AI Monitor</span>
        </div>
      </div>

      <div className="navbar-center">
        <div className="node-count" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.8125rem', flexWrap: 'wrap', minWidth: 0 }}>
          <span>Nodes:</span>
          <span className="node-count-badge">{totalNodes}</span>
          <span style={{ color: 'var(--accent-success)' }}>● {onlineCount} online</span>
        </div>
      </div>

      <div className="navbar-actions">
        <button
          className="navbar-btn navbar-btn-icon theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Current: ${theme} mode. Click to toggle.`}
        >
          {theme === 'dark' ? (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591 1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
            </svg>
          )}
        </button>

        <button
          className="navbar-btn navbar-btn-primary"
          onClick={onRefresh}
          aria-label="Refresh data"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          Refresh
        </button>

        {selectedNode && (
          <>
            <div className="navbar-selected-node">
              <span>Viewing:</span>
              <span className="node-name">{selectedNodeInfo?.hostname || selectedNode}</span>
            </div>
            <button
              onClick={() => onNodeSelect("")}
              className="navbar-btn navbar-btn-secondary"
              aria-label="Back to all nodes"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              All Nodes
            </button>
          </>
        )}
      </div>
    </nav>
  );
}