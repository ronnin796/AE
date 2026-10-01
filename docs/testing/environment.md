# AetherEdge Part I — Testing Environment

**Date:** 2026-10-01
**Branch:** mid-defense-hardening

---

## System Information

| Component | Version |
|-----------|---------|
| OS | CachyOS Linux (rolling) |
| Kernel | 7.2.8-1-cachyos |
| Architecture | x86_64 |
| CPU | AMD Ryzen 7 4800H with Radeon Graphics (16 cores) |
| Memory | 16.6 GB |

---

## Software Versions

| Tool | Version |
|------|---------|
| Rust | 1.80+ (via rustup) |
| Cargo | 1.80+ |
| Python | 3.14.7 |
| uv | 0.4+ |
| Node.js | 20+ |
| npm | 10+ |
| SQLite | 3.45+ |

---

## Project Dependencies

### Rust (edge/Cargo.toml)
| Crate | Version |
|-------|---------|
| tokio | 1.38 (full) |
| config | 0.14 |
| serde | 1.0 (derive) |
| serde_repr | 0.1 |
| toml | 0.8 |
| tracing | 0.1 |
| tracing-subscriber | 0.3 (env-filter, fmt, json) |
| anyhow | 1.0 |
| rmp-serde | 1.1 |
| sysinfo | 0.30 |
| ort | 2.0.0-rc.13 (load-dynamic) |
| clap | 4.5 (derive, env) |
| uuid | 1.7 (v4, serde, fast-rng) |
| bytes | 1.5 |

### Python Server (server/pyproject.toml)
| Package | Version |
|---------|---------|
| fastapi | >=0.104.0 |
| uvicorn[standard] | >=0.24.0 |
| sqlalchemy | >=2.0.0 |
| pydantic | >=2.5.0 |
| pydantic-settings | >=2.1.0 |
| python-multipart | >=0.0.6 |
| alembic | >=1.13.0 |
| aiosqlite | >=0.22.1 |
| msgpack | >=1.2.3 |
| pytest | >=7.4.0 (dev) |
| pytest-asyncio | >=0.23.0 (dev) |
| httpx | >=0.25.0 (dev) |

### Python ML (ml/pyproject.toml)
| Package | Version |
|---------|---------|
| torch | >=2.0.0 |
| torchvision | >=0.15.0 |
| onnx | >=1.15.0 |
| onnxruntime | >=1.16.0 |
| onnxruntime-tools | >=1.16.0 |
| numpy | >=1.24.0 |
| scikit-learn | >=1.3.0 |
| tqdm | >=4.65.0 |

### Dashboard (dashboard/package.json)
| Package | Version |
|---------|---------|
| react | 18.2+ |
| react-dom | 18.2+ |
| @tanstack/react-query | 5.0+ |
| axios | 1.6+ |
| recharts | 2.10+ |
| vite | 5.0+ |
| typescript | 5.0+ |

---

## Database

| Property | Value |
|----------|-------|
| Type | SQLite |
| File | aetheredge.db (in server/) |
| Tables | nodes, telemetry |
| ORM | SQLAlchemy 2.0 (async) |

---

## Network

| Service | Port | Protocol |
|---------|------|----------|
| FastAPI HTTP API | 8080 | HTTP/1.1 |
| TCP Binary Protocol | 8081 | Custom (AETH magic + MessagePack) |

---

## Test Hardware Notes

- All tests run on single machine (localhost)
- Edge nodes run as separate processes on same host
- Multi-node simulation via different --node-id values
- No VMs or physical separate nodes used in Part I testing
