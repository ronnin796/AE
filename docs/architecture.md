# AetherEdge — Architecture Documentation

## Overview

**AetherEdge** is a distributed, ultra-lightweight edge AI inference engine and monitor designed for academic final-year projects. The system is structured in two parts:

- **Part I**: Foundation prototype (~50-60% of final system)
- **Part II**: Advanced features and production readiness (~40-50%)

This document describes the Part I architecture and component interactions.

---

## 🏗️ System Architecture

### High-Level Diagram

```text
                      ┌─────────────────────┐
                      │   FastAPI Server    │
                      │   (Python, Uvicorn) │
                      └───────┬─────────────┘
                              │
                    ┌───────────▼───────────┐
                    │  MessagePack Protocol │
                    │  (rmp-serde, compact)│
                    └───────┬─────────────┘
                            │
              ┌──────────────▼───────────────┐
              │          Rust Edge Daemons   │
              │  (Tokio async, /proc, /sys) │
              └──────────────┬───────────────┘
                           │
              ┌────────────────▼─────────────┐
              │   React + TypeScript UI      │
              │  (Vite, Recharts, TanStack)  │
              └────────────────┬─────────────┘
                                 │
                   TCP/IP Network
```

---

## 📦 Component Breakdown

### 1. Rust Edge Daemon

**Purpose**: Collect Linux system telemetry, manage node identity, communicate with server, support local AI inference

**Key Features**:
- System telemetry collection (`/proc`, `/sys`)
- Node identity and metadata management
- MessagePack protocol for communication
- Heartbeat mechanism for liveness detection
- ONNX Runtime inference engine

**Core Modules**:
- `main.rs` — Entry point, CLI args, initialization
- `config.rs` — Configuration loading (TOML + env vars)
- `logging.rs` — Structured logging (tracing subscriber)
- `node.rs` — Node identity (UUID, hostname, CPU/memory info)
- `telemetry/` — Collectors for CPU, memory, temperature, system
- `protocol/` — MessagePack envelope and message types
- `networking/` — TCP client/server communication
- `inference/` — ONNX Runtime integration

**Dependencies**:
- `tokio` — Async runtime
- `rmp-serde` — MessagePack serialization
- `ort` — ONNX Runtime Rust bindings
- `sysinfo` — System information (fallback)
- `clap` — CLI argument parsing
- `serde` — Data serialization

### 2. FastAPI Server

**Purpose**: Central coordination, data persistence, API endpoints, node management

**Key Features**:
- REST API for node registration and status
- SQLite database for data persistence
- Telemetry ingestion and storage
- Heartbeat monitoring and health checks
- API documentation (Swagger/OpenAPI)

**Core Modules**:
- `app/main.py` — FastAPI app initialization, routes
- `app/config.py` — Pydantic Settings configuration
- `app/database.py` — SQLAlchemy async engine
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response validation
- `app/api/` — Route handlers (nodes, telemetry)
- `app/services/` — Business logic services
- `app/api/__init__.py` — Router organization

**Dependencies**:
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `sqlalchemy` — ORM and DB abstraction
- `pydantic` — Validation and settings
- `alembic` — Database migrations

### 3. React Dashboard

**Purpose**: Real-time monitoring interface, node overview, telemetry visualization

**Key Features**:
- Node overview with status badges
- Live telemetry charts (CPU, memory, temperature)
- Node details and telemetry summaries
- Real-time updates via polling
- Responsive design (mobile-friendly)

**Core Components**:
- `src/main.tsx` — React entry point
- `src/App.tsx` — Main application layout
- `src/types/index.ts` — TypeScript type definitions
- `src/api/client.ts` — Axios API client wrapper
- `src/hooks/useNodes.ts` — React Query for node data
- `src/hooks/useTelemetry.ts` — React Query for telemetry (includes useDebugEvents, useAllNodesTelemetrySummary)
- `components/NodeList.tsx` — Node overview list
- `components/NodeCard.tsx` — Individual node card view with telemetry preview
- `components/TelemetryCharts.tsx` — Recharts visualization
- `components/StatusBadge.tsx` — Status indicator component
- `components/NodeOverview.tsx` — Stats summary box
- `components/NavBar.tsx` — Application navigation
- `components/TelemetryDashboard.tsx` — Node-specific telemetry
- `components/DebugPanel.tsx` — **NEW v2.0.23**: System event stream viewer
- `context/DebugContext.tsx` — **NEW v2.0.23**: Debug event state management (backend + manual events)

**Dependencies**:
- `react` + `react-dom` — UI library
- `vite` — Dev server and build tool
- `@tanstack/react-query` — Data fetching and caching
- `recharts` — Charting library
- `axios` — HTTP client

### 4.1 Telemetry Summary & Debug API (v2.0.23)

**Telemetry Summary Endpoint**: `GET /api/v1/telemetry/summary/all`

Purpose: Efficiently fetch telemetry statistics for ALL nodes in a single database query, avoiding N+1 API calls when rendering NodeCard previews in the node list.

- Single query with LEFT JOIN (nodes → telemetry) grouped by node_id
- Returns: count, avg/max cpu, avg/max memory, avg/max temperature, latest_timestamp per node
- Polling interval: 5 seconds (via React Query)
- Used by: NodeList → NodeCard telemetry preview section

**Debug API Endpoints**:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/debug/events` | Reconstructed event stream from DB (registrations, heartbeats, telemetry, disconnections) |
| `GET /api/v1/debug/stats` | System-wide statistics (node counts, telemetry points, latest per node) |
| `GET /api/v1/debug/connections` | Active TCP connections from edge nodes |

Event reconstruction sources:
- Telemetry table → "telemetry" events with metric values
- Nodes table created_at → "connect" events (registration)
- Nodes table status + last_seen → "heartbeat"/"disconnect" events

DebugPanel features:
- Auto-scroll toggle
- Event type filter (connect, disconnect, heartbeat, telemetry, command, error)
- Manual event clearing
- 5-second polling interval
- Merges backend events with frontend-generated events (node selection, commands, refresh)

### 4. Protocol Layer

**Purpose**: Lightweight binary serialization for edge↔server communication

**Message Types**:
- `REGISTER` — Node registration request
- `REGISTER_RESPONSE` — Server registration response
- `HEARTBEAT` — Periodic liveness check
- `HEARTBEAT_ACK` — Server acknowledgment
- `TELEMETRY` — System metric transmission
- `INFERENCE_RESULT` — AI inference output
- `ERROR` — Error reporting

**Serialization**: MessagePack (`rmp-serde`)
- 3-5× smaller than JSON equivalent
- Zero-copy deserialization in Rust
- Schema evolution friendly (field additions don't break)

**Envelope Format**:
```
[4 bytes magic: "AETH"]
[4 bytes payload length: big-endian u32]
[payload: serialized message]
```

### 5. System Infrastructure

**Database**: SQLite (Part I) → PostgreSQL (Part II)
- `nodes` table: Node registry with status tracking
- `telemetry` table: Time-series metric storage
- Relationships: One-to-many (node → telemetry data points)

**Networking**:
- TCP/IP for reliable transport
- Automatic reconnection with exponential backoff
- Connection pooling for multiple nodes
- Timeout-based heartbeat detection

**Configuration**:
- Edge: `config.toml` + environment variables
- Server: `.env` file + Pydantic Settings
- Dashboard: Environment variables for API base URL
- Version-aware configuration for Part II upgrades

---

## 🔄 Data Flow

### Telemetry Pipeline

```text
Linux System (/proc, /sys)
     ↓
Rust Telemetry Collectors
     ↓
Telemetry Struct (CPU, Memory, Temp, etc.)
     ↓
MessagePack Serialization
     ↓
TCP → FastAPI Server
     ↓
SQLite Database (nodes + telemetry tables)
     ↓
React Dashboard (polling every 2-5 seconds)
     ↓
User Interface (charts, status badges, node list)
```

### Node Registration Flow

```text
Edge Node (start)
     ↓
Generate Node Identity (UUID + system info)
     ↓
Send REGISTER message (MessagePack)
     ↓
Server validates and stores node
     ↓
Return RegisterResponse (success/failure)
     ↓
Node status: ONLINE
     ↓
Periodic HEARTBEAT messages (every 10s)
     ↓
Server updates last_seen timestamp
     ↓
Server status: ONLINE if recent heartbeat
     ↓
Server status: OFFLINE if heartbeat timeout (30s)
```

### Inference Pipeline

```text
Python Model (PyTorch)
     ↓
Export to ONNX format
     ↓
INT8 Quantization (optional)
     ↓
Edge Node loads ONNX model
     ↓
ONNX Runtime inference engine
     ↓
Local inference execution
     ↓
InferenceResult message (MessagePack)
     ↓
Server receives and stores
     ↓
Dashboard displays results
```

---

## 🔌 Communication Protocols

### MessagePack Protocol Details

**Header Structure**:
```
Magic Bytes: "AETH" (4 bytes)
Payload Length: Big-endian u32 (4 bytes)
Payload: Serialized MessagePack message
```

**Message Format**:
```
[MessageType: u8]
[Sequence Number: u64]
[Timestamp: u64]
[Payload: byte array]
```

**Message Types**:
| Type | Value | Direction | Description |
|------|-------|-----------|-------------|
| Register | 1 | Edge → Server | Node registration |
| RegisterResponse | 2 | Server → Edge | Registration result |
| Heartbeat | 3 | Edge → Server | Liveness check |
| HeartbeatAck | 4 | Server → Edge | Acknowledgment |
| Telemetry | 5 | Edge → Server | System metrics |
| InferenceResult | 7 | Edge → Server | AI output |
| Error | 255 | Either | Error reporting |

---

## 🗄️ Database Schema

### Part I: SQLite Schema

```sql
-- Nodes table
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,       -- Unique node identifier
    hostname TEXT NOT NULL,             -- Human-readable hostname
    os TEXT NOT NULL,                   -- Operating system name
    os_version TEXT,                    -- OS version
    kernel_version TEXT,                -- Kernel version
    cpu_brand TEXT,                     -- CPU model/brand
    cpu_cores INTEGER,                 -- Number of CPU cores
    total_memory INTEGER,              -- Total memory (bytes)
    version TEXT,                      -- Software version
    arch TEXT,                         -- CPU architecture
    status TEXT DEFAULT 'offline',     -- ONLINE, OFFLINE, DEGRADED
    last_seen DATETIME,                -- Last heartbeat timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry table
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL,          -- FK to nodes.id
    timestamp DATETIME NOT NULL,       -- Data point timestamp
    cpu_usage REAL,                    -- CPU percentage
    memory_usage REAL,                 -- Memory percentage
    temperature REAL,                  -- Celsius
    uptime INTEGER,                    -- Seconds
    load_1 REAL,                       -- 1-min load average
    load_5 REAL,                       -- 5-min load average
    load_15 REAL,                      -- 15-min load average
    processes_running INTEGER,         -- Running processes count
    processes_total INTEGER,           -- Total processes count
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);
```

### Part II: PostgreSQL Migration (Planned)

- Connection pooling with `pgx`
- Partitioned telemetry tables for time-series optimization
- Retention policies (auto-archive old data)
- Read replicas for dashboard queries
- Enhanced schema with capabilities, tags, metadata

---

## 🛠️ Development Environment

### Prerequisites

**Rust**:
```bash
rustup default stable
rustup component add rustfmt
rustup component add clippy
```

**Python**:
```bash
python3 --version  # Should be 3.11+
pip install uv  # Fast Python package manager
uv sync  # Install dependencies
```

**Node.js**:
```bash
node --version  # Should be 20+
npm install  # Install frontend dependencies
npm run dev  # Start development server
```

### Project Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd aetheredge

# 2. Setup development environment
./scripts/dev_setup.sh

# 3. Verify all components compile
cd edge && cargo check  # Should succeed
cd server && uv sync   # Should succeed
cd dashboard && npm install  # Should succeed

# 4. Start the system
# Terminal 1: FastAPI Server
cd server && uv run uvicorn app.main:app --reload

# Terminal 2: Edge Node A
cd edge && cargo run -- --node-id node-a

# Terminal 3: Edge Node B
cd edge && cargo run -- --node-id node-b

# Browser: http://localhost:5173
```

### IDE Configuration

**VS Code**:
- Install Rust Analyzer extension
- Install Python extension
- Install ESLint/Prettier for TypeScript
- Use `.vscode/settings.json` for formatting

**Settings**:
```json
{
  "rust-analyzer.checkOnSave": true,
  "python.linting.enabled": true,
  "typescript.format.enable": true,
  "editor.defaultFormatter": "esbenp"
}
```

---

## 📦 Dependency Management

### Rust (Cargo.toml)

Key dependencies organized by feature:

```toml
[dependencies]
# Core runtime
tokio = { version = "1.38", features = ["full"] }

# Serialization
serde = { version = "1.0", features = ["derive"] }
rmp-serde = "1.1"        # MessagePack
clap = { version = "4.5", features = ["derive"] }  # CLI

# System information
sysinfo = "0.30"         # System metrics (fallback)

// ONNX Runtime for inference
ort = { version = "2.0.0-rc.13", features = ["load-dynamic"] }

// Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "fmt", "json"] }

// Configuration
config = "0.14"
toml = "0.8"

// System
anyhow = "1.0"
bytes = "1.5"
uuid = { version = "1.7", features = ["v4", "serde"] }
```

### Python (pyproject.toml)

```toml
[project.dependencies]
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.4.0",
    "black>=24.0.0",
]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^2.10.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "vite": "^5.0.0",
    "eslint": "^8.50.0",
    "typescript": "^5.2.0"
  }
}
```

---

## 📐 Design Rationale

### Why MessagePack?

1. **Compact**: 3-5× smaller than JSON for typical telemetry payloads
2. **Efficient**: Zero-copy deserialization in Rust
3. **Evolution-friendly**: Adding new fields doesn't break existing clients
4. **Binary-safe**: Handles arbitrary byte data

### Why SQLite for Part I?

1. **Zero-config**: No server installation required
2. **File-based**: Single file, easy to backup and share
3. **Sufficient scale**: Prototype scale doesn't need enterprise DB
4. **Migration path**: Can migrate to PostgreSQL for Part II

### Why React for Dashboard?

1. **Component-driven**: Reusable UI components
2. **Ecosystem**: Huge library of charts and utilities
3. **Performance**: Virtual DOM, efficient re-rendering
4. **Server-side rendering**: Optional with Next.js (future)

### Why ONNX for Model Format?

1. **Cross-platform**: Supported on Linux, Windows, macOS
2. **Runtime availability**: ONNX Runtime for C++, Python, Rust
3. **Performance**: Optimized inference engines
4. **Quantization**: INT8 support built-in

---

## 🔄 Part I to Part II Migration Path

### Database Migration

```text
SQLite (Part I) → PostgreSQL (Part II)
────────────────────────────────────────
nodes table          → Partitioned by region/zone
telemetry table      → Time-series optimized (TimescaleDB)
indexes              → Additional performance indexes
schema               → Enhanced with capabilities/tags

Networking

TCP (Part I) → mTLS (Part II)
──────────────────────────────────────
TLS certificates   → CA-signed certificates
Mutual auth        → Both sides verify identities
Session management → JWT + TLS combination

Protocol

MessagePack (Part I) → Protobuf/mTLS (Part II)
─────────────────────────────────────────────
Schema evolution     → Defined schema with versioning
Acknowledgment      → Explicit ACK/NACK messages
Compression         → Built-in compression support

AI/ML

ONNX Runtime (Part I) → Enhanced model registry (Part II)
─────────────────────────────────────────────
Model versions       → Semantic versioning
Remote deployment    → HTTP/HTTPS model fetching
Lifecycle management → Version rollback, canary releases

Dashboard

React (Part I) → Advanced React (Part II)
──────────────────────────────────────
Real-time updates    → WebSocket + Server-Sent Events
Alerts               → Integrated alerting system
Analytics            → Advanced charts and metrics
User management      → RBAC and authentication
```

---

## 📋 Coding Conventions

### Rust

- **Format**: `cargo fmt` on every commit
- **Lint**: `cargo clippy` — fix all warnings
- **Naming**: snake_case for functions/variables, CamelCase for types
- **Comments**: Doc comments for all public APIs (`///`)
- **Error Handling**: Use `anyhow::Context` for error wrapping

### Python

- **Format**: `black` — automatic formatting
- **Lint**: `ruff` — fix all issues
- **Type Check**: `mypy` — target `strict=False` for Part I
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Comments**: Docstrings for all public functions (`"""...)`)

### TypeScript/React

- **Format**: `prettier` — automatic formatting
- **Lint**: `eslint` — fix all issues
- **Type Check**: `tsc` — strict mode where possible
- **Naming**: camelCase for functions/variables, PascalCase for components
- **Comments**: JSDoc for all public APIs (`/** ... */`)

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview and quickstart |
| `docs/architecture.md` | System design and component map |
| `docs/telemetry.md` | `/proc`/`/sys` collectors, data formats |
| `docs/communication.md` | Protocol, serialization, message types |
| `docs/inference.md` | ONNX Runtime integration, model loading |
| `docs/quantization.md` | INT8 quantization math and pipeline |
| `docs/database.md` | Schema, migrations, query patterns |
| `docs/testing.md` | Test strategy, running tests |
| `docs/benchmarking.md` | Methodology, results, reproduction |
| `docs/part2-roadmap.md` | Extension plan from Part I foundation |

---

## 🎯 Key Metrics

| Metric | Target | Current (Part I) |
|--------|--------|------------------|
| **Model Size** | < 10 MB FP32 | ~5 MB (example model) |
| **INT8 Reduction** | > 75% | ~75% (quantization) |
| **Inference Latency** | < 100 ms | ~50 ms (benchmark) |
| **Telemetry Interval** | 1-5 seconds | 2 seconds |
| **Heartbeat Timeout** | 30 seconds | 30 seconds |
| **Dashboard Updates** | < 5 seconds | 2 seconds |
| **Startup Time** | < 5 seconds | ~3 seconds (edge) |
| **Database Size** | < 10 MB | ~1 MB (prototype) |

---

## 🚧 Known Limitations

### Part I Limitations

1. **No TLS/SSL**: Plain TCP communication only
2. **SQLite only**: Not suitable for production scale
3. **Basic telemetry**: CPU, memory, temperature only
4. **Simple dashboard**: No alerts, limited visualization
5. **Static quantization**: No dynamic/advanced strategies
6. **Single-threaded**: No concurrent model inference
7. **No authentication**: Open connections

### Part II Planned Improvements

1. **mTLS**: Mutual TLS authentication
2. **PostgreSQL**: Production-scale database
3. **Advanced telemetry**: Disk, network, GPU metrics
4. **Enhanced dashboard**: Alerts, analytics, user management
5. **Dynamic quantization**: Calibration-based optimization
6. **Model registry**: Version management and remote deployment
7. **Resource scheduling**: CPU/memory-aware placement

---

## 📞 Support & Maintenance

### Bug Reports

1. Check `docs/testing.md` for known issues
2. Reproduce with latest `cargo build` / `uv sync`
3. Report with environment details (OS, Rust version, etc.)

### Upgrades

1. Follow `docs/part2-roadmap.md` for Part II migration
2. Update dependencies per `pyproject.toml` / `Cargo.toml`
3. Run `./scripts/dev_setup.sh` after changes

### Contributing

1. Follow coding conventions in `docs/architecture.md`
2. Add tests in respective test directories
3. Update documentation for new features
4. Submit pull requests following project guidelines

---

*Document generated: 2026-09-30*
*Part of AetherEdge final-year project — All rights reserved*