# AetherEdge

**A Distributed, Ultra-Lightweight Edge AI Inference Engine & Monitor**

Final-year Computer Engineering project — Part I (Foundation Prototype)

---

## Overview

AetherEdge is a distributed system for running AI inference at the edge with real-time system telemetry monitoring. It consists of lightweight Rust daemons deployed on edge nodes, a central FastAPI server for coordination and data persistence, and a React dashboard for visualization.

### Part I Scope (Current)

This repository contains the **Part I prototype** (~50-60% of final system):

| Component | Status |
|-----------|--------|
| Rust Edge Daemon | ✅ Core + Telemetry + Networking |
| FastAPI Server | ✅ Node Registry + Telemetry Ingestion + SQLite |
| Communication Protocol | ✅ MessagePack over TCP |
| Linux Telemetry | ✅ CPU, Memory, Temperature, Uptime, Load |
| Node Registration | ✅ Register + Heartbeat + ONLINE/OFFLINE/DEGRADED/Maintenance |
| AI Inference | ✅ ONNX Runtime local inference |
| INT8 Quantization | ✅ Static quantization + benchmarks |
| React Dashboard | ✅ **Node list + Interactive Telemetry Charts + Node Control** |

### Part II Scope (Future)

| Feature | Planned |
|---------|---------|
| Persistent buffering & synchronization | 🔲 |
| Remote model deployment & registry | 🔲 |
| TLS/mTLS & authentication | 🔲 |
| Resource-aware scheduling | 🔲 |
| Advanced dashboard (alerts, model mgmt) | 🔲 |
| PostgreSQL + partitioning | 🔲 |
| Large-scale benchmarking | 🔲 |

---

## Architecture

```
┌─────────────┐     TCP/MessagePack      ┌──────────────┐
│  Edge Node  │ ◄──────────────────────► │ FastAPI      │
│  (Rust)     │  Register, Heartbeat,    │ Server       │
│             │  Telemetry, Inference,   │              │
│  - /proc    │  Commands                │  - SQLite    │
│  - /sys     │                          │  - REST API  │
│  - ONNX RT  │                          │  - TCP Cmd   │
└─────────────┘                          └──────┬───────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │     React Dashboard     │
                                    │  - Cluster overview     │
                                    │  - Node grid (search)   │
                                    │  - Interactive charts   │
                                    │  - Node control (tabs)  │
                                    │  - Dark/Light theme     │
                                    └─────────────────────────┘
```

---

## Quickstart

### Prerequisites

- **Rust**: 1.75+ (`rustup`)
- **Python**: 3.11+ with `uv` (recommended) or `pip`
- **Node.js**: 20+ with `npm` or `pnpm`
- **Linux**: `/proc` and `/sys` access (native)

### Development Setup

```bash
# One-time setup
./scripts/dev_setup.sh

# Or manually:
cd edge && cargo build
cd ../server && uv sync
cd ../ml && uv sync
cd ../dashboard && npm install
```

### Running the System

**Terminal 1 — FastAPI Server:**
```bash
cd server && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Terminal 2 — Edge Node A:**
```bash
cd edge && cargo run -- --node-id node-a --server-addr 127.0.0.1:8080
```

**Terminal 3 — Edge Node B:**
```bash
cd edge && cargo run -- --node-id node-b --server-addr 127.0.0.1:8080
```

**Browser — Dashboard:**
```bash
cd dashboard && npm run dev
# Open http://localhost:5173
```

---

## Project Structure

```
aetheredge/
├── edge/              # Rust edge daemon
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── config.rs
│       ├── node.rs
│       ├── telemetry/
│       ├── protocol/
│       ├── networking/
│       ├── inference/
│       └── logging.rs
├── server/            # FastAPI backend
│   ├── pyproject.toml
│   └── app/
├── ml/                # Model preparation & quantization
│   ├── pyproject.toml
│   └── src/
├── dashboard/         # React monitoring UI
│   ├── package.json
│   └── src/
├── docs/              # Documentation
├── scripts/           # Operational scripts
└── docker-compose.yml # Multi-node demo
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, component interactions |
| [Telemetry](docs/telemetry.md) | `/proc`/`/sys` collectors, data formats |
| [Communication](docs/communication.md) | Protocol, serialization, message types |
| [Inference](docs/inference.md) | ONNX Runtime integration, model loading |
| [Quantization](docs/quantization.md) | INT8 static quantization, math, benchmarks |
| [Database](docs/database.md) | Schema, migrations, query patterns |
| [Testing](docs/testing.md) | Test strategy, running tests |
| [Benchmarking](docs/benchmarking.md) | Methodology, results, reproduction |
| [Part II Roadmap](docs/part2-roadmap.md) | Extension plan from Part I foundation |

---

## Configuration

### Edge Daemon (`edge/config.toml`)

```toml
[node]
node_id = "edge-node-1"      # Unique identifier
hostname = ""                # Auto-detected if empty

[server]
address = "127.0.0.1:8080"   # FastAPI server address
reconnect_interval = 5       # Seconds

[telemetry]
interval = 2                 # Collection interval (seconds)
collect_cpu = true
collect_memory = true
collect_temperature = true
collect_uptime = true
collect_load = true

[inference]
model_path = "models/model.onnx"
```

### Server (`server/.env`)

```env
DATABASE_URL=sqlite:///./aetheredge.db
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=info
NODE_TIMEOUT=30  # Seconds before node marked OFFLINE
```

---

## License

MIT — Academic project, free for educational use.

---

## Author

Computer Engineering Final Year Project — AetherEdge Part I