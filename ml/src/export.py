#!/usr/bin/env python3
"""Export PyTorch models to ONNX format for AetherEdge

Part I: Basic ONNX export pipeline
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import torch
import torch.nn as nn
import numpy as np

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import setup_logging, save_metadata, format_size

logger = logging.getLogger(__name__)


class SimpleMLP(nn.Module):
    """Simple MLP for demonstration"""

    def __init__(self, input_size: int = 784, hidden_size: int = 128, num_classes: int = 10):
        super(SimpleMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


def create_demo_model() -> Tuple[nn.Module, Dict[str, Any]]:
    """Create a demo PyTorch model for export.

    Returns:
        Model instance and example input shape
    """
    model = SimpleMLP(input_size=784, hidden_size=128, num_classes=10)
    model.eval()

    # Example input for ONNX export
    example_input = torch.randn(1, 784)

    metadata = {
        "model_type": "MLP",
        "input_size": 784,
        "hidden_size": 128,
        "num_classes": 10,
        "input_shape": [1, 784],
        "output_shape": [1, 10],
        "framework": "PyTorch",
        "export_format": "ONNX"
    }

    return model, metadata, example_input


def export_to_onnx(
    model: nn.Module,
    example_input: torch.Tensor,
    output_path: Path,
    metadata: Dict[str, Any],
    opset_version: int = 11
) -> Path:
    """Export PyTorch model to ONNX format.

    Args:
        model: PyTorch model (in eval mode)
        example_input: Example input tensor for tracing
        output_path: Output path for ONNX file
        metadata: Model metadata
        opset_version: ONNX opset version

    Returns:
        Path to exported ONNX file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to ONNX
    torch.onnx.export(
        model,
        example_input,
        str(output_path),
        opset_version=opset_version,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )

    logger.info(f"Exported model to {output_path}")
    logger.info(f"Model size: {format_size(output_path.stat().st_size)}")

    # Save metadata
    metadata["onnx_opset"] = opset_version
    metadata["model_size_bytes"] = output_path.stat().st_size
    save_metadata(output_path.parent, metadata)

    return output_path


def prepare_model(
    output_dir: Path = Path("models/example-model"),
    input_size: int = 784,
    hidden_size: int = 128,
    num_classes: int = 10
) -> Path:
    """Prepare and export a demo model.

    Args:
        output_dir: Output directory for model
        input_size: Input features size
        hidden_size: Hidden layer size
        num_classes: Number of output classes

    Returns:
        Path to exported ONNX model
    """
    logger.info("Creating demo model...")
    model, metadata, example_input = create_demo_model()

    onnx_path = output_dir / "model.onnx"
    logger.info(f"Exporting to {onnx_path}...")

    export_to_onnx(model, example_input, onnx_path, metadata)

    logger.info("Model preparation complete!")
    return onnx_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    model_path = prepare_model()
    print(f"Exported model: {model_path}")