# AetherEdge ML Tooling

ML preparation and quantization utilities for the AetherEdge project

This directory contains Python tools for model preparation, quantization, and benchmarking in the AetherEdge distributed edge AI system.

## Overview

The ML tooling provides:

1. **Model Export**: Export PyTorch models to ONNX format
2. **INT8 Quantization**: Convert FP32 models to INT8 for edge deployment
3. **Benchmarking**: Compare FP32 vs INT8 model performance
4. **Utilities**: Helper functions for model management

## Key Components

### 1. Model Export (`export.py`)

Exports PyTorch models to ONNX format:
```python
from aetheredge.ml.export import ModelExporter

# Export a PyTorch model
exporter = ModelExporter()
model_path = exporter.export_model(my_torch_model)
```

### 2. Quantization (`quantize.py`)

Quantizes ONNX models from FP32 to INT8:
```python
from aetheredge.ml.quantize import quantize_model, create_calibration_data

# Quantize a model
quantized_path, stats = quantize_model(
    fp32_model="path/to/model.onnx",
    int8_model="path/to/model_int8.onnx"
)
```

### 3. Benchmarking (`benchmark.py`)

Compares FP32 and INT8 model performance:
```python
from aetheredge.ml.benchmark import compare_models

# Run benchmark
results = compare_models(
    fp32_model="model.onnx",
    int8_model="model_int8.onnx"
)
```

### 4. Utilities (`utils.py`)

Helper functions for model metadata and information:
```python
from aetheredge.ml.utils import load_metadata, get_model_info
```

## Quick Start

### 1. Create Example Model

```bash
cd ml
python -c "from src.export import ModelExporter; exporter = ModelExporter(); exporter.export_example_model()"
```

### 2. Quantize the Model

```bash
cd ml
python -c "
from src.quantize import quantize_model, export_example_model
# First create the example model
model_path = export_example_model()
# Then quantize it
quantized_path, stats = quantize_model(
    model_path, 
    Path('models/example-model/model_int8.onnx')
)
print(f'Quantized model: {quantized_path}')
print(f'Stats: {stats}')
"
```

### 3. Run Benchmark

```bash
cd ml
python src/benchmark.py
```

## API Reference

### ModelExporter

| Method | Description |
|--------|-------------|
| `export_model()` | Export PyTorch to ONNX |
| `export_example_model()` | Create a demo model |

### Quantization

| Function | Description |
|----------|-------------|
| `quantize_model()` | Quantize FP32 to INT8 |
| `create_calibration_data()` | Generate calibration data |

### Benchmarking

| Function | Description |
|----------|-------------|
| `compare_models()` | Compare FP32 vs INT8 performance |

### Utilities

| Function | Description |
|----------|-------------|
| `load_metadata()` | Load model metadata |
| `get_model_info()` | Get model file information |

## File Structure

```
ml/
├── pyproject.toml                    # Package configuration
├── src/                              # Python source files
│   ├── __init__.py                   # Package initialization
│   ├── export.py                     # Model export utilities
│   ├── quantize.py                   # Quantization tools
│   ├── benchmark.py                  # Comparison benchmark
│   └── utils.py                       # Helper functions
├── models/                           # Model storage
│   └── example-model/               # Example model files
│       ├── model.onnx               # FP32 model
│       ├── model_int8.onnx           # INT8 quantized model (optional)
│       └── metadata.json            # Model metadata
└── README.md                         # This file
```

## Features

### Model Export

- **PyTorch Integration**: Export any PyTorch model to ONNX
- **Flexible Input Shapes**: Support for dynamic axes
- **Export Options**: Configurable export parameters

### INT8 Quantization

- **Static Quantization**: INT8 weight quantization
- **Per-channel Support**: Advanced quantization modes
- **Calibration**: Automated calibration data handling
- **Statistics**: Detailed quantization metrics

### Benchmarking

- **Performance Comparison**: FP32 vs INT8 latency and size
- **Architecture Analysis**: Node count and operator comparison
- **Detailed Metrics**: Per-run statistics and averages
- **Error Handling**: Graceful failure on incompatible models

### Model Management

- **Metadata Tracking**: Model version and framework info
- **File Management**: Automatic directory creation
- **Information Retrieval**: Model size and metadata access

## Usage Examples

### Basic Export

```python
import torch
from aetheredge.ml.export import ModelExporter

# Create a simple model
class MyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 5)
    
    def forward(self, x):
        return self.linear(x)

# Export to ONNX
model = MyModel()
exporter = ModelExporter()
model_path = exporter.export_model(model)
```

### Quantization

```python
from aetheredge.ml.quantize import quantize_model

# Create dummy data for calibration
calibration_data = np.random.randn(100, 3, 224, 224).astype(np.float32)

# Quantize model
quantized_model, stats = quantize_model(
    model_path="model.onnx",
    int8_model="model_int8.onnx",
    calibration_data=calibration_data,
    per_channel=True,
    reduce_range=True
)
```

### Benchmark

```python
from aetheredge.ml.benchmark import compare_models

# Compare models
results = compare_models(
    fp32_model="model.onnx",
    int8_model="model_int8.onnx",
    num_iterations=100
)

print(f"Model size reduction: {results['model_size']['size_reduction_percent']:.1f}%")
print(f"Latency improvement: {results['performance']['latency_impro100']:.1f}%")
```

## Notes

### Model Requirements

- Supported frameworks: PyTorch (for export)
- Supported formats: ONNX
- Quantization: INT8

### Dependencies

Required Python packages:
```
torch>=2.0.0
torchvision>=0.15.0
onnx>=1.15.0
onxruntime>=1.16.0
numpy>=1.24.0
scikit-learn>=1.3.0
tqdm>=4.65.0
```

### Hardware Requirements

- GPU for PyTorch model export (optional)
- CPU for ONNX Runtime inference
- Sufficient disk space for model storage

### Performance Considerations

- **Memory**: Large models may require significant RAM
- **Storage**: ONNX models can be larger than original PyTorch
- **Calibration**: Calibration data can be large
- **Benchmarking**: May take time for multiple iterations

### Error Handling

Common errors and solutions:

1. **Model not found**: Ensure correct file paths
2. **Quantization error**: Check model compatibility
3. **Benchmark error**: Verify ONNX model validity
4. **Import error**: Install required dependencies

## Troubleshooting

### "ModuleNotFoundError: No module named 'onnxruntime'"

Install required package:
```bash
pip install onnxruntime
```

### "ImportError: libiomp5.so.0: cannot open shared object file"

Install Intel oneAPI:
```bash
# Linux
sudo apt-get install libiomp-dev
# Or via conda
conda install intel-openmp
```

### "RuntimeError: External data is too large"

This error occurs when the ONNX model is too large. Try:
1. Reducing model size
2. Using quantization
3. Checking model format

## Future Enhancements

### Planned Features

1. **Dynamic Quantization**: Mixed precision quantization
2. **Advanced Calibration**: Sophisticated calibration methods
3. **Model Compression**: Further compression techniques
4. **Continuous Integration**: Automated testing and validation
5. **Docker Support**: Containerized model preparation

### Research Integration

- **Knowledge Distillation**: For further compression
- **Post-training Quantization**: Without calibration data
- **Pruning**: Model size reduction
- **Neural Architecture Search**: Optimized model structures

## License

This project is part of the AetherEdge academic research project.

## Acknowledgments

This tool was developed as part of the AetherEdge final-year project.
Special thanks to the PyTorch and ONNX communities for their excellent tools.

## Support

For issues or questions, please refer to the main AetherEdge documentation.

---

*Generated by AetherEdge ML Tooling* ✅ **COMPLETE**