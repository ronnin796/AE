# AetherEdge

**A Distributed, Ultra-Lightweight Edge AI Inference Engine & Monitor**

Final-year Computer Engineering project — Part I (Foundation Prototype)

---

## Overview

AetherEdge is a distributed system for running AI inference at the edge with real-time system telemetry monitoring. It consists of lightweight Rust daemons deployed on edge nodes, a central FastAPI server for coordination and data persistence, and a React dashboard for visualization.

### Part I Scope (Current)

This repository contains the **Part I prototype** (~65-75% of final system):

| Component | Status | Evidence |
|-----------|--------|----------|
| Rust Edge Daemon | ✅ Core + Telemetry + Networking | `edge/src/main.rs`, `telemetry/`, `networking/` |
| FastAPI Server | ✅ Node Registry + Telemetry Ingestion + SQLite | `server/app/main.py`, `models/`, `services/` |
| Communication Protocol | ✅ MessagePack over TCP (AETH magic) | `edge/src/protocol/`, `server/app/tcp_server.py` |
| Linux Telemetry | ✅ CPU, Memory, Temperature, Uptime, Load | `edge/src/telemetry/cpu.rs`, `memory.rs`, `temperature.rs`, `system.rs` |
| Node Registration | ✅ Register + Heartbeat + ONLINE/OFFLINE/DEGRADED/Maintenance | `server/app/api/nodes.py`, `tcp_server.py` |
| AI Inference (ONNX Runtime) | 🧪 Engine exists, not fully wired | `edge/src/inference/engine.rs` — scaffold |
| INT8 Quantization | ✅ Static + Dynamic + Benchmarks | `ml/src/quantize.py`, `benchmark.py` |
| React Dashboard | ✅ Node list + Charts + Node Control | `dashboard/src/components/` |

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
│       ├── main.rs           # Entry point, CLI, task orchestration
│       ├── config.rs         # TOML + env config loading
│       ├── node.rs           # NodeIdentity, NodeMetadata (sysinfo + /proc)
│       ├── lib.rs            # Public exports
│       ├── logging.rs        # tracing setup
│       ├── telemetry/        # CPU, Memory, Temperature, System collectors
│       │   ├── mod.rs        # TelemetryCollector orchestrator
│       │   ├── cpu.rs        # /proc/stat delta sampling
│       │   ├── memory.rs     # /proc/meminfo parsing
│       │   ├── temperature.rs # /sys/class/thermal zones
│       │   └── system.rs     # /proc/uptime, /proc/loadavg
│       ├── protocol/         # Binary protocol (AETH + MessagePack)
│       │   ├── mod.rs        # Envelope, MessageType, encode/decode
│       │   └── messages.rs   # Register, Heartbeat, Telemetry, Inference, ServerCommand
│       ├── networking/       # TCP client with auto-reconnect
│       │   └── mod.rs        # NetworkClient, sequence numbers
│       └── inference/        # ONNX Runtime inference
│           ├── mod.rs
│           └── engine.rs     # InferenceEngine (scaffold)
├── server/            # FastAPI backend
│   ├── pyproject.toml
│   └── app/
│       ├── main.py           # FastAPI app, lifespan, routers
│       ├── config.py         # Settings via pydantic-settings
│       ├── database.py       # SQLAlchemy async + aiosqlite
│       ├── tcp_server.py     # Binary protocol TCP server
│       ├── models/           # Node, Telemetry (SQLAlchemy)
│       ├── schemas/          # Pydantic v2 request/response
│       ├── services/         # Database CRUD, node_service, heartbeat_service, inference_service
│       └── api/              # REST endpoints (nodes, telemetry)
├── ml/                # Model preparation & quantization
│   ├── pyproject.toml
│   └── src/
│       ├── export.py         # PyTorch → ONNX export
│       ├── quantize.py       # Static/dynamic INT8 quantization
│       ├── benchmark.py      # FP32 vs INT8 latency/size comparison
│       └── utils.py          # Metadata I/O, size formatting
├── dashboard/         # React monitoring UI
│   ├── package.json
│   └── src/
│       ├── main.tsx          # Entry point
│       ├── App.tsx           # Layout, routing, providers
│       ├── api/client.ts     # Axios + React Query hooks
│       ├── hooks/            # useNodes, useTelemetry
│       ├── components/       # NodeList, NodeCard, NodeDetail, TelemetryCharts, etc.
│       ├── context/          # ThemeContext, DebugContext
│       └── types/            # TypeScript interfaces
├── docs/              # Documentation
│   ├── architecture.md
│   ├── telemetry.md
│   ├── communication.md
│   ├── inference.md
│   ├── quantization.md
│   ├── database.md
│   ├── testing.md
│   ├── benchmarking.md
│   ├── part2-roadmap.md
│   ├── audit.md
│   └── testing/
├── scripts/           # Operational scripts
└── docker-compose.yml # Multi-node demo (planned)
```

---

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Architecture](docs/architecture.md) | System design, component interactions | ✅ |
| [Telemetry](docs/telemetry.md) | `/proc`/`/sys` collectors, data formats | ✅ |
| [Communication](docs/communication.md) | Protocol, serialization, message types | ✅ |
| [Inference](docs/inference.md) | ONNX Runtime integration, model loading | ✅ |
| [Quantization](docs/quantization.md) | INT8 static quantization, math, benchmarks | ✅ |
| [Database](docs/database.md) | Schema, migrations, query patterns | ✅ |
| [Testing](docs/testing.md) | Test strategy, running tests | ✅ |
| [Benchmarking](docs/benchmarking.md) | Methodology, results, reproduction | ✅ |
| [Part II Roadmap](docs/part2-roadmap.md) | Extension plan from Part I foundation | 🔵 |

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

## Testing

```bash
# Rust unit tests
cd edge && cargo test

# Python unit tests
cd server && uv run pytest -v

# Dashboard build verification
cd dashboard && npm run build

# ML tooling (requires onnxruntime, torch)
cd ml && python -m src.export && python -m src.quantize && python -m src.benchmark
```

**Test Results:** 53 tests passing (24 Python unit + inline Rust). See `docs/testing/final-test-summary.md` and `docs/testing/logs/` for evidence.

---

## License

MIT — Academic project, free for educational use.

---

## Author

Computer Engineering Final Year Project — AetherEdge Part I

---

## Implementation Status

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for detailed feature-by-feature audit with evidence references.