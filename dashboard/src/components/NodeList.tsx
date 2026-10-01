import React from "react";
import { Node } from "../types";
import { useNodes, useOnlineNodes, useOfflineNodes } from "../hooks/useNodes";
import NodeCard from "./NodeCard";

interface NodeListProps {
  onSelect: (nodeId: string) => void;
}

export default function NodeList({ onSelect }: NodeListProps) {
  const { data: nodesData } = useNodes(1, 20);
  const { data: onlineNodes = [] } = useOnlineNodes();
  const { data: offlineNodes = [] } = useOfflineNodes();
  const [nodes, setNodes] = React.useState<Node[]>([]);
  const [page, setPage] = React.useState(1);
  const [total, setTotal] = React.useState(0);
  const pageSize = 20;

  React.useEffect(() => {
    if (nodesData) {
      setNodes(nodesData.nodes);
      setTotal(nodesData.total);
      setPage(1);
    }
  }, [nodesData]);

  if (!nodesData) {
    return <div className="loading">Loading nodes...</div>;
  }

  return (
    <div className="node-list-container">
      <h2>Nodes</h2>

      <div className="node-list-header">
        <div className="node-list-header-left">
          <span>Total Nodes: {total}</span>
          <span>Online: {onlineNodes.length}</span>
          <span>Offline: {offlineNodes.length}</span>
        </div>
        <button onClick={() => setPage(1)} className="page-btn">First</button>
        <button onClick={() => setPage(page - 1)} className="page-btn" disabled={page <= 1}>
          Previous
        </button>
        <span>Page {page} of {Math.ceil(total / pageSize)}</span>
        <button onClick={() => setPage(page + 1)} className="page-btn">Next</button>
      </div>

      {nodes.length > 0 && (
        <div className="node-list">
          {nodes.map((node) => (
            <NodeCard key={node.node_id} node={node} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}