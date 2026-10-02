# Current Node Data Flow Report

## Agent Sends (Rust Edge Daemon)

| Message | Interval | Fields |
|---------|----------|--------|
| **Register** | On connect | node_id, hostname, os, os_version, kernel_version, cpu_brand, cpu_cores, total_memory, version, arch, capabilities: ["telemetry", "heartbeat", "inference"] |
| **Heartbeat** | Every 10s | node_id, timestamp, status (Online), uptime |
| **Telemetry** | Every 2s | cpu_usage, cpu_per_core, memory_usage, memory_total, memory_available, memory_used, temperature, temperatures, uptime, load_1, load_5, load_15, processes_running, processes_total |

## Server Receives (TCP Server on port 8081)

| Handler | Action |
|---------|--------|
| `handle_register` | Creates/updates node in DB, returns RegisterResponse with server config (heartbeat_interval=10, telemetry_interval=2) |
| `handle_heartbeat` | Updates node.last_seen = now(), status = ONLINE |
| `handle_telemetry` | Stores telemetry in DB, updates node.last_seen = now(), status = ONLINE |

## Server Stores (SQLite via SQLAlchemy)

**Node table:**
- id, node_id, hostname, os, os_version, kernel_version, cpu_brand, cpu_cores, total_memory, version, arch, capabilities (JSON text), tags (JSON text)
- status (ONLINE/OFFLINE/DEGRADED/MAINTENANCE)
- last_seen, created_at, updated_at

**Telemetry table:**
- All telemetry fields + node_id (FK), timestamp

## Dashboard Requests (HTTP API on port 8080)

| Endpoint | Called By |
|----------|-----------|
| `GET /api/v1/nodes` | `useNodes` hook |
| `GET /api/v1/nodes/{node_id}` | `useNode` hook |
| `GET /api/v1/nodes/status/online` | `useOnlineNodes` hook |
| `GET /api/v1/nodes/status/offline` | `useOfflineNodes` hook |
| `GET /api/v1/telemetry/stats/{node_id}` | `useTelemetryStats` hook |
| `GET /api/v1/telemetry/aggregated/{node_id}` | `useAggregatedTelemetry` hook |

## Dashboard Receives

| Hook | Returns |
|------|---------|
| `useNodes` | NodeListResponse { nodes: Node[], total, page, page_size } |
| `useNode` | Node { id, node_id, hostname, os, ..., status, last_seen, created_at, updated_at } |
| `useTelemetryStats` | TelemetryStats { node_id, count, avg_cpu, max_cpu, avg_memory, max_memory, avg_temperature, max_temperature, latest_timestamp } |
| `useAggregatedTelemetry` | TelemetryAggregated { node_id, timestamps[], cpu_usage[], memory_usage[], temperature[], load_1[] } |

## Failure Points

### 1. **Blank Node Detail Page - Root Cause**
In `App.tsx` line 22:
```typescript
const { data: nodeDetail, isLoading: nodeLoading } = useNode(selectedNode || "");
```
When `selectedNode` is `null`, it passes empty string `""` to `useNode`, which calls `GET /api/v1/nodes/` (the **list** endpoint), not the detail endpoint. The list endpoint returns `NodeListResponse` (with `nodes[]`, `total`, etc.), not a single `Node` object. This causes the `NodeDetail` component to receive malformed data.

The `useNode` hook lacks `enabled: !!nodeId` option, so it fires even with empty string.

### 2. **Capability Type Mismatch**
- Rust sends: `capabilities: Vec<String>` (e.g., `["telemetry", "heartbeat", "inference"]`)
- Python schema expects: `NodeCapabilities { telemetry: bool, heartbeat: bool, inference: bool }`
- Database stores: `Text` (JSON)
- TypeScript expects: `capabilities?: string[]`
This causes potential deserialization issues when the API returns node data.

### 3. **No Individual Node Disconnect/Reconnect Control**
- All nodes share the same TCP connection pool (`_connected_clients` dict in `tcp_server.py`)
- No API endpoint to disconnect a specific node
- No way for agent to gracefully shutdown via server command (the `shutdown` command exists in protocol but isn't properly wired to disconnect the specific node's TCP connection)

### 4. **No Debug Visibility**
- Server logs are minimal (only INFO level for connections)
- No logging of received message types (REGISTER, HEARTBEAT, TELEMETRY)
- No agent-side logging of sent messages
- Dashboard has no system event log

### 5. **Node Detail API Missing Key Fields**
The `GET /api/v1/nodes/{node_id}` returns `NodeResponse` which has all fields, but:
- The `capabilities` field type mismatch (see #2)
- No telemetry data included in node detail (need separate calls)
- No connection status info (TCP connected vs DB status)

---

## Required Fixes Priority Order

1. **Fix `useNode` hook** - Add `enabled: !!nodeId` and handle empty string
2. **Fix capability serialization** - Align Rust, Python, and TypeScript types
3. **Add debug logging** - Server and agent
4. **Add node disconnect/reconnect API** - Per-node TCP connection management
5. **Add system event log to dashboard** - Debug panel
6. **Verify telemetry end-to-end** - Ensure data flows from agent → TCP → DB → HTTP API → Dashboard