import { useState } from "react";
import { useNodes, useOnlineNodes, useOfflineNodes, useNode } from "./hooks/useNodes";
import { useAggregatedTelemetry, useTelemetryStats } from "./hooks/useTelemetry";

import NavBar from "./components/NavBar";
import NodeOverview from "./components/NodeOverview";
import NodeList from "./components/NodeList";
import TelemetryDashboard from "./components/TelemetryDashboard";
import StatusSummary from "./components/StatusSummary";
import NodeDetail from "./components/NodeDetail";

function App() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Fetch nodes
  const { data: nodesData } = useNodes(1, 20);

  // Fetch online nodes
  const { data: onlineNodes = [] } = useOnlineNodes();

  // Fetch offline nodes
  const { data: offlineNodes = [] } = useOfflineNodes();

  // Fetch selected node details
  const { data: nodeDetail, isLoading: nodeLoading } = useNode(selectedNode || "");

  // Node telemetry if selected
  const { data: aggregatedTelemetry, refetch: refetchTelemetry } = useAggregatedTelemetry(
    selectedNode || "",
    50
  );

  const { data: stats } = selectedNode
    ? useTelemetryStats(selectedNode)
    : { data: null };

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
        {selectedNode ? (
          <>
            <NodeDetail node={nodeDetail} isLoading={nodeLoading} stats={stats} />
            <StatusSummary nodeId={selectedNode} stats={stats} />
            <TelemetryDashboard
              nodeId={selectedNode}
              aggregatedTelemetry={aggregatedTelemetry}
              stats={stats}
            />
          </>
        ) : (
          <NodeList
            onSelect={(nodeId: string) => setSelectedNode(nodeId)}
          />
        )}
      </div>
    </div>
  );
}

export default App;