import React from "react";
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

  return (
    <div className="node-overview">
      <h2>Node Overview</h2>

      <div className="stats-grid">
        <div className="stat-box total">
          <span className="stat-label">Total Nodes</span>
          <span className="stat-value">{totalNodes}</span>
        </div>

        <div className="stat-box online">
          <span className="stat-label">Online</span>
          <span className="stat-value">{totalOnline}</span>
        </div>

        <div className="stat-box offline">
          <span className="stat-label">Offline</span>
          <span className="stat-value">{totalOffline}</span>
        </div>

        <div className="stat-box degraded">
          <span className="stat-label">Degraded</span>
          <span className="stat-value">{totalDegraded}</span>
        </div>
      </div>
    </div>
  );
}