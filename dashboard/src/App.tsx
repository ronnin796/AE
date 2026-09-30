import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { NodeListResponse, Node } from "../types";
import { useOnlineNodes, useOfflineNodes, useAggregatedTelemetry, useTelemetryStats } from "../hooks";

import NavBar from "./components/NavBar";
import NodeOverview from "./components/NodeOverview";
import NodeList from "./components/NodeList";
import TelemetryDashboard from "./components/TelemetryDashboard";
import StatusSummary from "./components/StatusSummary";

function App() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Fetch nodes
  const { data: nodesData, isLoading } = useQuery<NodeListResponse>({
    queryKey: ["nodes", 1, 20],
    queryFn: () => api.getNodes(1, 20),
    refetchInterval: 5000,
  });

  // Fetch online nodes
  const onlineNodes = useOnlineNodes();

  // Fetch offline nodes
  const offlineNodes = useOfflineNodes();

  // Node telemetry if selected
  const { data: aggregatedTelemetry, refetch: refetchTelemetry } = useAggregatedTelemetry(
    selectedNode || "",
    50
  );

  const { data: stats, isLoading: statsLoading } = selectedNode
    ? useTelemetryStats(selectedNode)
    : { data: null, isLoading: false };

  return (
    <div className="app">
      <NavBar
        selectedNode={selectedNode}
        onNodeSelect={(nodeId: string) => setSelectedNode(nodeId)}
        onRefresh={() => refetchTelemetry()}
      />
      <div className="content">
        <NodeOverview
          nodes={nodesData?.nodes || []}
          onlineNodes={onlineNodes}
          offlineNodes={offlineNodes}
        />
        {selectedNode && (
          <>
            <StatusSummary nodeId={selectedNode} stats={stats} />
            <TelemetryDashboard
              nodeId={selectedNode}
              aggregatedTelemetry={aggregatedTelemetry}
            />
          </>
        )}
        {!selectedNode && (
          <NodeList
            nodes={nodesData?.nodes || []}
            onSelect={(nodeId: string) => setSelectedNode(nodeId)}
          />
        )}
      </div>
    </div>
  );
}

export default App;