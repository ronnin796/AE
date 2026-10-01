interface NavBarProps {
  selectedNode: string | null;
  onNodeSelect: (nodeId: string) => void;
  onRefresh: () => void;
}

export default function NavBar({ selectedNode, onNodeSelect, onRefresh }: NavBarProps) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>AetherEdge</h1>
        <span className="navbar-subtitle">Edge AI Monitor</span>
      </div>

      <div className="navbar-actions">
        <button onClick={onRefresh} className="refresh-button">
          Refresh
        </button>
        {selectedNode && (
          <button
            onClick={() => onNodeSelect("")}
            className="back-button"
          >
            ← All Nodes
          </button>
        )}
      </div>
    </nav>
  );
}