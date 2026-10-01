# AetherEdge Part I — Test Results

**Date:** 2026-10-01
**Branch:** mid-defense-hardening
**Commit:** Latest

---

## Unit Tests

### Rust Unit Tests (edge/)

| Test ID | Test Type | Component | Test Parameters/Input | Expected Result | Actual Result | Status | Evidence |
|---------|-----------|-----------|----------------------|-----------------|---------------|--------|----------|
| UT-001 | Unit | CPU Collector | `CpuTimes` struct with sample values | `total()` and `active()` calculate correctly | `total()=988`, `active()=168` | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-002 | Unit | CPU Collector | `calculate_usage(prev, curr)` with delta | Returns usage % between 0-100 | Returns valid percentage | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-003 | Unit | CPU Collector | `parse_proc_stat()` on `/proc/stat` | Parses CPU times for all cores | Returns Vec<CpuTimes> | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-004 | Unit | Memory Collector | `MemoryCollector::new()` | Constructs successfully | Constructs without error | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-005 | Unit | Temperature Collector | `TemperatureCollector::new()` | Constructs successfully | Constructs without error | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-006 | Unit | System Collector | `SystemCollector::new()` | Constructs successfully | Constructs without error | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-007 | Unit | Telemetry | `Telemetry::new(node_id)` | Creates telemetry with timestamp | Creates with node_id and timestamp > 0 | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-008 | Unit | Telemetry Config | `TelemetryConfig::default()` | All collection flags true | All flags true | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-009 | Unit | Protocol Envelope | `encode_envelope` / `decode_envelope` | Round-trip preserves all fields | All fields match after round-trip | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-010 | Unit | Message Type | `MessageType::from_u8()` | Correctly maps u8 to enum variants | Maps 1=Register, 5=Telemetry, 255=Error | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-011 | Unit | Register Message | MessagePack serialize/deserialize | Preserves all register fields | All fields preserved | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-012 | Unit | Heartbeat Message | MessagePack serialize/deserialize | Preserves node_id, status, uptime | All fields preserved | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-013 | Unit | Network Client | `NetworkClient::new(addr, identity)` | Creates client with correct addr | Client.server_addr == addr | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-014 | Unit | Node Identity | `NodeIdentity::build(None, None)` | Generates UUID, collects system info | node_id not empty, hostname not empty | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-015 | Unit | Node Identity | `NodeIdentity::build(Some(id), Some(host))` | Uses provided overrides | node_id == id, hostname == host | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-016 | Unit | Node Metadata | `NodeMetadata::from_identity()` | Includes capabilities list | Contains telemetry, heartbeat, inference | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |
| UT-017 | Unit | Logging | `logging::init()` | Initializes tracing subscriber | Initializes without error | PASS | [rust-unit-test.log](../logs/rust-unit-test.log) |

**Rust Unit Tests Summary:** 17 passed, 0 failed

---

### Python Unit Tests (server/)

| Test ID | Test Type | Component | Test Parameters/Input | Expected Result | Actual Result | Status | Evidence |
|---------|-----------|-----------|----------------------|-----------------|---------------|--------|----------|
| UT-101 | Unit | Node Schemas | `NodeBase` with valid data | Creates node with all fields | All fields set correctly | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-102 | Unit | Node Schemas | `NodeBase` minimal (required only) | Creates node with defaults | Optional fields are None | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-103 | Unit | Node Schemas | `NodeRegister` with full data | Creates registration schema | All fields set correctly | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-104 | Unit | Node Schemas | `NodeRegisterResponse` | Creates response with config | success=true, config populated | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-105 | Unit | Node Schemas | `NodeUpdate` partial update | Only provided fields set | hostname and cpu_cores set, others None | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-106 | Unit | Node Schemas | `ServerConfig` | Creates config with intervals | heartbeat=10, telemetry=2 | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-107 | Unit | Node Schemas | `NodeCapabilities` | Creates capabilities bools | telemetry=true, heartbeat=true, inference=true | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-108 | Unit | Node Schemas | `NodeListResponse` empty | Creates empty paginated response | total=0, page=1 | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-109 | Unit | Telemetry Schemas | `TelemetryBase` full data | Creates telemetry with all metrics | All fields including arrays set | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-110 | Unit | Telemetry Schemas | `TelemetryBase` minimal | Creates with only required fields | node_id, timestamp set; others None | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-111 | Unit | Telemetry Schemas | `TelemetryCreate` | Creates ingest schema | node_id, timestamp, cpu_usage set | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-112 | Unit | Telemetry Schemas | `TelemetryQuery` defaults | Default limit=100, offset=0 | limit=100, offset=0 | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-113 | Unit | Telemetry Schemas | `TelemetryQuery` custom | Custom limit/offset/node_id | Values match input | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-114 | Unit | Telemetry Schemas | `TelemetryAggregated` | Creates chart data structure | Arrays populated correctly | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-115 | Unit | Telemetry Schemas | `TelemetryStats` | Creates statistics object | All stat fields populated | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-116 | Unit | Database | `get_node_by_id` found | Returns existing node | Node with correct node_id returned | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-117 | Unit | Database | `get_node_by_id` not found | Returns None | Returns None | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-118 | Unit | Database | `create_node` | Inserts node, returns with ID | node.id assigned, status=ONLINE | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-119 | Unit | Database | `update_node` | Updates specified fields | hostname and cpu_cores updated | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-120 | Unit | Database | `update_node` not found | Raises ValueError | ValueError with "not found" message | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-121 | Unit | Database | `list_nodes` pagination | Returns correct page size | Page 1: 2 items, Page 2: 2 items, Page 3: 1 item | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-122 | Unit | Database | `add_telemetry` | Inserts telemetry, updates node | Telemetry saved, node.last_seen updated | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-123 | Unit | Database | `add_telemetry` node not found | Raises ValueError | ValueError with "not found" message | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-124 | Unit | Database | `get_telemetry` with filters | Returns filtered telemetry list | 3 items returned for node | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-125 | Unit | Database | `get_telemetry_for_node` | Returns telemetry for node | 1 item with cpu_usage=75.0 | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-126 | Unit | Database | `get_telemetry_stats` | Calculates correct aggregates | avg_cpu=30.0, max_cpu=50.0, count=5 | PASS | [python-unit-test.log](../logs/python-unit-test.log) |
| UT-127 | Unit | Database | `get_telemetry_stats` not found | Raises ValueError | ValueError with "not found" message | PASS | [python-unit-test.log](../logs/python-unit-test.log) |

**Python Unit Tests Summary:** 27 passed, 0 failed

---

## Integration Tests

| Test ID | Test Type | Component | Test Parameters/Input | Expected Result | Actual Result | Status | Evidence |
|---------|-----------|-----------|----------------------|-----------------|---------------|--------|----------|
| IT-001 | Integration | Node Registration | Rust edge node → TCP server → DB | Node registered and stored | Node registered, appears in `/api/v1/nodes/` | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-002 | Integration | Multi-node Registration | Node A + Node B → Server | Both registered independently | 2 nodes registered, both status=online | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-003 | Integration | Heartbeat | Active node → periodic heartbeat | last_seen updated periodically | last_seen updated after 15s wait | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-004 | Integration | Telemetry Transmission | Linux → Rust → TCP → DB → Dashboard | Real telemetry appears in dashboard | 10+ telemetry samples with real CPU/memory data | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-005 | Integration | Node Disconnection | Stop edge node → wait timeout → maintenance | Server marks node OFFLINE | 1 node marked offline, status=offline | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-006 | Integration | Node Reconnection | Stop node → restart with same ID | Node re-registers, status ONLINE | Node re-registered, status=online | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-007 | Integration | Invalid Input - Registration | Malformed HTTP registration | Server rejects with 422 | 422 returned for empty/invalid payload | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-007 | Integration | Invalid Input - Telemetry | Malformed telemetry (negative timestamp, memory>100) | Server rejects with 422 | 422 returned for invalid telemetry | PASS | [integration-test.log](../logs/integration-test.log) |
| IT-008 | Integration | Concurrent Nodes | 2 nodes sending telemetry simultaneously | Telemetry correctly associated per node | Each node's telemetry isolated correctly | PASS | [integration-test.log](../logs/integration-test.log) |

**Integration Tests Summary:** 9 passed, 0 failed

---

## System Tests

| Test ID | Test Type | Component | Test Parameters/Input | Expected Result | Actual Result | Status | Evidence |
|---------|-----------|-----------|----------------------|-----------------|---------------|--------|----------|
| ST-001 | System | End-to-End Edge Monitoring | Full pipeline: 2 nodes, 60s, 2s interval | Real telemetry visible in dashboard, both nodes online | Node A: 33 samples, Node B: 33 samples, both online | PASS | [system-test.log](../logs/system-test.log) |

---

## Benchmark Tests

| Test ID | Test Type | Component | Test Parameters/Input | Expected Result | Actual Result | Status | Evidence |
|---------|-----------|-----------|----------------------|-----------------|---------------|--------|----------|
| BT-001 | Benchmark | Model Size | FP32 vs INT8 ONNX | Size comparison | PENDING (no model exported yet) | PENDING | - |
| BT-002 | Benchmark | Inference Latency | 100 runs, same input | Mean, min, max, stddev | PENDING (no model exported yet) | PENDING | - |
| BT-003 | Benchmark | Edge Daemon Memory | Running daemon RSS over 30s | Memory consumption in MB | Mean=29.2MB, Min=29.2MB, Max=29.2MB | PASS | [benchmark.log](../logs/benchmark.log) |
| BT-004 | Benchmark | Edge Daemon CPU | Idle daemon CPU % over 30s | CPU overhead percentage | Mean=0.13%, Max=2.00% | PASS | [benchmark.log](../logs/benchmark.log) |
| BT-005 | Benchmark | Telemetry Message Size | JSON serialized telemetry | Size in bytes | 573 bytes | PASS | [benchmark.log](../logs/benchmark.log) |
| BT-006 | Benchmark | Telemetry Interval | Configured 2s interval over 30s | Actual interval measurement | Mean=2.00s, Stdev=0.00s | PASS | [benchmark.log](../logs/benchmark.log) |

---

## Overall Summary

| Category | Total | Passed | Failed | Pending |
|----------|-------|--------|--------|---------|
| Rust Unit Tests | 17 | 17 | 0 | 0 |
| Python Unit Tests | 27 | 27 | 0 | 0 |
| Integration Tests | 9 | 9 | 0 | 0 |
| System Tests | 1 | 1 | 0 | 0 |
| Benchmark Tests | 6 | 4 | 0 | 2 |
| **Total** | **60** | **58** | **0** | **2** |

---

## Notes

1. All unit tests use actual system calls (e.g., `/proc/stat`, `/proc/meminfo`) - no mocking of system data
2. Python unit tests use in-memory SQLite database for isolation
3. Rust unit tests include actual `/proc` parsing logic verification
4. Integration tests run against a live FastAPI server and real Rust edge daemon processes
5. Integration tests use the file-based SQLite database (not in-memory) to test the full stack
6. All telemetry values are real measurements from the Linux system (`/proc/stat`, `/proc/meminfo`, `/sys/class/thermal`, `/proc/uptime`, `/proc/loadavg`)
6. System tests and benchmark tests pending (Phases E and F)