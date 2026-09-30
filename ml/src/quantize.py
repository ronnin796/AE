"""Model quantization utilities"""
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantization
from pathlib import Path
import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def quantize_model(
    model_fp32: Path,
    model_int8: Path,
    calibration_data: Optional[np.ndarray] = None,
    per_channel: bool = False,
    reduce_range: bool = False,
    weight_type: quantization.QuantType = quantization.QuantType.QInt8,
) -> Tuple[Path, dict]:
    """
    Quantize a FP32 ONNX model to INT8

    Args:
        model_fp32: Path to FP32 ONNX model
        model_int8: Path for output INT8 model
        calibration_data: Data for calibration (if None, uses min/max)
        per_channel: Whether to use per-channel quantization
        reduce_range: Whether to reduce quantization range
        weight_type: Quantization type for weights

    Returns:
        Tuple of (Path to quantized model, quantization stats)
    """
    # Ensure output directory exists
    model_int8.parent.mkdir(parents=True, exist_ok=True)

    # Create calibration data reader if needed
    if calibration_data is not None:
        # In a real implementation, we'd use a proper calibration data reader
        # For demo, we'll just use min/max calibration
        pass

    # Quantize the model
    quant_stats = quantization.quantize_static(
        model_input=str(model_fp32),
        model_output=str(model_int8),
        calibration_data_reader=None,  # For demo - in reality would use actual data
        quant_format=quantization.QuantFormat.QOperator,
        per_channel=per_channel,
        reduce_range=reduce_range,
        weight_type=weight_type,
        activation_type=quantization.QuantType.QUInt8,
        nodes_to_exclude=[],  # Exclude problematic nodes if needed
        nodes_to_include=[],  # Include specific nodes if needed
    )

    logger.info(f"Quantized model saved to: {model_int8}")
    logger.info(f"Quantization stats: {quant_stats}")

    return model_int8, quant_stats

def create_calibration_data(num_samples: int = 100,
                          input_shape: tuple = (1, 3, 224, 224)) -> np.ndarray:
    """Create dummy calibration data for demonstration"""
    # In reality, this would be real data from your dataset
    return np.random.randn(num_samples, *input_shape[1:]).astype(np.float32)

def export_example_model() -> Path:
    """Create and export a simple example model for demonstration"""
    import torch
    import torch.nn as nn

    # Create a simple CNN-like model
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
            self.relu = nn.ReLU()
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
            self.fc = nn.Linear(16, 10)

        def forward(self, x):
            x = self.relu(self.conv1(x))
            x = self.pool(x)
            x = x.view(x.size(0), -1)
            x = self.fc(x)
            return x

    model = SimpleModel()

    # Export to ONNX
    dummy_input = torch.randn(1, 3, 224, 224)
    onnx_path = Path("models/example-model/model.onnx")
    onnx_path.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )

    # Create metadata
    metadata = {
        "model_name": "example-model",
        "framework": "pytorch",
        "format": "onnx",
        "version": "1.0",
        "input_shape": list(dummy_input.shape),
        "output_shape": [1, 10],
        "description": "Simple CNN model for demonstration",
        "created_by": "AetherEdge ML Tooling"
    }

    metadata_path = Path("models/example-model/metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return onnx_path