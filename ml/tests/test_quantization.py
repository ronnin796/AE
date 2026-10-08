#!/usr/bin/env python3
"""Unit tests for ONNX model quantization"""

import pytest
import sys
from pathlib import Path
import numpy as np
import onnx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.quantize import (
    prepare_quantized_model,
    compare_fp32_int8,
    quantize_model_static,
    quantize_model_dynamic,
    create_calibration_data
)


def test_quantization_creates_int8_model():
    """Test that quantization produces an INT8 model"""
    fp32_path, int8_path = prepare_quantized_model(
        Path("models/example-model"),
        use_static=True,
        num_calibration_samples=10
    )

    assert fp32_path.exists(), "FP32 model should exist"
    assert int8_path.exists(), "INT8 model should exist"

    # Verify INT8 model loads in onnxruntime
    import onnxruntime as ort
    int8_session = ort.InferenceSession(str(int8_path), providers=["CPUExecutionProvider"])

    # Check if model contains quantization nodes
    model = onnx.load(str(int8_path))

    # Look for QuantizeLinear or DequantizeLinear nodes (QDQ format)
    quant_nodes = [node for node in model.graph.node if node.op_type in ["QuantizeLinear", "DequantizeLinear"]]
    assert len(quant_nodes) > 0, "INT8 model should contain quantization nodes"


def test_int8_model_runs_inference():
    """Test that INT8 model actually runs inference"""
    fp32_path, int8_path = prepare_quantized_model(
        Path("models/example-model"),
        use_static=True,
        num_calibration_samples=10
    )

    import onnxruntime as ort
    import numpy as np

    int8_session = ort.InferenceSession(str(int8_path), providers=["CPUExecutionProvider"])
    input_name = int8_session.get_inputs()[0].name

    # Test input
    test_input = np.random.rand(1, 784).astype(np.float32)
    output = int8_session.run(None, {input_name: test_input})

    assert len(output) == 1, "Should have 1 output"
    assert output[0].shape == (1, 10), f"Expected shape (1, 10), got {output[0].shape}"
    assert not np.all(np.isnan(output[0])), "Output should not be NaN"


def test_fp32_int8_comparison():
    """Test FP32 vs INT8 comparison function"""
    fp32_path = Path(__file__).parent.parent / "models/example-model/model.onnx"
    int8_path = Path(__file__).parent.parent / "models/example-model/model_int8.onnx"

    if not int8_path.exists():
        pytest.skip("INT8 model not found - run quantization first")

    comparison = compare_fp32_int8(fp32_path, int8_path, test_data_count=5)

    assert "fp32_size_bytes" in comparison
    assert "int8_size_bytes" in comparison
    assert "accuracy_percent" in comparison
    assert comparison["fp32_size_bytes"] > 0
    assert comparison["int8_size_bytes"] > 0
    assert 0 <= comparison["accuracy_percent"] <= 100


def test_calibration_data_generation():
    """Test that calibration data is generated correctly"""
    data = create_calibration_data(num_samples=5, input_shape=(1, 784))

    assert len(data) == 5, "Should generate 5 samples"
    assert all(isinstance(d, np.ndarray) for d in data), "All samples should be numpy arrays"
    assert all(d.shape == (1, 784) for d in data), "All samples should have correct shape"
    assert all((d >= 0.0).all() and (d <= 1.0).all() for d in data), "All samples should be in [0,1]"


def test_metadata_saved_after_quantization():
    """Test that metadata is saved after quantization"""
    from src.utils import load_metadata

    fp32_path, int8_path = prepare_quantized_model(
        Path("models/example-model"),
        use_static=True,
        num_calibration_samples=10
    )

    metadata = load_metadata(int8_path.parent)

    assert metadata is not None, "Metadata should be saved"
    assert "quantization" in metadata, "Metadata should contain quantization info"
    assert "model_size_bytes" in metadata, "Metadata should contain model size"
    assert "original_model_size_bytes" in metadata, "Metadata should contain original model size"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])