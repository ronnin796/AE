import { useState } from "react";
import { useNodes, useOnlineNodes, useOfflineNodes } from "./hooks/useNodes";
import { useAggregatedTelemetry, useTelemetryStats } from "./hooks/useTelemetry";

import NavBar from "./components/NavBar";
import NodeOverview from "./components/NodeOverview";
import NodeList from "./components/NodeList";
import TelemetryDashboard from "./components/TelemetryDashboard";
import StatusSummary from "./components/StatusSummary";

function App() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Fetch nodes
  const { data: nodesData } = useNodes(1, 20);

  // Fetch online nodes
  const { data: onlineNodes = [] } = useOnlineNodes();

  // Fetch offline nodes
  const { data: offlineNodes = [] } = useOfflineNodes();

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
            onSelect={(nodeId: string) => setSelectedNode(nodeId)}
          />
        )}
      </div>
    </div>
  );
}

export default App;