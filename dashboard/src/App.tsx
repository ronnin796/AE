import { useState } from "react";
import { ThemeProvider } from "./context/ThemeContext";
import { DebugProvider, useDebug } from "./context/DebugContext";
import { useNodes, useOnlineNodes, useOfflineNodes, useNode } from "./hooks/useNodes";
import { useAggregatedTelemetry, useTelemetryStats } from "./hooks/useTelemetry";

import NavBar from "./components/NavBar";
import NodeOverview from "./components/NodeOverview";
import NodeList from "./components/NodeList";
import TelemetryDashboard from "./components/TelemetryDashboard";
import StatusSummary from "./components/StatusSummary";
import NodeDetail from "./components/NodeDetail";
import DebugPanel from "./components/DebugPanel";

function AppContent() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Fetch nodes for sidebar/overview
  const { data: nodesData } = useNodes(1, 100);
  const { data: onlineNodes = [] } = useOnlineNodes();
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

  const { addEvent } = useDebug();

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNode(nodeId);
    if (nodeId) {
      addEvent({ type: "connect", node_id: nodeId, message: `Selected node ${nodeId}` });
    }
  };

  const handleRefresh = () => {
    refetchTelemetry();
    addEvent({ type: "command", node_id: "system", message: "Manual refresh triggered" });
    // The useQuery hooks will auto-refetch based on their intervals
  };

  return (
    <DebugProvider>
      <div className="app">
        <NavBar
          selectedNode={selectedNode}
          onNodeSelect={handleNodeSelect}
          onRefresh={handleRefresh}
        />
        <main className="main-content">
          <aside className="sidebar" aria-label="Cluster overview">
            <NodeOverview
              nodes={nodesData?.nodes || []}
              onlineNodes={onlineNodes}
              offlineNodes={offlineNodes}
            />
            {selectedNode && (
              <TelemetryDashboard
                nodeId={selectedNode}
                aggregatedTelemetry={aggregatedTelemetry}
                stats={stats}
              />
            )}
            {!selectedNode && (
              <TelemetryDashboard
                nodeId=""
                aggregatedTelemetry={undefined}
                stats={null}
              />
            )}
            <DebugPanel />
          </aside>

          <div className="content-area" role="main">
            {selectedNode && nodeDetail && !nodeLoading ? (
              <>
                <NodeDetail node={nodeDetail} stats={stats} />
              </>
            ) : selectedNode && nodeLoading ? (
              <div className="loading-detail" role="status" aria-live="polite">
                <div className="skeleton skeleton-title" />
                <div className="skeleton skeleton-card" style={{ marginTop: '1rem' }} />
                <div className="skeleton skeleton-card" style={{ marginTop: '1rem' }} />
              </div>
            ) : (
              <NodeList onSelect={handleNodeSelect} />
            )}
          </div>
        </main>
      </div>
    </DebugProvider>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;