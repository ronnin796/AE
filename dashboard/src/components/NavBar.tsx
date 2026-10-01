import { useNodes } from "../hooks/useNodes";
import { Node } from "../types";

interface NavBarProps {
  selectedNode: string | null;
  onNodeSelect: (nodeId: string) => void;
  onRefresh: () => void;
}

export default function NavBar({ selectedNode, onNodeSelect, onRefresh }: NavBarProps) {
  const { data: nodesData } = useNodes(1, 100);
  const selectedNodeInfo = nodesData?.nodes.find((n: Node) => n.node_id === selectedNode);

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
          <>
            <span className="navbar-selected-node">
              Viewing: {selectedNodeInfo?.hostname || selectedNode}
            </span>
            <button
              onClick={() => onNodeSelect("")}
              className="back-button"
            >
              ← All Nodes
            </button>
          </>
        )}
      </div>
    </nav>
  );
}