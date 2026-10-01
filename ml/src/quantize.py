#!/usr/bin/env python3
"""Quantize ONNX models to INT8 for AetherEdge

Part I: Static quantization pipeline with calibration
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import numpy as np

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import setup_logging, save_metadata, load_metadata, format_size

logger = logging.getLogger(__name__)


def create_calibration_data(num_samples: int = 100, input_shape: Tuple[int, ...] = (1, 784)) -> List[np.ndarray]:
    """Generate synthetic calibration data for quantization.

    Args:
        num_samples: Number of calibration samples
        input_shape: Shape of input data

    Returns:
        List of numpy arrays for calibration
    """
    logger.info(f"Generating {num_samples} calibration samples...")
    calibration_data = []
    for _ in range(num_samples):
        # Generate random data normalized to [0, 1] range
        sample = np.random.rand(*input_shape).astype(np.float32)
        calibration_data.append(sample)
    return calibration_data


def quantize_model_static(
    model_path: Path,
    calibration_data: List[np.ndarray],
    output_path: Optional[Path] = None,
    per_channel: bool = False,
    reduce_range: bool = False
) -> Path:
    """Quantize ONNX model using static quantization.

    Args:
        model_path: Path to FP32 ONNX model
        calibration_data: List of calibration data samples
        output_path: Output path for INT8 model (defaults to model_path with '_int8' suffix)
        per_channel: Whether to use per-channel quantization
        reduce_range: Whether to reduce quantization range

    Returns:
        Path to quantized ONNX model
    """
    try:
        import onnx
        from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat, QuantType
    except ImportError as e:
        logger.error(f"Required packages not available: {e}")
        logger.error("Please install: pip install onnx onnxruntime onnxruntime-tools")
        raise

    if output_path is None:
        output_path = model_path.parent / f"{model_path.stem}_int8{model_path.suffix}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    class SimpleCalibrationReader(CalibrationDataReader):
        def __init__(self, data_list: List[np.ndarray]):
            self.data_list = data_list
            self.iterator = iter(data_list)

        def get_next(self):
            try:
                return next(self.iterator)
            except StopIteration:
                return None

        def rewind(self):
            self.iterator = iter(self.data_list)

    logger.info("Starting static quantization...")
    logger.info(f"Input model: {model_path} ({format_size(model_path.stat().st_size)})")
    logger.info(f"Output model: {output_path}")

    calibration_reader = SimpleCalibrationReader(calibration_data)

    quantize_static(
        model_input=str(model_path),
        model_output=str(output_path),
        calibration_data_reader=calibration_reader,
        quant_format=QuantFormat.QOperator if per_channel else QuantFormat.QOperator,
        weight_type=QuantType.QInt8,
        reduce_range=reduce_range,
        per_channel=per_channel
    )

    logger.info(f"Quantization complete! Output size: {format_size(output_path.stat().st_size)}")

    # Save quantization metadata
    metadata = load_metadata(model_path.parent) or {}
    metadata.update({
        "quantization": {
            "method": "static",
            "per_channel": per_channel,
            "reduce_range": reduce_range,
            "calibration_samples": len(calibration_data)
        },
        "quantized_model_size_bytes": output_path.stat().st_size,
        "original_model_size_bytes": model_path.stat().st_size,
        "compression_ratio": model_path.stat().st_size / output_path.stat().st_size if output_path.stat().st_size > 0 else 0
    })
    save_metadata(output_path.parent, metadata)

    return output_path


def quantize_model_dynamic(
    model_path: Path,
    output_path: Optional[Path] = None,
    weight_type: str = "QInt8"
) -> Path:
    """Quantize ONNX model using dynamic quantization.

    Args:
        model_path: Path to FP32 ONNX model
        output_path: Output path for INT8 model (defaults to model_path with '_int8' suffix)
        weight_type: Weight quantization type (QInt8, QUInt8)

    Returns:
        Path to quantized ONNX model
    """
    try:
        import onnx
        from onnxruntime.quantization import quantize_dynamic, QuantType
    except ImportError as e:
        logger.error(f"Required packages not available: {e}")
        logger.error("Please install: pip install onnx onnxruntime onnxruntime-tools")
        raise

    if output_path is None:
        output_path = model_path.parent / f"{model_path.stem}_int8{model_path.suffix}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting dynamic quantization...")
    logger.info(f"Input model: {model_path} ({format_size(model_path.stat().st_size)})")
    logger.info(f"Output model: {output_path}")

    weight_type_map = {
        "QInt8": QuantType.QInt8,
        "QUInt8": QuantType.QUInt8
    }

    quantize_dynamic(
        model_input=str(model_path),
        model_output=str(output_path),
        weight_type=weight_type_map.get(weight_type, QuantType.QInt8)
    )

    logger.info(f"Dynamic quantization complete! Output size: {format_size(output_path.stat().st_size)}")

    # Save quantization metadata
    metadata = load_metadata(model_path.parent) or {}
    metadata.update({
        "quantization": {
            "method": "dynamic",
            "weight_type": weight_type
        },
        "quantized_model_size_bytes": output_path.stat().st_size,
        "original_model_size_bytes": model_path.stat().st_size,
        "compression_ratio": model_path.stat().st_size / output_path.stat().st_size if output_path.stat().st_size > 0 else 0
    })
    save_metadata(output_path.parent, metadata)

    return output_path


def prepare_quantized_model(
    model_dir: Path = Path("models/example-model"),
    use_static: bool = True,
    num_calibration_samples: int = 100
) -> Tuple[Path, Path]:
    """Prepare both FP32 and INT8 versions of a model.

    Args:
        model_dir: Directory containing the FP32 model
        use_static: Whether to use static quantization (True) or dynamic (False)
        num_calibration_samples: Number of calibration samples for static quantization

    Returns:
        Tuple of (fp32_path, int8_path)
    """
    model_dir = model_dir.resolve()
    fp32_path = model_dir / "model.onnx"

    if not fp32_path.exists():
        logger.info("FP32 model not found. Creating demo model...")
        from export import prepare_model
        fp32_path = prepare_model(model_dir)

    if use_static:
        logger.info("Creating calibration data for static quantization...")
        calibration_data = create_calibration_data(
            num_samples=num_calibration_samples,
            input_shape=(1, 784)  # From our demo model
        )
        int8_path = quantize_model_static(fp32_path, calibration_data)
    else:
        int8_path = quantize_model_dynamic(fp32_path)

    return fp32_path, int8_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fp32_model, int8_model = prepare_quantized_model()
    print(f"FP32 model: {fp32_model}")
    print(f"INT8 model: {int8_model}")