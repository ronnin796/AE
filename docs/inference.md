# AetherEdge Inference — Edge AI Documentation

## Overview

This document describes the inference pipeline for running AI models locally on edge nodes, including ONNX Runtime integration and model management.

---

## 🤖 Why Edge Inference?

### Benefits
1. **Privacy**: Data stays on-device
2. **Latency**: No network round-trips for inference
3. **Bandwidth**: Reduces data transfer costs
4. **Reliability**: Works offline
5. **Scalability**: Distributes compute load

### Trade-offs
1. **Limited compute**: Constrained resources
2. **Model size**: Must be lightweight
3. **Power consumption**: Battery-constrained devices
4. **Heat generation**: Thermal constraints

---

## 📦 Model Format

### ONNX (Open Neural Network Exchange)

**Choice**: ONNX format for model portability

**Why ONNX?**
1. **Cross-platform**: Works on Linux, Windows, macOS
2. **Language support**: Python, Rust, C++, JavaScript
3. **Runtime options**: ONNX Runtime, TensorRT, OpenVINO
4. **Quantization**: Native INT8 support
5. **Vendor support**: Microsoft, NVIDIA, Intel backing

**Alternative Considered**: TensorFlow Lite
- Pros: Mobile-first, smaller footprint
- Cons: Limited language bindings, less standardized

### Model Pipeline

```text
PyTorch/TensorFlow
      ↓ Export
ONNX Format (.onnx)
      ↓ Load
ONNX Runtime
      ↓ Run
Edge Inference
```

---

## 🏗️ Implementation

### Rust Inference Engine

```rust
use ort::{Environment, Session};

pub struct InferenceEngine {
    session: Option<ort::Session>,
    input_name: String,
    output_names: Vec<String>,
}

impl InferenceEngine {
    pub fn new(model_path: &Path) -> Result<Self> {
        let environment = Environment::new()?;
        let session = environment
            .new_session_builder()?
            .with_model_from_file(model_path)?;
        
        Ok(Self {
            session: Some(session),
            input_name: "input".to_string(),
            output_names: vec!["output".to_string()],
        })
    }

    pub fn infer(&mut self, input: &[f32], shape: &[usize]) -> Result<Vec<f32>> {
        let input_tensor = ort::Tensor::from_array((shape.to_vec(), input.to_vec()))?;
        let outputs = self.session.run(ort::inputs![
            self.input_name.as_str() => input_tensor
        ])?;
        
        let output = outputs.get("output")?
            .try_extract_array::<f32>()?;
        Ok(output.to_vec())
    }
}
```

### Model Metadata

Each model includes metadata:

```json
{
    "model_name": "example-model",
    "framework": "pytorch",
    "format": "onnx",
    "version": "1.0",
    "input_shape": [1, 3, 224, 224],
    "output_shape": [1, 10],
    "description": "Simple CNN model for demonstration"
}
```

---

## 📁 Model Management

### Part I Structure

```
models/
└── example-model/
    ├── model.onnx          # FP32 model
    └── metadata.json       # Model metadata
```

**Note**: Full model registry is planned for Part II.

### Model Loading Process

```text
1. Edge Node starts
2. Check for local model: models/example-model/model.onnx
3. Load ONNX model via InferenceEngine::new()
4. Verify input/output dimensions
5. Ready for inference requests
```

---

## 🧪 Testing Inference

### Integration Test

```rust
#[tokio::test]
async fn test_inference_engine() {
    let model_path = Path::new("models/example-model/model.onnx");
    if !model_path.exists() {
        return; // Skip if no model
    }
    
    let engine = InferenceEngine::new(model_path).expect("Failed to load model");
    let input = vec![1.0f32; 224*224*3]; // Dummy input
    let shape = vec![1, 3, 224, 224];
    
    let output = engine.infer(&input, &shape).expect("Inference failed");
    assert!(!output.is_empty());
}
```

### Python Export Script

```python
import torch
from aetheredge.ml.export import ModelExporter

exporter = ModelExporter()
model_path = exporter.export_example_model()
print(f"Model exported to: {model_path}")
```

---

## 📊 Benchmarking

### Comparison Metrics

| Metric | FP32 | INT8 | Target |
|--------|------|------|--------|
| Model Size | - | < 75% of FP32 | ✅ |
| Inference Latency | - | < 90% of FP32 | ✅ |
| Accuracy | - | No significant drop | ✅ |

### Measurement Script

```python
from aetheredge.ml.benchmark import compare_models

results = compare_models(
    fp32_model="models/model.onnx",
    int8_model="models/model_int8.onnx",
    num_iterations=100
)

print(f"Size reduction: {results['model_size']['size_reduction_percent']:.1f}%")
print(f"Latency improvement: {results['performance']['latency_improvement_percent']:.1f}%")
```

---

## 🔄 Part II Extensions

### Planned Features

1. **Model Registry**: Version management and remote fetching
2. **Dynamic Loading**: Load/unload models at runtime
3. **Batch Inference**: Process multiple inputs together
4. **Hardware Acceleration**: GPU, NPU support
5. **Adaptive Scheduling**: Based on resource usage

---

## 📚 References

- ONNX: https://onnx.ai/
- ONNX Runtime: https://onnxruntime.ai/
- Rust ort crate: https://crates.io/crates/ort

---

*Document generated: 2026-09-30*