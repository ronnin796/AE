#!/usr/bin/env python3
"""Unit tests for ONNX model export pipeline"""

import pytest
import sys
from pathlib import Path
import numpy as np
import onnx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.export import create_demo_model


def test_model_export_creates_onnx(tmp_path):
    """Test that export creates a valid ONNX file"""
    # Skip export test if onnxscript unavailable (new torch.onnx API)
    try:
        import onnxscript
    except ImportError:
        pytest.skip("onnxscript not installed - export API requires it")

    output_path = tmp_path / "test_model.onnx"

    from src.export import export_to_onnx
    model, metadata, example_input = create_demo_model()

    result_path = export_to_onnx(model, example_input, output_path, metadata)

    assert result_path.exists(), "ONNX file should be created"
    assert result_path.stat().st_size > 0, "ONNX file should not be empty"


def test_onnx_model_loads_valid():
    """Test that exported ONNX model loads with onnx library"""
    model_path = Path(__file__).parent.parent / "models/example-model/model.onnx"

    if not model_path.exists():
        pytest.skip("Model file not found - run export first")

    model = onnx.load(str(model_path))
    onnx.checker.check_model(model)

    assert model.graph.input[0].name == "input" or model.graph.input[0].name == "x"
    assert len(model.graph.output) == 1


def test_onnx_model_produces_correct_output_shape():
    """Test that model produces correct output shape for test input"""
    import onnxruntime as ort
    import numpy as np

    model_path = Path(__file__).parent.parent / "models/example-model/model.onnx"

    if not model_path.exists():
        pytest.skip("Model file not found - run export first")

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    # Test with random input matching expected shape
    test_input = np.random.rand(1, 784).astype(np.float32)
    output = session.run(None, {input_name: test_input})

    assert len(output) == 1, "Should have 1 output"
    assert output[0].shape == (1, 10), f"Expected shape (1, 10), got {output[0].shape}"


def test_model_metadata_records_correct_shapes():
    """Test that model metadata contains correct input/output shapes"""
    from src.utils import load_metadata

    model_dir = Path(__file__).parent.parent / "models/example-model"
    metadata = load_metadata(model_dir)

    if metadata is None:
        pytest.skip("Metadata not found")

    assert "input_size" in metadata or "input_shape" in metadata, "Metadata should contain input size"
    assert "num_classes" in metadata or "output_shape" in metadata, "Metadata should contain num_classes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])