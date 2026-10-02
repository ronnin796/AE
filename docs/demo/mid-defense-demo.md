# AetherEdge Part I — Mid-Defense Demonstration Script

**Duration:** 5–10 minutes  
**Audience:** Academic Defense Committee  
**Date:** 2026-10-01  
**Branch:** mid-defense-hardening  

---

## Demonstration Overview

| Phase | Duration | Focus |
|-------|----------|-------|
| 1. Problem & Architecture | 1 min | Context & system design |
| 2. System Startup | 1.5 min | Server + 2 edge nodes |
| 3. Dashboard Overview | 1.5 min | **Enhanced** node monitoring UI with sidebar |
| 4. Live Telemetry | 2 min | Real CPU/Memory/Temperature **charts** |
| 5. Workload Injection | 2 min | CPU spike observation **in real-time charts** |
| 6. Node Failure | 1 min | Disconnection detection |
| 7. Node Recovery | 1 min | Reconnection |
| 8. Node Control | 1 min | **NEW** Remote commands (shutdown, reboot, intervals) |
| 9. Test Evidence | 30 sec | Test campaign summary |
| 10. Part I → Part II | 30 sec | Roadmap |

**Total: ~10 minutes**

---

## Detailed Script

---

### 1. Problem & Architecture (1 minute)

> **Speaker:** "Edge computing requires local AI inference with centralized monitoring. AetherEdge solves this with a lightweight Rust daemon on each edge node collecting real system telemetry and running ONNX inference, while a central FastAPI server provides monitoring and management."

**Show:** Architecture diagram (FIG-01)
- **Edge Nodes:** Rust daemon → Linux `/proc`/`/sys` → TCP binary protocol
- **Server:** FastAPI + SQLite + HTTP API
- **Dashboard:** React + TanStack Query + Recharts + **Theme support**
- **Key Point:** "Everything you'll see uses real `/proc` data — no mocks."

---

### 2. System Startup (1.5 minutes)

> **Speaker:** "Let me start the system: one central server, two edge nodes."

**Commands:**
```bash
# Terminal 1: Server
cd server && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080

# Terminal 2: Node A
cd edge && cargo run -- --node-id demo-node-a --telemetry-interval 2

# Terminal 3: Node B  
cd edge && cargo run -- --node-id demo-node-b --telemetry-interval 2
```

**Narrate while starting:**
- "Server initializes SQLite database and starts TCP listener on port 8081"
- "Each edge daemon reads `/proc/stat`, `/proc/meminfo`, `/sys/class/thermal`"
- "Registration via custom TCP protocol (MessagePack + custom framing)"
- "Heartbeat every 10s, telemetry every 2s"

**Evidence:** Show TERM-06 (server logs), DEMO-10 (edge registration logs)

---

### 3. Dashboard Overview (1.5 minutes)

> **Speaker:** "The React dashboard polls the HTTP API every 5 seconds. The new layout features a persistent sidebar with cluster overview and a main content area."

**Open:** http://localhost:5173 (or served dist/)

**Show DEMO-01:** Dashboard with both nodes
- **Sidebar:** Cluster overview with stat cards (Total, Online, Offline, Degraded)
- **Sidebar:** Real-time telemetry summary for selected node
- **Main Area:** Node grid with enhanced cards showing hostname, OS, CPU, memory, version, last seen
- **Status Indicators:** Color-coded badges with animated status dots
- **Search & Filter:** Search by name/ID/OS, filter by status, sort options
- **Theme Toggle:** Dark/Light mode in navbar (persisted to localStorage)

**Key Point:** "All data comes from HTTP API → SQLite → TCP protocol → actual Linux `/proc`"

**Evidence:** DEMO-01, DEMO-04 screenshots

---

### 4. Live Telemetry (2 minutes)

> **Speaker:** "Let's look at real-time telemetry with interactive charts."

**Actions:**
1. Click Node A → Shows **Overview tab** with system info + telemetry summary
2. Click **Telemetry tab** → Shows **interactive Recharts** (CPU, Memory, Temp, Load)
3. Click **System tab** → Detailed system information
4. Click **Commands tab** → Available remote commands
5. Click Node B → Compare

**Narrate:**
- "CPU chart updates every 2 seconds with actual `/proc/stat` delta"
- "Memory from `/proc/meminfo` — total, available, used, percentage"
- "Temperature from `/sys/class/thermal` — real Celsius readings"
- "Load average from `/proc/loadavg`"
- "Charts are interactive — hover for exact values, responsive layout"

**Point at charts:** "Notice the natural variation — this is real system activity, not synthetic data."

**Evidence:** DEMO-02, DEMO-03 screenshots

---

### 5. Workload Injection (2 minutes)

> **Speaker:** "Now let's generate real CPU load on Node A and watch the dashboard respond in real-time."

**Command:**
```bash
# In a new terminal
stress-ng --cpu 4 --timeout 30
# Or simpler: yes > /dev/null &
```

**Observe DEMO-05 (GIF):**
- Node A CPU chart spikes from ~10% to ~80%+
- Memory may increase slightly
- Charts update in real-time (2s interval)
- Sidebar telemetry summary updates automatically

**Narrate:**
- "This is real CPU consumption from `stress-ng`"
- "Telemetry interval is 2 seconds — you see the spike within 2 seconds"
- "No polling delay, no synthetic interpolation"
- "Peak values captured in stats"

**Evidence:** DEMO-05 (GIF of CPU spike)

---

### 6. Node Failure Detection (1 minute)

> **Speaker:** "Now let's simulate a node failure by stopping Node B."

**Command:**
```bash
pkill -f "demo-node-b"
```

**Wait 15 seconds...** (heartbeat timeout + maintenance check)

**Observe DEMO-06:**
- Node B status changes from "ONLINE" to "OFFLINE" (red badge)
- Sidebar overview cards update: "Online: 1, Offline: 1"
- Node card shows red status bar and OFFLINE badge
- Last seen timestamp freezes
- Connection quality indicator shows offline

**Narrate:**
- "Server detects missing heartbeat after configurable timeout (default 30s)"
- "Maintenance endpoint allows manual offline marking with custom timeout"
- "No false positives — only marks offline after confirmed silence"

**Evidence:** DEMO-06 screenshot

---

### 7. Node Recovery (1 minute)

> **Speaker:** "Now let's bring Node B back online."

**Command:**
```bash
cd edge && cargo run -- --node-id demo-node-b --telemetry-interval 2 &
```

**Observe DEMO-07 (GIF):**
- Node B reappears in node list
- Status changes to "ONLINE" (green badge)
- Telemetry resumes immediately
- Charts continue from where they left off
- Same node ID preserves identity and history

**Narrate:**
- "No manual intervention needed — daemon re-registers automatically"
- "Same node ID preserves identity and history"
- "Designed for unreliable edge networks"

**Evidence:** DEMO-07 (GIF)

---

### 8. Node Control (1 minute) — **NEW**

> **Speaker:** "The dashboard now supports sending commands to edge nodes via the TCP control channel."

**Actions:**
1. Select Node A → Click **Commands tab**
2. Click "Telemetry: 5s" → Observe interval change confirmation
3. Click "Heartbeat: 10s" → Observe confirmation
4. (Optional) Click "Reboot Node" → Confirm → Node restarts
5. (Optional) Click "Shutdown Node" → Confirm → Node stops gracefully

**Observe:**
- Toast notifications for command success/failure
- Commands disabled when node is offline
- Confirmation dialogs for destructive actions

**Narrate:**
- "Commands sent via TCP control channel, not HTTP"
- "Background task queue on server ensures delivery"
- "Node applies config changes without restart (for intervals)"
- "Full audit trail in server logs"

**Evidence:** DEMO-08 (screenshots of command execution)

---

### 9. Test Evidence Summary (30 seconds)

> **Speaker:** "Let me briefly summarize the test campaign that validates all this."

**Show Slide/Table:**

| Category | Tests | Pass Rate |
|----------|-------|-----------|
| Rust Unit Tests | 17 | 100% |
| Python Unit Tests | 27 | 100% |
| Integration Tests | 9 | 100% |
| System Test (60s) | 1 | 100% |
| Benchmarks | 4/6 | 67% (2 pending) |

**Key Metrics:**
- Edge daemon: 29 MB RAM, 0.13% CPU
- Telemetry: 573 bytes, 2.00s interval ±0%
- 60s sustained: 33 samples/node, zero loss
- Dashboard: < 200ms initial load, 60fps charts

**Evidence:** All logs in `docs/testing/logs/`

---

### 10. Part I → Part II Roadmap (30 seconds)

> **Speaker:** "Part I establishes the foundation. Part II adds production capabilities."

**Show Roadmap Slide:**

| Part I (Done) | Part II (Planned) |
|---------------|-------------------|
| ✅ TCP binary protocol | 🔒 TLS 1.3 + mTLS |
| ✅ Real telemetry pipeline | 📦 Remote model deployment |
| ✅ SQLite persistence | 🗄️ PostgreSQL + connection pooling |
| ✅ React dashboard | 🔐 JWT authentication |
| ✅ ONNX inference engine | 📦 Model registry + versioning |
| ✅ 29 MB / 0.13% CPU | 📊 Advanced scheduling |
| ✅ 2s interval precision | ⚡ Sub-second intervals |
| ✅ **Interactive charts (Recharts)** | 📈 Advanced analytics |
| ✅ **Dark/Light theme** | 🎨 Custom theming |
| ✅ **Remote node commands** | 🎮 Fleet management |

**Closing:** "AetherEdge Part I is a working, tested foundation. All code is open, all tests reproducible. Ready for Part II."

---

## Backup Slides (If Questions)

### Technical Deep Dives Available:
1. **TCP Protocol** — MessagePack framing, `AETH` magic bytes, sequence numbers
2. **Telemetry Collection** — `/proc/stat` delta calculation, thermal zones
3. **Database Schema** — Nodes + Telemetry tables, indexes, relationships
4. **Benchmark Methodology** — psutil sampling, JSON size measurement
5. **Test Reproducibility** — All commands in `docs/testing/reproduction.md`
6. **Dashboard Architecture** — React Query caching, component composition, CSS variables theming

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Server fails to start | Pre-recorded GIFs of all dashboard states |
| Edge node crashes | Second edge binary pre-built |
| Network issues | All local (localhost), no external deps |
| Demo too long | Skip to key moments, have 5-min version ready |
| Committee asks for code | GitHub repo ready, specific files bookmarked |
| Charts don't render | Static chart screenshots as backup |

---

## Timing Summary

| Segment | Target | Max |
|---------|--------|-----|
| 1. Problem/Architecture | 1:00 | 1:30 |
| 2. System Startup | 1:30 | 2:00 |
| 3. Dashboard Overview | 1:30 | 2:00 |
| 4. Live Telemetry | 2:00 | 2:30 |
| 5. Workload Injection | 2:00 | 2:30 |
| 6. Node Failure | 1:00 | 1:30 |
| 7. Node Recovery | 1:00 | 1:30 |
| 8. Node Control | 1:00 | 1:30 |
| 9. Test Evidence | 0:30 | 1:00 |
| 10. Part II Roadmap | 0:30 | 1:00 |
| **Total** | **10:00** | **13:00** |

---

## Emergency 5-Minute Version

If time-critical:
1. **30s** — Architecture + startup (show already running)
2. **1:30** — Dashboard + live telemetry (both nodes, charts)
3. **1:30** — Workload spike + node failure + recovery
4. **1:00** — Node control demo + test summary
5. **0:30** — Part II roadmap

---

## Demo Environment Checklist

- [ ] Server running on port 8080
- [ ] Two edge nodes: `demo-node-a`, `demo-node-b`
- [ ] Dashboard at http://localhost:5173
- [ ] `stress-ng` installed for workload injection
- [ ] Browser: Chrome/Firefox (tested)
- [ ] Screen resolution: 1920x1080 minimum
- [ ] Backup: Pre-recorded GIFs in `docs/demo/assets/`
- [ ] Theme: Test both dark/light modes

---

*Prepared: 2026-10-01*  
*All demonstration content from actual system execution — no staged or fake data*