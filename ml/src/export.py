"""Model export and quantization for ONNX Runtime"""
"""
AetherEdge ML Tooling - Python scripts for model preparation and quantization

This module provides tools for:
1. Exporting PyTorch models to ONNX format
2. Static INT8 quantization
3. Model benchmarking (FP32 vs INT8)
"""

from pathlib import Path
import numpy as np
import torch
import onnx
from onnx import helper
from onnxruntime import quantization
import json
import os
from typing import Optional, Tuple

# Global model path for demo purposes
DEFAULT_MODEL_PATH = "models/example-model/model.onnx"


class ModelExporter:
    """Utility class for model export and quantization"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else None
        self.model = None

    def export_model(self, model: torch.nn.Module,
                    output_dir: str = "models",
                    model_name: str = "example-model") -> Path:
        """
        Export PyTorch model to ONNX format

        Args:
            model: PyTorch model to export
            output_dir: Directory to save the model
            model_name: Name for the model file

        Returns:
            Path to the exported ONNX model
        """
        # Create models directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save model with proper path
        model_path = output_dir / f"{model_name}.onnx"

        # Export model
        torch.onnx.export(
            model,
            torch.randn(1, 3, 224, 224),  # Example input shape
            model_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
        )

        info(f"Model exported to: {model_path}")
        return model_path

    def export_example_model(self) -> Path:
        """Export a sample model for demonstration"""
        model_path = self.export_model(self._create_dummy_model(), "models", "example-model")
        return model_path

    def _create_dummy_model(self) -> torch.nn.Module:
        """Create a simple model for demonstration"""
        class DummyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = torch.nn.Linear(100, 10)

            def forward(self, x):
                return self.fc(x)

        return DummyModel()