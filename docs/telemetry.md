# AetherEdge Telemetry — Linux System Monitoring

## Overview

The AetherEdge edge node collects system telemetry directly from Linux kernel interfaces (`/proc` and `/sys`). This document explains how each collector works, the data it provides, and how it integrates with the distributed monitoring architecture.

---

## 🐧 Linux System Monitoring

### Why `/proc` and `/sys`?

Linux exposes system information through virtual filesystems:

1. **`/proc` (procfs)** — Virtual filesystem containing process and system information
   - Real-time statistics (CPU, memory, load)
   - Process information
   - Kernel version and system info
   - Always available in kernel builds

2. **`/sys` (sysfs)** — Virtual filesystem for kernel objects
   - Device and hardware information
   - Driver attributes
   - System buses and classes
   - Thermal zone information

**Why Direct Access?**

Rather than using high-level libraries (like `sysinfo`), AetherEdge reads directly from `/proc` and `/sys`:

1. **No Dependencies**: Zero additional libraries needed
2. **Kernel-Level Accuracy**: Data comes directly from the kernel
3. **Lightweight**: Minimal memory and CPU footprint
4. **Transparent**: You can verify readings manually with `cat`
5. **Educational**: Teaches Linux system internals

### File Structure:

```
/proc/
├── stat              # CPU statistics per processor
├── meminfo           # Memory usage information
├── uptime            # System uptime in seconds
├── loadavg           # Load averages
└── cpuinfo           # CPU model, speed, features

/sys/
└── class/
    └── thermal/
        ├── thermal_zone0/
        │   ├── temp
        │   └── type
        ├── thermal_zone1/
        │   ├── temp
        │   └── type
        └── ...          # One per thermal sensor
```

---

## 📊 Telemetry Data Collected

### 1. CPU Usage

#### Implementation: `telemetry/cpu.rs`

**Source**: `/proc/stat`

**How it works**:
1. Read `/proc/stat` twice (100ms apart)
2. Calculate CPU usage delta between samples
3. Return total usage and per-core breakdown

**Example `/proc/stat` format**:
```
cpu  3357 0 4313 1362393 13523 0 0 0 0 0
cpu0 1050 0 1316 455174 4493 0 0 0 0 0
cpu1 1149 0 1505 455196 4511 0 0 0 0 0
intr 115328 112866 8 0 0 0 0 0 0 0
ctxt 62166
btime 1696123456
processes 2345
procs_running 2
procs_blocked 0
```

**Calculation**:
```
CPU Usage = (DeltaIdle / DeltaTotal) * 100
Where:
  DeltaIdle = idle_now - idle_before
  DeltaTotal = total_now - total_before
```

**Fields Collected**:
- `cpu_usage`: Total CPU usage percentage (0-100% per core)
- `cpu_per_core`: Array of per-core usage percentages

**Error Handling**:
- Returns `0.0` usage if `/proc/stat` is unreadable
- Handles missing cores gracefully
- Uses saturating subtraction to avoid overflow

---

### 2. Memory Usage

#### Implementation: `telemetry/memory.rs`

**Source**: `/proc/meminfo`

**How it works**:
1. Read `/proc/meminfo`
2. Parse key-value pairs
3. Calculate memory usage percentage

**Example `/proc/meminfo` format**:
```
MemTotal:        8001380 kB
MemFree:         1234568 kB
MemAvailable:    3456780 kB
Buffers:          123456 kB
Cached:           234567 kB
...
```

**Fields Collected**:
- `memory_usage`: Used memory percentage (0-100%)
- `memory_total`: Total physical RAM (bytes)
- `memory_available`: Available memory including cache (bytes)
- `memory_used`: Used memory (bytes)

**Conversion**: Values in `/proc/meminfo` are in kB → multiply by 1024 for bytes

---

### 3. Temperature

#### Implementation: `telemetry/temperature.rs`

**Source**: `/sys/class/thermal/thermal_zone*/temp`

**How it works**:
1. Enumerate `/sys/class/thermal/thermal_zone*` directories
2. Read each zone's `temp` file (millidegrees Celsius)
3. Filter out invalid readings (< -50°C or > 150°C)

**Example thermal zone structure**:
```
/sys/class/thermal/thermal_zone0/
├── temp        # 45000 (45.0°C)
└── type        # x86_pkg_temp

/sys/class/thermal/thermal_zone1/
├── temp        # 42000 (42.0°C)
└── type        # coretemp
```

**Fields Collected**:
- `temperature`: First available sensor (°C)
- `temperatures`: Array of all thermal sensor readings

**Error Handling**:
- Returns empty vector if `/sys/class/thermal` doesn't exist
- Gracefully skips unreadable zone files
- Daemon continues without temperature data

---

### 4. System Information

#### Implementation: `telemetry/system.rs`

**Sources**:
- `/proc/uptime` — System uptime
- `/proc/loadavg` — Load averages

**How it works**:
1. Parse `/proc/uptime` for two values separated by space
2. Parse `/proc/loadavg` for 1/5/15-minute load averages

**Example `/proc/loadavg`**:
```
0.23 0.18 0.15 2/345 12345
```
- First three numbers: 1-min, 5-min, 15-min load averages
- Fourth: running process count / total process count
- Fifth: most recently created PID

**Fields Collected**:
- `uptime`: System uptime in seconds
- `load_1`: 1-minute load average
- `load_5`: 5-minute load average
- `load_15`: 15-minute load average
- `processes_running`: Number of running processes
- `processes_total`: Total number of processes

---

## 🏗️ Telemetry Collection Architecture

### Collector Pattern

```
TelemetryCollector (coordinator)
├── CpuCollector      → /proc/stat
├── MemoryCollector   → /proc/meminfo
├── TemperatureCollector → /sys/class/thermal
└── SystemCollector   → /proc/uptime, /proc/loadavg
```

Each collector implements the same interface:
```rust
impl Collector {
    pub fn new() -> Self;
    pub async fn collect(&self) -> Result<CollectedData>;
}
```

### Data Flow

```text
1. Edge Node starts
             ↓
     TelemetryCollector::new(config)
             ↓
        tokio::spawn(async {
            loop {
                interval.tick().await;
                
                collector.collect(&node_identity).await
                    .map_err(|e| error!("Failed to collect: {}", e));

                network_client.send_telemetry(&telemetry).await
                    .map_err(|e| error!("Failed to send: {}", e));
            }
        })
             ↓
       Server API: POST /api/v1/telemetry
             ↓
       SQLite: INSERT INTO telemetry ...
             ↓
       Dashboard: Poll /api/v1/telemetry?node_id=xxx
```

---

## 📈 Telemetry Data Structure

### Protocol Definition

```rust
#[derive(Serialize, Deserialize)]
pub struct Telemetry {
    pub node_id: String,
    pub timestamp: u64,
    pub cpu_usage: Option<f64>,
    pub cpu_per_core: Option<Vec<f64>>,
    pub memory_usage: Option<f64>,
    pub memory_total: Option<u64>,
    pub memory_available: Option<u64>,
    pub memory_used: Option<u64>,
    pub temperature: Option<f64>,
    pub temperatures: Option<Vec<f64>>,
    pub uptime: Option<u64>,
    pub load_1: Option<f64>,
    pub load_5: Option<f64>,
    pub load_15: Option<f64>,
    pub processes_running: Option<u32>,
    pub processes_total: Option<u32>,
}
```

### Database Schema (SQLite)

```sql
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL REFERENCES nodes(id),
    timestamp DATETIME NOT NULL,
    cpu_usage REAL,
    memory_usage REAL,
    temperature REAL,
    uptime INTEGER,
    load_1 REAL,
    load_5 REAL,
    load_15 REAL,
    processes_running INTEGER,
    processes_total INTEGER,
    ...
);
```

---

## 🧪 Testing Telemetry

### Manual Verification

You can verify the collectors manually using shell commands:

```bash
# CPU
cat /proc/stat | head -2

# Memory
cat /proc/meminfo | head -5

# Temperature
ls /sys/class/thermal/thermal_zone*/temp
cat /sys/class/thermal/thermal_zone*/temp

# Uptime
cat /proc/uptime

# Load average
cat /proc/loadavg
```

### Unit Tests

#### CPU Tests (`telemetry/cpu.rs`)

```rust
#[test]
fn test_cpu_times_total() {
    let times = CpuTimes {
        user: 100, nice: 10, system: 50, idle: 800,
        iowait: 20, irq: 5, softirq: 3, steal: 0, guest: 0, guest_nice: 0,
    };
    assert_eq!(times.total(), 988);
    assert_eq!(times.active(), 168);
}

#[test]
fn test_calculate_usage() {
    let prev = CpuTimes { user: 100, nice: 0, system: 50, idle: 800, ..Default::default() };
    let curr = CpuTimes { user: 150, nice: 0, system: 70, idle: 820, ..Default::default() };
    let usage = CpuCollector::calculate_usage(&prev, &curr);
    assert!(usage > 0.0 && usage < 100.0);
}
```

#### Memory Tests (`telemetry/memory.rs`)

```rust
#[test]
fn test_memory_collector_creation() {
    let collector = MemoryCollector::new();
    let _ = collector;
}
```

#### System Tests (`telemetry/system.rs`)

```rust
#[test]
fn test_system_collector_creation() {
    let collector = SystemCollector::new();
    let _ = collector;
}
```

### Integration Testing

```rust
// Run with: cargo test --no-fail-fast
#[tokio::test]
async fn test_full_telemetry_pipeline() {
    let collector = TelemetryCollector::new(TelemetryConfig::default());
    let identity = NodeIdentity::new_test("test-node");

    // Collect telemetry
    let telemetry = collector.collect(&identity).await.expect("Collection failed");

    // Verify fields
    assert_eq!(telemetry.node_id, "test-node");
    assert!(telemetry.timestamp > 0);
}
```

---

## ⚙️ Configuration

### Telemetry Configuration

```rust
#[derive(Serialize, Deserialize)]
pub struct TelemetryConfig {
    pub collect_cpu: bool,           // Default: true
    pub collect_memory: bool,        // Default: true
    pub collect_temperature: bool,   // Default: true (graceful fallback)
    pub collect_uptime: bool,        // Default: true
    pub collect_load: bool,          // Default: true
}
```

### CLI Options

```
--telemetry-interval <SECONDS>     # Override collection interval
--no-telemetry                     # Disable telemetry collection
--no-heartbeat                     # Disable heartbeat
```

### Environment Variables

```
AETHEREDGE_TELEMETRY_INTERVAL=2     # Collection interval (seconds)
AETHEREDGE_NO_TELEMETRY=false       # Disable telemetry
```

---

## 📊 Telemetry Pipeline Flow

```text
┌─────────────────────────────────────────────┐
│ Edge Node                                    │
│                                             │
│ ┌──────────────┐  ┌──────────────┐          │
│ │   CpuCollector │ → │ MemoryCollector │ →    │
│ └──────────────┘  └──────────────┘          │
│ ┌──────────────┐  ┌──────────────┐          │
│ │ TempCollector  │ → │ SystemCollector │ →    │
│ └──────────────┘  └──────────────┘          │
│           ↓                                   │
│   TelemetryCollector (merge)                │
│           ↓                                   │
│   MessagePack Serialization                 │
│           ↓                                   │
│   TCP → FastAPI Server                        │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Server                                      │
│           ↓                                 │
│   POST /api/v1/telemetry                    │
│           ↓                                 │
│   SQLAlchemy INSERT                         │
│           ↓                                 │
│   SQLite Database                           │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Dashboard                                   │
│           ↓                                 │
│   Poll GET /api/v1/telemetry/node/{id}      │
│           ↓                                 │
│   Recharts Charts                           │
│           ↓                                 │
│   Real-time Updates                         │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Extending Telemetry (Part II)

### Adding New Collectors

Part II will extend telemetry with additional collectors:

1. **Network Statistics** — `/proc/net/dev`
   ```rust
   // Planned for Part II
   mod network_stats;
   ```

2. **Disk Usage** — `/` filesystem stats
   ```rust
   // Planned for Part II
   mod disk;
   ```

3. **GPU Metrics** — NVIDIA SMI integration
   ```rust
   // Planned for Part II
   mod gpu;
   ```

4. **Process Metrics** — `/proc/[pid]/status`
   ```rust
   // Planned for Part II
   mod process;
   ```

### Architecture for Extensibility

```rust
/// Trait for all telemetry collectors
#[async_trait::async_trait]
pub trait TelemetryCollector: Send + Sync {
    async fn collect(&self) -> Result<TelemetryData>;
    fn name(&self) -> &'static str;
    fn is_available(&self) -> bool;
}

/// Registry of available collectors
pub struct CollectorRegistry {
    collectors: Vec<Box<dyn TelemetryCollector>>,
}
```

This allows Part II to add new collectors without modifying the core pipeline.

---

## 📚 References

### Linux Documentation

- `/proc` filesystem: `man 5 proc`
- `/sys` filesystem: `man 5 sysfs`

### Key Files

| File | Purpose |
|------|---------|
| `edge/src/telemetry/mod.rs` | Main collector and Telemetry struct |
| `edge/src/telemetry/cpu.rs` | CPU usage from `/proc/stat` |
| `edge/src/telemetry/memory.rs` | Memory metrics from `/proc/meminfo` |
| `edge/src/telemetry/temperature.rs` | Thermal zones from `/sys/class/thermal` |
| `edge/src/telemetry/system.rs` | Uptime/load averages from `/proc` |

---

## 🚧 Known Limitations

### Part I

1. **No custom metrics**: Only standard system metrics
2. **Fixed collection interval**: 2-second default
3. **Synchronous collection**: Collectors don't overlap
4. **No historical analysis**: Only current snapshot
5. **Limited process metrics**: Count only

### Part II Planned

1. **Custom metric plugins**: User-defined collectors
2. **Dynamic sampling**: Adaptive collection intervals
3. **Parallel collection**: Concurrent sensor reads
4. **Historical analysis**: Statistical summaries
5. **Process-level monitoring**: Resource usage per process

---

*Document generated: 2026-09-30*
*Part of AetherEdge final-year project — All rights reserved*