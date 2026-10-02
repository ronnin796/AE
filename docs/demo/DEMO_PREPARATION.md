# AetherEdge Part I — Demo Preparation Guide

**Purpose:** Complete checklist for a professional, defensible academic demonstration  
**Target:** Mid-Defense / Final Presentation  
**Duration:** 10 minutes (5-min emergency version available)

---

## 🎯 Demo Objectives

1. **Prove the system works end-to-end** — real data, no mocks
2. **Showcase technical depth** — `/proc`/`/sys` collection, TCP protocol, React architecture
3. **Demonstrate extensibility** — Part II roadmap from solid foundation
4. **Evidence-based claims** — test logs, benchmarks, reproducible commands

---

## 🖥️ Environment Setup (Do 30 min before demo)

### Required Software
```bash
# Verify versions
rustc --version       # 1.75+
python3 --version     # 3.11+
node --version        # 20+
npm --version         # 10+
```

### Start All Services (3 Terminals + Browser)

**Terminal 1 — FastAPI Server:**
```bash
cd /home/ronnin/Projects/AE_Edge/server
source .venv/bin/activate  # or uv sync
uvicorn app.main:app --host 0.0.0.0 --port 8080
```
✅ Should show: `Uvicorn running on http://0.0.0.0:8080`

**Terminal 2 — Edge Node A:**
```bash
cd /home/ronnin/Projects/AE_Edge/edge
cargo run -- --node-id demo-node-a --telemetry-interval 2 --server-addr 127.0.0.1:8080
```
✅ Should show: `Registered successfully`, `Telemetry sent`

**Terminal 3 — Edge Node B:**
```bash
cd /home/ronnin/Projects/AE_Edge/edge
cargo run -- --node-id demo-node-b --telemetry-interval 2 --server-addr 127.0.0.1:8080
```
✅ Should show: `Registered successfully`, `Telemetry sent`

**Browser — Dashboard:**
```bash
cd /home/ronnin/Projects/AE_Edge/dashboard
npm run dev
# OR serve production build:
npx serve dist -l 5173
```
✅ Open http://localhost:5173 — should show 2 nodes ONLINE

### Verify Checklist
- [ ] Server logs show both node registrations
- [ ] Dashboard shows 2 nodes, both green ONLINE
- [ ] Node cards display hostname, CPU, memory, OS
- [ ] Click node → Detail view opens with 4 tabs
- [ ] Telemetry tab shows charts (CPU, Memory, Temp, Load)
- [ ] Theme toggle works (top-right)
- [ ] Search/filter works in node list

---

## 🎬 Demo Script (10 Minutes)

### Minute 0:00–1:00 — Problem & Architecture
- **Slide:** Architecture diagram
- **Talking points:**
  - "Edge AI needs local inference + central monitoring"
  - "AetherEdge: Rust daemon (29MB) + FastAPI + React"
  - "Everything is real `/proc`/`/sys` data — no mocks"
  - Point to: TCP protocol, MessagePack, SQLite, REST API

### Minute 1:00–2:30 — System Startup (Live)
- **Action:** Show 3 terminals already running
- **Narrate:** "Server on 8080, two nodes reporting every 2s"
- **Show:** Server logs with registration messages
- **Key metric:** "29MB RAM, 0.13% CPU per node"

### Minute 2:30–4:00 — Dashboard Tour
- **Show:** http://localhost:5173
- **Walkthrough:**
  1. **Navbar:** Theme toggle, node counts, refresh
  2. **Sidebar:** Cluster overview (4 stat cards), telemetry summary
  3. **Main:** Node grid with search/filter/sort
  4. **Node Card:** Status bar, specs, telemetry preview, last seen
  5. **Click node** → Detail view

### Minute 4:00–6:00 — Live Telemetry + Charts
- **Click Node A** → Telemetry tab
- **Show charts:** CPU, Memory, Temperature, Load
- **Interact:** Hover for values, responsive resize
- **Explain:** "50 data points, 2s interval, Recharts"
- **Switch to Node B** → Compare

### Minute 6:00–8:00 — Workload Injection (The "Wow" Moment)
- **Command (new terminal):**
  ```bash
  stress-ng --cpu 4 --timeout 30
  # or: yes > /dev/null &
  ```
- **Watch:** CPU chart spikes 10% → 80%+ in real-time
- **Point out:** Sidebar telemetry updates, peak captured in stats
- **Narrate:** "Real `stress-ng` load, 2s telemetry interval, zero lag"

### Minute 8:00–9:00 — Node Failure & Recovery
- **Kill Node B:** `pkill -f "demo-node-b"`
- **Wait 15s** → Show OFFLINE badge (red), sidebar updates
- **Restart:** `cargo run -- --node-id demo-node-b --telemetry-interval 2 &`
- **Show:** Auto-recovery, same node ID, history preserved

### Minute 9:00–10:00 — Node Control + Evidence + Roadmap
- **Commands tab:** Show Shutdown, Reboot, Interval controls
- **Test Evidence slide:** 53 tests, 100% pass, benchmarks
- **Roadmap slide:** Part I → Part II table

---

## 🛡️ Defensibility Checklist

### Technical Claims → Evidence
| Claim | Evidence Location |
|-------|-------------------|
| "Real `/proc` data" | `edge/src/telemetry/cpu.rs`, `memory.rs`, `temperature.rs` |
| "MessagePack protocol" | `edge/src/protocol/mod.rs`, `messages.rs` |
| "29MB / 0.13% CPU" | `docs/testing/logs/benchmark.log` |
| "2s interval ±0%" | `docs/testing/logs/integration-test.log` |
| "60s zero loss" | `docs/testing/logs/system-test.log` |
| "100% test pass" | `docs/testing/final-test-summary.md` |
| "ONNX inference works" | `edge/src/inference/engine.rs`, `ml/` models |

### Code References for Committee
- **TCP Protocol:** `edge/src/protocol/mod.rs` (magic bytes `AETH`, sequence)
- **Telemetry Collection:** `edge/src/telemetry/*.rs` (delta calculation)
- **Database Schema:** `server/app/models/*.py` (SQLAlchemy)
- **Dashboard Architecture:** `dashboard/src/App.tsx` (React Query + Context)
- **Charts:** `dashboard/src/components/TelemetryCharts.tsx` (Recharts)

### Backup Plans
| Failure | Backup |
|---------|--------|
| Dashboard won't load | Pre-recorded GIFs in `docs/demo/assets/` |
| Node crashes | Second binary: `edge/target/release/aetheredge-edge` |
| Network issues | All localhost, no external deps |
| Charts broken | Static screenshots in presentation |
| Time cut short | 5-min version (see below) |

---

## ⚡ Emergency 5-Minute Version

| Time | Action |
|------|--------|
| 0:00–0:30 | Architecture + show running system |
| 0:30–2:00 | Dashboard + both nodes + charts |
| 2:00–3:30 | `stress-ng` spike + kill node + recovery |
| 3:30–4:30 | Commands tab + test summary |
| 4:30–5:00 | Part II roadmap + close |

---

## 📋 Pre-Demo Verification (Run 10 min Before)

```bash
# 1. Verify all tests pass
cd /home/ronnin/Projects/AE_Edge/edge && cargo test 2>&1 | tail -20
cd /home/ronnin/Projects/AE_Edge/server && uv run pytest 2>&1 | tail -20

# 2. Verify dashboard builds
cd /home/ronnin/Projects/AE_Edge/dashboard && npm run build 2>&1 | tail -10

# 3. Quick smoke test
curl -s http://localhost:8080/api/v1/nodes | jq '.total'
curl -s http://localhost:8080/api/v1/nodes/status/online | jq 'length'

# 4. Check logs exist
ls -la /home/ronnin/Projects/AE_Edge/docs/testing/logs/
```

---

## 🎤 Speaking Tips

1. **Pace:** ~130 words/min, pause after key demos
2. **Pointer:** Use mouse to highlight, don't just speak
3. **Narrate actions:** "I'm clicking Node A... now the Telemetry tab..."
4. **Connect to thesis:** "This validates our claim that..."
5. **Handle questions:** "Great question — the implementation is in [file], let me show you after"

---

## 📁 Key Files for Committee Access

```
GitHub Repo: [your-repo-url]
├── edge/src/              # Rust daemon (telemetry, protocol, inference)
├── server/app/            # FastAPI (models, API, services)
├── dashboard/src/         # React (components, hooks, charts)
├── ml/                    # Quantization, models
├── docs/
│   ├── architecture.md
│   ├── progress.md
│   ├── testing/
│   │   ├── final-test-summary.md
│   │   ├── logs/*.log
│   │   └── reproduction.md
│   └── demo/
│       ├── mid-defense-demo.md
│       └── DEMO_PREPARATION.md
└── README.md
```

---

## ✅ Final Sign-Off

- [ ] All 3 terminals running
- [ ] Dashboard loads with 2 nodes
- [ ] Charts render correctly
- [ ] `stress-ng` installed and tested
- [ ] Backup GIFs accessible
- [ ] Presentation slides ready
- [ ] GitHub repo link copied
- [ ] Water/coffee ready

---

**Prepared:** 2026-10-01  
**Status:** ✅ Ready for demonstration