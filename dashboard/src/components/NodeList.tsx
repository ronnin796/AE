import React from "react";
import { Node, NodeListResponse } from "../types";
import { useNodes } from "../hooks/useNodes";
import { useEffect, useState } from "react";

interface NodeListProps {
  onSelect: (nodeId: string) => void;
}

export default function NodeList({ onSelect }: NodeListProps) {
  const { data: nodes, isLoading } = useNodes(1, 20);
  const [nodes, setNodes] = useState<NodeListResponse['nodes']>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (nodesData) {
      setNodes(nodesData.nodes);
      setTotal(nodesData.total);
      setPage(1);
    }
  }, [nodesData]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  }

  if (isLoading) {
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
    </div>

    {nodes.length > 0 && (
      <div className="node-list">
        {nodes.map((node) => (
          <NodeCard key={node.node_id} node={node} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}