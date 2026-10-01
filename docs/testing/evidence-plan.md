# AetherEdge Part I — Evidence Plan for Mid-Defense

**Date:** 2026-10-01  
**Branch:** mid-defense-hardening  

---

## Purpose

This document lists all figures, screenshots, and evidence items needed for the mid-defense presentation and final report. Each item maps to a specific test result or demonstration moment.

---

## Figures for Written Report

| Figure ID | Title | Source | Test Support | Report Section |
|-----------|-------|--------|--------------|----------------|
| FIG-01 | System Architecture Diagram | Draw.io / Mermaid | — | 1. Introduction |
| FIG-02 | Rust Unit Test Results | `rust-unit-test.log` | UT-001 to UT-017 | 3. Unit Testing |
| FIG-03 | Python Unit Test Results | `python-unit-test.log` | UT-101 to UT-127 | 3. Unit Testing |
| FIG-04 | Integration Test Matrix | `integration-test.log` | IT-001 to IT-008 | 4. Integration Testing |
| FIG-05 | System Test Timeline | `system-test.log` | ST-001 | 5. System Testing |
| FIG-06 | Benchmark Results Table | `benchmark.log` | BT-003 to BT-006 | 6. Performance Testing |
| FIG-07 | Edge Daemon Memory Profile | `benchmark.log` (BT-003) | BT-003 | 6.1 Resource Usage |
| FIG-08 | Edge Daemon CPU Profile | `benchmark.log` (BT-004) | BT-004 | 6.1 Resource Usage |
| FIG-09 | Telemetry Message Size | `benchmark.log` (BT-005) | BT-005 | 6.2 Network |
| FIG-10 | Interval Accuracy | `benchmark.log` (BT-006) | BT-006 | 6.2 Network |

---

## Screenshots for Live Demonstration

| Screenshot ID | Description | Capture Method | When to Capture |
|---------------|-------------|----------------|-----------------|
| DEMO-01 | Dashboard Overview — 2 nodes online | Browser screenshot | After starting both nodes |
| DEMO-02 | Node A Detail View — CPU/RAM/Temp charts | Browser screenshot | Node A selected |
| DEMO-03 | Node B Detail View — CPU/RAM/Temp charts | Browser screenshot | Node B selected |
| DEMO-04 | Node Overview Cards — 2 Online, 0 Offline | Browser screenshot | Initial state |
| DEMO-05 | CPU Spike During Workload | Browser screenshot (animated GIF preferred) | During `stress-ng` on Node A |
| DEMO-06 | Node B Offline State | Browser screenshot | After killing Node B + 15s wait |
| DEMO-07 | Node B Reconnecting | Browser screenshot (animated GIF) | After restarting Node B |
| DEMO-08 | HTTP API Response — Node List | Terminal + browser dev tools | During demo |
| DEMO-09 | HTTP API Response — Telemetry | Terminal + browser dev tools | During demo |
| DEMO-10 | Edge Daemon Logs — Registration | Terminal screenshot | At node startup |
| DEMO-11 | Edge Daemon Logs — Telemetry | Terminal screenshot | During operation |

---

## Terminal Outputs for Report

| Output ID | Description | Source File | Report Section |
|-----------|-------------|-------------|----------------|
| TERM-01 | `cargo test` output | `rust-unit-test.log` | 3.1 |
| TERM-02 | `pytest tests/unit/` output | `python-unit-test.log` | 3.2 |
| TERM-03 | `pytest tests/integration/` output | `integration-test.log` | 4 |
| TERM-04 | `pytest tests/system/` output | `system-test.log` | 5 |
| TERM-05 | `pytest tests/benchmark/` output | `benchmark.log` | 6 |
| TERM-05 | Edge daemon startup logs | Live terminal | Demo |
| TERM-06 | Server startup logs | `server/test_server.log` | Demo |

---

## Live Demonstration Checklist

| Step | Action | Evidence Captured |
|------|--------|-------------------|
| 1 | Start server | TERM-06 |
| 2 | Start Node A | DEMO-10, DEMO-01 |
| 3 | Start Node B | DEMO-01 |
| 4 | Show dashboard overview | DEMO-01, DEMO-04 |
| 5 | Select Node A | DEMO-02 |
| 6 | Show Node B | DEMO-03 |
| 7 | Run workload on Node A | DEMO-05 (GIF) |
| 8 | Kill Node B | DEMO-06 |
| 9 | Restart Node B | DEMO-07 (GIF) |
| 9 | Show API responses | DEMO-08, DEMO-09 |

---

## Evidence Mapping to Test Results

| Test Category | Evidence Type | Files |
|---------------|---------------|-------|
| Unit Tests | Log files | `rust-unit-test.log`, `python-unit-test.log` |
| Integration Tests | Log file + screenshots | `integration-test.log`, DEMO-01..DEMO-07 |
| System Test | Log file + terminal output | `system-test.log`, TERM-04 |
| Benchmarks | Log file + terminal output | `benchmark.log`, TERM-05 |
| Live Demo | Screenshots + GIFs | DEMO-01..DEMO-11 |

---

## File Naming Convention

All evidence files follow: `<type>-<id>-<description>.<ext>`

Examples:
- `screenshot-demo-01-dashboard-overview.png`
- `gif-demo-05-cpu-spike.gif`
- `terminal-rust-unit-tests.txt`
- `log-integration-tests.txt`

---

## Storage

All evidence stored in:
```
docs/testing/
├── logs/                    # Raw test outputs
├── evidence/                # Screenshots, GIFs, terminal captures
│   ├── screenshots/
│   ├── gifs/
│   └── terminals/
└── reports/                 # Generated reports
```

---

## Capture Instructions

### Screenshots
- Use `gnome-screenshot` or `flameshot`
- Capture full browser window for dashboard
- Include URL bar to show localhost
- Resolution: 1920x1080 minimum

### GIFs (Animated)
- Use `peek` or `byzanz-record`
- 10-15 seconds duration
- 10 FPS, 800x600 minimum
- Focus on changing metrics (CPU spike, node status change)

### Terminal Captures
- Use `script` command or terminal recorder
- `script -c "cargo test" terminal-rust-unit.txt`
- Preserve ANSI colors if possible

---

## Backup Plan

If live demo fails:
1. Pre-recorded GIFs of all demo steps
- Pre-captured screenshots of all dashboard states
- Terminal outputs saved as text files
- Video recording of full demo as last resort

---

*Prepared: 2026-10-01*  
*All evidence from actual test execution — no fabricated content*