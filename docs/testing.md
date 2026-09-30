# AetherEdge Testing — Test Strategy

## Overview

This document describes the testing strategy for the AetherEdge Part I prototype, including test types, coverage, and execution.

## Testing Objectives

### Part I Testing Goals

1. **Functionality**: Verify all core components work correctly
2. **Reliability**: Ensure robust error handling
3. **Performance**: Measure response times and throughput
4. **Integration**: Test end-to-end system behavior
5. **Compatibility**: Verify cross-component interactions

### Part II Future Testing

- Unit Tests: Component-level testing
- Integration Tests: System-level validation
- Load Tests: Performance benchmarking
- Chaos Tests: Fault tolerance and recovery

## Test Types

### 1. Unit Tests

**Description**: Test individual components in isolation

**Examples**:
- Rust telemetry collector tests
- Python model export tests
- Protocol serialization tests
- Database CRUD operations

**Tools**:
- Rust: cargo test
- Python: pytest
- JavaScript: npm test

### 2. Integration Tests

**Description**: Test component interactions

**Examples**:
- Edge daemon to Server communication
- Server to Database to Dashboard flow
- Multi-node registration scenarios

**Tools**:
- Rust: tokio::test
- Python: pytest-httpx

### 3. Performance Tests

**Description**: Measure system performance

**Examples**:
- Telemetry collection latency
- Model inference speed comparison
- Network communication overhead

**Tools**:
- Rust: criterion
- Python: benchmark framework

## Test Coverage Targets

### Part I Coverage Matrix

| Component | Target Coverage | Notes |
|-----------|-----------------|-------|
| Rust Edge Daemon | 80% | Focus on telemetry and networking |
| FastAPI Server | 70% | Focus on API endpoints |
| Database Layer | 85% | Focus on CRUD operations |
| Protocol Layer | 90% | Focus on message types |
| Dashboard | 60% | Focus on critical paths |
| ML Tooling | 70% | Focus on export and quantize |

## Test Execution

### Rust Tests

```bash
cd edge
cargo test --all
cargo test --lib
```

### Python Tests

```bash
cd server
uv run pytest tests/ -v

cd ml
uv run pytest tests/ -v
```

### Dashboard Tests

```bash
cd dashboard
npm test
```

### Integration Tests

```bash
# Start server
cd server && uv run uvicorn app.main:app --reload &

# Start edge nodes
cd edge && cargo run -- --node-id node-a &
cd edge && cargo run -- --node-id node-b &

# Run integration tests
cd server && uv run pytest tests/integration/ -v
```

## Key Test Cases

### Rust Telemetry Tests

- CPU usage calculation accuracy
- Memory usage calculation accuracy
- Temperature sensor parsing
- System uptime and load average parsing

### Protocol Tests

- MessagePack serialization/deserialization
- Envelope encoding/decoding
- Message type validation
- Error handling

### Server Tests

- Node registration
- Heartbeat processing
- Telemetry ingestion
- Database queries

### Integration Tests

- Full telemetry pipeline
- Multi-node scenarios
- Edge-to-server communication

## Test Data

### Mock Data

```json
{
  "node_id": "test-node",
  "hostname": "test-host",
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "temperature": 45.0,
  "uptime": 3600
}
```

## Test Environment

### Prerequisites

- Rust 1.75+
- Python 3.11+
- Node.js 20+
- SQLite

### CI/CD Integration

Planned for Part II:
- Automated test runs on push
- Test coverage reports
- Performance regression detection

## Known Limitations

### Part I

- No automated test runner for dashboard components
- Limited integration test coverage
- No performance regression detection

### Part II Planned

- Full CI/CD pipeline
- Automated performance testing
- Chaos engineering tests
- Load testing framework

## References

- Rust Testing: https://doc.rust-lang.org/book/ch11-00-testing.html
- Pytest: https://docs.pytest.org/
- Jest: https://jestjs.io/

## Next Steps

1. Write unit tests for telemetry collectors
2. Add integration tests for protocol layer
3. Create dashboard component tests
4. Add performance benchmarks
5. Set up CI/CD pipeline (Part II)

---

*Document generated: 2026-09-30*