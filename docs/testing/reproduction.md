# AetherEdge Part I — Test Reproduction Guide

**Date:** 2026-10-01
**Branch:** mid-defense-hardening

---

## Prerequisites

### System Requirements
- Linux (tested on CachyOS Linux, kernel 7.2.8)
- Rust 1.80+ (via rustup)
- Python 3.14+ with uv
- Node.js 20+ with npm
- SQLite 3.45+

### Project Setup
```bash
# Clone repository
git clone <repo-url>
cd AE_Edge

# Switch to mid-defense branch
git checkout mid-defense-hardening
```

---

## Building the Project

### Rust Edge Daemon
```bash
cd edge
cargo build --release
# Binary at: target/release/aetheredge-edge
```

### Python Server
```bash
cd server
uv sync
# Virtual environment at: .venv/
```

### React Dashboard
```bash
cd dashboard
npm install
npm run build
# Output in: dist/
```

---

## Running Tests

### Unit Tests

#### Rust (Edge Daemon)
```bash
cd edge
cargo test
# Expected: 17 passed
```

#### Python (Server)
```bash
cd server
.venv/bin/pytest tests/unit/ -v
# Expected: 27 passed
```

### Integration Tests
```bash
cd server
.venv/bin/pytest tests/integration/ -v -s
# Expected: 9 passed
```

### System Test
```bash
cd server
.venv/bin/pytest tests/system/ -v -s
# Expected: 1 passed (60s duration)
```

### Benchmark Tests
```bash
cd server
.venv/bin/pytest tests/benchmark/ -v -s
# Expected: 4 passed
```

### All Tests
```bash
# From project root
cd edge && cargo test
cd ../server && .venv/bin/pytest tests/ -v
```

---

## Running the System Manually

### 1. Start the Server
```bash
cd server
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```
Server runs on:
- HTTP API: http://localhost:8080
- TCP Protocol: localhost:8081

### 2. Start Edge Node(s)
```bash
cd edge
# Single node
cargo run -- --node-id node-a --telemetry-interval 2

# Multiple nodes (separate terminals)
cargo run -- --node-id node-a --telemetry-interval 2
cargo run -- --node-id node-b --telemetry-interval 2
```

### 3. View Dashboard
```bash
cd dashboard
npm run dev
# Open http://localhost:5173
```
Or serve built version:
```bash
cd dashboard
npx serve dist
# Open http://localhost:3000
```

---

## Demonstration Script (Mid-Defense)

### 1. Start Server
```bash
cd server
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 &
```

### 2. Start Two Edge Nodes
```bash
cd edge
cargo run -- --node-id demo-node-a --telemetry-interval 2 &
cargo run -- --node-id demo-node-b --telemetry-interval 2 &
```

### 3. Open Dashboard
Open http://localhost:5173 in browser

### 4. Observe
- Both nodes appear in dashboard with ONLINE status
- Real-time CPU, Memory, Temperature charts
- Node overview cards with system info

### 5. Generate Workload
```bash
# On node-a's machine (or same machine)
stress-ng --cpu 4 --timeout 30
# Or: yes > /dev/null &
```

### 6. Observe Dashboard Response
- Node A CPU spikes in real-time
- Memory may increase slightly
- Charts update every 2 seconds

### 7. Demonstrate Node Failure
```bash
# Kill node-b
pkill -f "demo-node-b"
# Wait ~15 seconds
# Node B shows OFFLINE in dashboard
```

### 8. Demonstrate Reconnection
```bash
# Restart node-b
cd edge
cargo run -- --node-id demo-node-b --telemetry-interval 2 &
# Node B shows ONLINE again
```

---

## Benchmark Reproduction

### Edge Daemon Memory
```bash
cd server
.venv/bin/pytest tests/benchmark/test_benchmarks.py::TestBenchmarks::test_bt003_edge_daemon_memory_consumption -v -s
```

### Edge Daemon CPU
```bash
cd server
.venv/bin/pytest tests/benchmark/test_benchmarks.py::TestBenchmarks::test_bt004_edge_daemon_cpu_overhead -v -s
```

### Telemetry Message Size
```bash
cd server
.venv/bin/pytest tests/benchmark/test_benchmarks.py::TestBenchmarks::test_bt005_telemetry_message_size -v -s
```

### Telemetry Interval Accuracy
```bash
cd server
.venv/bin/pytest tests/benchmark/test_benchmarks.py::TestBenchmarks::test_bt006_telemetry_interval_accuracy -v -s
```

---

## Troubleshooting

### Server Won't Start
- Check if port 8080/8081 already in use: `lsof -i :8080`
- Check database file permissions: `ls -la server/aetheredge.db`
- Check logs: `cat server/test_server.log`

### Edge Node Can't Connect
- Verify server TCP port 8081 is listening: `ss -ltn | grep 8081`
- Check firewall rules
- Verify node ID is unique

### Dashboard Shows No Data
- Check browser console for CORS errors
- Verify API base URL in dashboard/src/api/client.ts
- Check server CORS settings

### Database Errors
- Delete database file and restart: `rm server/aetheredge.db`
- Run migrations: `cd server && .venv/bin/alembic upgrade head`

---

## Expected Test Outputs

### Rust Unit Tests (17 tests)
```
test networking::tests::test_network_client_creation ... ok
test protocol::messages::tests::test_heartbeat_serialization ... ok
...
test result: ok. 17 passed; 0 failed
```

### Python Unit Tests (27 tests)
```
tests/unit/test_database.py::TestNodeDatabase::test_get_node_by_id_found PASSED
...
tests/unit/test_schemas.py::TestTelemetrySchemas::test_telemetry_stats PASSED
===================== 27 passed in 0.33s
```

### Integration Tests (9 tests)
```
test_it001_single_node_registration PASSED
test_it002_multi_node_registration PASSED
test_it003_heartbeat_updates_last_seen PASSED
test_it004_telemetry_pipeline PASSED
test_it008_concurrent_nodes_telemetry PASSED
test_it005_node_disconnection_detected PASSED
test_it006_node_reconnection PASSED
test_it007_malformed_registration_rejected PASSED
test_it007_malformed_telemetry_rejected PASSED
================== 9 passed in ~65s
```

### System Test (1 test)
```
test_st001_end_to_end_edge_monitoring Telemetry collected: Node A=33, Node B=33
PASSED
```

### Benchmark Tests (4 tests)
```
test_bt003_edge_daemon_memory_consumption PASSED (mean=29.2MB)
test_bt004_edge_daemon_cpu_overhead PASSED (mean=0.13%)
test_bt005_telemetry_message_size PASSED (573 bytes)
test_bt006_telemetry_interval_accuracy PASSED (mean=2.00s)
================== 4 passed in ~96s
```