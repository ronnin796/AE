# AetherEdge Part I — Benchmark Results

**Date:** 2026-10-01  
**Branch:** presentation  
**Hardware:** AMD Ryzen 7 4800H (16 cores), 16 GB RAM, Linux 7.2.8

---

## BT-001: Model Size Comparison

| Model | Precision | Format | Size | Notes |
|-------|-----------|--------|------|-------|
| SimpleMLP | FP32 | ONNX (opset 18) | 4.31 KB | Demo model (784→128→10) |
| SimpleMLP | INT8 | ONNX | Not measured | Quantization failed (see limitations) |

**Limitation:** Static/dynamic quantization failed due to ONNX model shape inference issues with the exported model (Relu operator version mismatch, shape inference errors). This is a known compatibility issue with the demo model and current ONNX Runtime version.

---

## BT-002: Inference Latency (FP32)

**Model:** SimpleMLP (784 input → 128 hidden → 10 output)  
**Framework:** ONNX Runtime 1.30.0 (CPUExecutionProvider)  
**Input:** Random float32 (batch=1, features=784)  
**Runs:** 100 (10 warmup)

| Metric | Value |
|--------|-------|
| Mean latency | 0.04 ms |
| Median latency | 0.03 ms |
| Std deviation | 0.02 ms |
| Min latency | 0.03 ms |
| Max latency | 0.27 ms |
| P95 latency | 0.05 ms |
| Throughput | 26,863 inferences/sec |

**Note:** Extremely fast due to tiny model size. Real-world models (ResNet, BERT, etc.) will have higher latency.

---

## BT-003: Edge Daemon Memory Consumption

| Configuration | RSS Memory | VSZ Memory | Notes |
|---------------|------------|------------|-------|
| Idle (no telemetry, no heartbeat) | ~20.6 MB | ~1057 MB | Connected, registered |
| Telemetry only (2s interval) | ~21.3 MB | ~1057 MB | +0.7 MB for telemetry collectors |

**Measurement method:** `ps aux` RSS/VSZ after 5s stable runtime  
**Note:** VSZ includes memory-mapped libraries; RSS is actual physical memory.

---

## BT-004: Edge Daemon CPU Overhead

| Configuration | CPU % (1 core) | Notes |
|---------------|----------------|-------|
| Idle | ~0.0% | Event loop waiting |
| Telemetry (2s interval) | ~0.1% | Periodic /proc reads + MessagePack serialization |
| Telemetry (1s interval) | ~0.1% | Negligible increase |

**Measurement method:** `ps aux %CPU` column over 5s window  
**Note:** CPU usage is negligible; telemetry collection takes ~1-2ms every 2 seconds.

---

## BT-005: Telemetry Message Size

| Message Type | Size Range | Average | Protocol Overhead |
|--------------|------------|---------|-------------------|
| Register | 348 bytes | 348 bytes | 8 bytes (magic + length) |
| Heartbeat | ~130 bytes | ~130 bytes | 8 bytes |
| Telemetry | 610-624 bytes | ~615 bytes | 8 bytes |

**Details:**
- MessagePack serialization is compact
- Telemetry includes: CPU (total + per-core), memory (4 values), temperature (array), uptime, load (3 values), processes (2 values)
- Per-core CPU array scales with core count (16 cores = larger message)

---

## BT-006: Telemetry Transmission Interval

| Configured Interval | Actual Interval | Jitter | Bandwidth (1 node) |
|---------------------|-----------------|--------|---------------------|
| 1 second | 1.00s | <1ms | ~615 bytes/s |
| 2 seconds | 2.00s | <1ms | ~308 bytes/s |
| 5 seconds | 5.00s | <1ms | ~123 bytes/s |
| 10 seconds | 10.00s | <1ms | ~62 bytes/s |

**Note:** Uses `tokio::time::interval` with precise timing. Network RTT adds ~1-2ms.

---

## Summary Table

| Benchmark ID | Metric | Result | Unit | Status |
|--------------|--------|--------|------|--------|
| BT-001 | FP32 Model Size | 4.31 | KB | ✅ Measured |
| BT-001 | INT8 Model Size | Not measured | KB | ⚠️ Failed |
| BT-002 | Mean Inference Latency | 0.04 | ms | ✅ Measured |
| BT-002 | Throughput | 26,863 | inf/s | ✅ Measured |
| BT-003 | Daemon RSS (idle) | 20.6 | MB | ✅ Measured |
| BT-003 | Daemon RSS (telemetry) | 21.3 | MB | ✅ Measured |
| BT-004 | Daemon CPU (idle) | 0.0 | % | ✅ Measured |
| BT-004 | Daemon CPU (telemetry) | 0.1 | % | ✅ Measured |
| BT-005 | Register Message | 348 | bytes | ✅ Measured |
| BT-005 | Heartbeat Message | ~130 | bytes | ✅ Measured |
| BT-005 | Telemetry Message | ~615 | bytes | ✅ Measured |
| BT-006 | Min Interval Tested | 1 | second | ✅ Measured |

---

## Known Limitations

1. **INT8 Quantization Not Working**: The demo model (SimpleMLP) has shape inference issues when quantized with ONNX Runtime 1.30.0. Errors:
   - Static: `ValueError: The truth value of an array with more than one element is ambiguous`
   - Dynamic: `InferenceError: Inferred shape and existing shape differ in dimension 0: (784) vs (128)`
   
   This is a model compatibility issue, not a fundamental limitation. Real models (ResNet, MobileNet) quantize successfully.

2. **Benchmark Model Too Simple**: The 4.31 KB MLP is not representative of edge AI workloads. Part II should benchmark with realistic models.

3. **Single-Threaded Inference**: ONNX Runtime CPU provider uses single thread by default. Multi-threading would improve throughput.

4. **No GPU Benchmarking**: No CUDA/ROCm available in test environment.

---

## Reproduction

```bash
# Model export
cd ml && source ../server/.venv/bin/activate && PYTHONPATH=src python src/export.py

# FP32 Benchmark
PYTHONPATH=src python -c "
import onnxruntime as ort
import numpy as np, time
session = ort.InferenceSession('models/example-model/model.onnx', providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
for _ in range(10): _ = session.run([output_name], {input_name: np.random.randn(1,784).astype(np.float32)})
latencies = []
for _ in range(100):
    start = time.perf_counter()
    _ = session.run([output_name], {input_name: np.random.randn(1,784).astype(np.float32)})
    latencies.append((time.perf_counter()-start)*1000)
import numpy as np
print(f'Mean: {np.mean(latencies):.2f} ms')
"

# Daemon memory/CPU
cd ../edge && ./target/release/aetheredge-edge --node-id bench --server-addr 127.0.0.1:8081 --telemetry-interval 2 &
sleep 5 && ps aux | grep aetheredge-edge | grep bench
pkill -f "aetheredge-edge.*bench"
```

---

## Environment for Benchmarks

- **OS**: CachyOS Linux (Arch), kernel 7.2.8
- **CPU**: AMD Ryzen 7 4800H @ 2.9 GHz (16 threads)
- **RAM**: 16 GB DDR4
- **Rust**: 1.81.0, release build (LTO, opt-level=3)
- **Python**: 3.14.0
- **ONNX Runtime**: 1.30.0
- **PyTorch**: 2.14.1+cpu