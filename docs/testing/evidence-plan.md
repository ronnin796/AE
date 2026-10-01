# AetherEdge Part I — Evidence Plan for Mid-Defense

**Date:** 2026-10-01  
**Branch:** presentation  

---

## Evidence Figures for Mid-Defense Presentation

### FIG-T01: Server Running with Two Registered Nodes
- **Title**: "AetherEdge Server with Two Registered Edge Nodes"
- **What it demonstrates**: Server successfully accepts and stores node registrations via TCP binary protocol
- **Test support**: IT-001, IT-002
- **Location in report**: Section 4.2 (Integration Testing Results)
- **Capture method**: Screenshot of browser at `http://localhost:8080/api/v1/nodes` showing JSON response with 2 nodes, or dashboard Node Overview showing "Total: 2, Online: 2"

### FIG-T02: Dashboard Showing Two Online Nodes
- **Title**: "Dashboard Node Overview — Two Edge Nodes Online"
- **What it demonstrates**: React dashboard correctly fetches and displays node status from FastAPI server
- **Test support**: IT-001, IT-002, ST-001
- **Location in report**: Section 5 (System Testing), Section 7 (Dashboard Verification)
- **Capture method**: Screenshot of dashboard at `http://localhost:5173` showing Node Overview cards: "Total Nodes: 2", "Online: 2", "Offline: 0", plus two node cards with status indicators

### FIG-T03: Live CPU/Memory Telemetry Charts
- **Title**: "Real-Time Telemetry Visualization — CPU and Memory Usage"
- **What it demonstrates**: Telemetry data flows from Linux → Rust → TCP → FastAPI → SQLite → React → Recharts in real-time
- **Test support**: IT-004, ST-001
- **Location in report**: Section 4.2 (IT-004), Section 5 (ST-001)
- **Capture method**: Screenshot of dashboard Node Detail view showing four Recharts line charts (CPU, Memory, Temperature, Load) with visible data points

### FIG-T04: CPU Change During Workload
- **Title**: "Telemetry Response to CPU Load — Real Workload Detection"
- **What it demonstrates**: Telemetry reflects actual system load changes (not simulated/mocked data)
- **Test support**: IT-004, ST-001
- **Location in report**: Section 5 (ST-001), Section 8 (Live Demonstration)
- **Capture method**: Before/after screenshots or screen recording: (1) baseline CPU ~5-15%, (2) run `stress -c 4` on edge node, (3) observe CPU spike to 60-80% in dashboard within 2-4 seconds

### FIG-T05: Node B Disconnected
- **Title**: "Node Failure Detection — Heartbeat Timeout"
- **What it demonstrates**: Server correctly detects node disconnection via heartbeat timeout mechanism
- **Test support**: IT-005, ST-001
- **Location in report**: Section 4.2 (IT-005), Section 5 (ST-001), Section 8 (Live Demonstration)
- **Capture method**: Screenshot of dashboard after stopping Node B: Node B status shows "OFFLINE", Node A remains "ONLINE", Node Overview shows "Online: 1, Offline: 1"

### FIG-T06: Node B Reconnecting
- **Title**: "Node Recovery — Automatic Reconnection"
- **What it demonstrates**: Stopped node can re-register and resume telemetry transmission
- **Test support**: IT-006, ST-001
- **Location in report**: Section 4.2 (IT-006), Section 5 (ST-001), Section 8 (Live Demonstration)
- **Capture method**: Screenshot sequence: (1) Node B OFFLINE, (2) restart edge daemon for Node B, (3) Node B status transitions to ONLINE, telemetry resumes

### FIG-T07: AI Inference Demonstration
- **Title**: "ONNX Runtime Inference on Edge — FP32 Model Execution"
- **What it demonstrates**: Edge node can load ONNX model and execute inference via Rust ort crate
- **Test support**: BT-002, ML tooling verification
- **Location in report**: Section 6 (Performance Testing), Section 8 (AI Demonstration)
- **Capture method**: Terminal screenshot showing: (1) model loaded, (2) inference executed, (3) output tensor printed, (4) latency measured (~0.04 ms)

### FIG-T08: FP32 vs INT8 Benchmark Comparison
- **Title**: "Model Quantization Impact — FP32 vs INT8 (Conceptual)"
- **What it demonstrates**: Quantization pipeline exists; FP32 benchmark results shown; INT8 path identified as future work
- **Test support**: BT-001, BT-002, ML tooling
- **Location in report**: Section 6 (Performance Testing), Section 9 (Future Work)
- **Capture method**: Table/screenshot showing: FP32 size 4.31 KB, FP32 latency 0.04 ms, INT8 size/latency "Not measured (known ONNX compatibility issue)"

---

## Additional Evidence Artifacts

### Test Logs (Appendix)
| Artifact | Path | Description |
|----------|------|-------------|
| Rust Unit Test Output | `docs/testing/logs/rust-unit-test.log` | `cargo test` full output |
| Python Unit Test Output | `docs/testing/logs/python-unit-test.log` | `pytest tests/` full output |
| Integration Test Output | `docs/testing/logs/integration-test.log` | `pytest tests/integration/` full output |
| Benchmark Data | `docs/testing/benchmarks.md` | Formatted benchmark results |

### Source Code Evidence
| Component | Key Files | Purpose |
|-----------|-----------|---------|
| Edge Telemetry | `edge/src/telemetry/*.rs` | `/proc` parsing, real data collection |
| Protocol | `edge/src/protocol/*.rs` | MessagePack, binary framing |
| Server API | `server/app/api/*.py` | REST endpoints |
| Dashboard Charts | `dashboard/src/components/TelemetryCharts.tsx` | Recharts visualization |
| ML Export | `ml/src/export.py` | PyTorch → ONNX |
| ML Quantize | `ml/src/quantize.py` | FP32 → INT8 |

### Configuration Evidence
| File | Purpose |
|------|---------|
| `edge/Cargo.toml` | Rust dependencies, versions |
| `server/pyproject.toml` | Python dependencies, versions |
| `dashboard/package.json` | Frontend dependencies |
| `ml/pyproject.toml` | ML tooling dependencies |

---

## Evidence Capture Checklist

### Before Mid-Defense
- [ ] FIG-T01: Screenshot of `/api/v1/nodes` with 2 nodes
- [ ] FIG-T02: Screenshot of dashboard Node Overview (2 online)
- [ ] FIG-T03: Screenshot of Node Detail charts (CPU, Memory, Temp, Load)
- [ ] FIG-T04: Before/after screenshots of CPU load test
- [ ] FIG-T05: Screenshot of Node B OFFLINE
- [ ] FIG-T06: Screenshot of Node B back ONLINE after restart
- [ ] FIG-T07: Terminal screenshot of inference execution
- [ ] FIG-T08: Benchmark comparison table
- [ ] All test logs saved to `docs/testing/logs/`
- [ ] Benchmark data in `docs/testing/benchmarks.md`
- [ ] Reproduction guide tested on clean machine

### During Mid-Defense (Live)
- [ ] Live demo: Start server → Start 2 nodes → Open dashboard
- [ ] Live demo: Run CPU load → Observe spike
- [ ] Live demo: Stop node → Observe offline → Restart → Observe online
- [ ] Live demo: Run inference → Show output
- [ ] Live demo: Show test logs and benchmark results

---

## Evidence Mapping to Report Sections

| Report Section | Evidence Figures | Test Results |
|----------------|------------------|--------------|
| 1. Introduction | — | — |
| 2. Architecture | FIG-T01, FIG-T02 | IT-001, IT-002 |
| 3. Edge Daemon | FIG-T03, FIG-T04 | IT-004, UT-001..UT-017 |
| 4. Server | FIG-T01, FIG-T02 | IT-001..IT-009, UT-020..UT-065 |
| 5. Dashboard | FIG-T02, FIG-T03, FIG-T04 | ST-001 |
| 6. ML Tooling | FIG-T07, FIG-T08 | BT-001, BT-002 |
| 7. Testing | All FIGs, Logs | All UT, IT, ST, BT |
| 8. Live Demo | FIG-T04, FIG-T05, FIG-T06, FIG-T07 | ST-001, IT-004, IT-005, IT-006 |
| 9. Future Work | FIG-T08 | BT-001 (INT8), Part II plan |

---

## Notes for Examiners

1. **No Faked Data**: All telemetry values come from actual `/proc` and `/sys` reads. Temperature may show "N/A" on systems without thermal zones.
2. **Integration Test Isolation**: Some integration tests fail in full suite due to shared server process state (test infrastructure limitation). All pass individually.
3. **INT8 Quantization**: Known ONNX Runtime compatibility issue with demo model. FP32 path fully functional.
4. **Reproducibility**: All steps documented in `docs/testing/reproduction.md` with exact commands.
5. **Academic Honesty**: All results are from actual execution. Limitations explicitly documented.