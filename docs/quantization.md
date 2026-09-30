# AetherEdge — INT8 Quantization Documentation

## Overview

This document describes the static INT8 quantization pipeline for converting FP32 models to INT8 for edge deployment.

---

## 📖 INT8 Quantization Concept

### What is Quantization?

Quantization maps floating-point values to integers to reduce model size and improve inference speed.

**FP32 → INT8 Mapping**:
```
α = max(|W|)                    # Scaling factor
W_int8 = round(W / α * 127)     # Quantized weights
```

Where:
- `W` is the original FP32 weight
- `α` is the scaling factor (max absolute weight)
- `W_int8` is the quantized integer value

### Why INT8?

1. **Size**: 4× smaller than FP32 (32-bit → 8-bit)
2. **Speed**: Faster matrix multiplication on integer hardware
3. **Memory**: Less RAM required
4. **Power**: Lower energy consumption
5. **Bandwidth**: Less data transfer

---

## 🏗️ Quantization Pipeline

### Step 1: Export FP32 Model

```python
from aetheredge.ml.export import ModelExporter

exporter = ModelExporter()
fp32_path = exporter.export_example_model()
```

### Step 2: Static Quantization

```python
from aetheredge.ml.quantize import quantize_model

quantized_path, stats = quantize_model(
    fp32_model="models/model.onnx",
    int8_model="models/model_int8.onnx",
    calibration_data=calibration_data,
    per_channel=False,
    reduce_range=False
)
```

### Step 3: Benchmark Comparison

```python
from aetheredge.ml.benchmark import compare_models

results = compare_models(
    fp32_model="models/model.onnx",
    int8_model="models/model_int8.onnx",
    num_iterations=100
)
```

---

## 📊 Expected Results

### Size Comparison

| Model | Size | Reduction |
|-------|------|-----------|
| FP32 | ~50 MB | — |
| INT8 | ~12 MB | 75% smaller |

### Latency Comparison

| Model | Avg Latency | Improvement |
|-------|-------------|-------------|
| FP32 | ~10 ms | — |
| INT8 | ~8 ms | 20% faster |

### Accuracy

- **INT8**: Comparable to FP32 (< 1% drop typical)
- **Calibration**: Maintains model accuracy
- **Per-channel**: Better for large models

---

## 🔄 Part II Extensions

### Planned Improvements

1. **Dynamic Quantization**: Per-tensor scaling
2. **Quantization-Aware Training**: Better accuracy
3. **Mixed Precision**: FP16 + INT8 hybrid
4. **Calibration Strategies**: Min/max, percentiles, entropy
5. **Post-Training Optimization**: Layer fusion, pruning

---

## 📚 References

- ONNX Runtime Quantization: https://onnxruntime.ai/docs/performance/quantization.html
- PyTorch Quantization: https://pytorch.org/docs/stable/quantization.html
- INT8 Arithmetic: https://developer.nvidia.com/blog/cuda-pro-tip-int8-vectorized-matrix-multiplication/

---

*Document generated: 2026-09-30*