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
from src.utils import setup_logging, save_metadata, load_metadata, format_size

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
                return {'x': next(self.iterator)}  # Return dict mapping input name to data
            except StopIteration:
                return None

        def rewind(self):
            self.iterator = iter(self.data_list)

    logger.info("Starting static quantization...")
    logger.info(f"Input model: {model_path} ({format_size(model_path.stat().st_size)})")
    logger.info(f"Output model: {output_path}")

    # Pre-process model for quantization compatibility with opset 18
    # Shape inference issues with newer opsets are common; pre-process before quantizing
    from onnx import shape_inference
    import shutil

    model_preproc_path = model_path.parent / f"{model_path.stem}_preproc.onnx"
    model_orig_path = model_path.parent / f"{model_path.stem}_orig.onnx"

    # Keep original backup
    shutil.copy2(str(model_path), str(model_orig_path))

    # Pre-process the model for quantization compatibility
    shape_inference.infer_shapes_path(str(model_path), str(model_preproc_path))
    logger.info(f"Preprocessed model for quantization saved to {model_preproc_path}")

    calibration_reader = SimpleCalibrationReader(calibration_data)

    # Static quantization: use QDQ (QuantizeLinear/DequantizeLinear) format
    # QDQ is recommended by ONNX Runtime for x64 CPUs for best performance
    logger.info("Running static quantization with QDQ format...")
    quantize_static(
        model_input=str(model_preproc_path),
        model_output=str(output_path),
        calibration_data_reader=calibration_reader,
        quant_format=QuantFormat.QDQ,  # QDQ format: QuantizeLinear/DequantizeLinear
        weight_type=QuantType.QInt8,
        per_channel=per_channel,
        reduce_range=reduce_range,
    )

    logger.info(f"Quantization complete! Output size: {format_size(output_path.stat().st_size)}")

    # Save quantization metadata
    metadata = load_metadata(model_path.parent) or {}
    metadata.update({
        "quantization": {
            "method": "static",
            "quant_format": "QDQ",
            "weight_type": "QInt8",
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


def compare_fp32_int8(
    fp32_path: Path,
    int8_path: Path,
    test_data_count: int = 10,
    provider: str = "CPUExecutionProvider"
) -> Dict[str, Any]:
    """Compare FP32 and INT8 model inference results.

    Args:
        fp32_path: Path to FP32 ONNX model
        int8_path: Path to INT8 ONNX model
        test_data_count: Number of test samples to compare
        provider: ONNX Runtime execution provider

    Returns:
        Comparison dictionary with latency and accuracy
    """
    import onnxruntime as ort
    import numpy as np

    fp32_sess = ort.InferenceSession(str(fp32_path), providers=[provider])
    int8_sess = ort.InferenceSession(str(int8_path), providers=[provider])

    input_name = fp32_sess.get_inputs()[0].name

    # Generate test data
    test_data = [np.random.rand(1, 784).astype(np.float32) for _ in range(test_data_count)]

    fp32_preds = []
    int8_preds = []

    for x in test_data:
        # FP32 inference
        fp32_out = fp32_sess.run(None, {input_name: x})[0]
        # INT8 inference
        int8_out = int8_sess.run(None, {input_name: x})[0]

        # Get predicted class (argmax)
        fp32_pred = np.argmax(fp32_out, axis=1)[0]
        int8_pred = np.argmax(int8_out, axis=1)[0]

        fp32_preds.append(fp32_pred)
        int8_preds.append(int8_pred)

    # Calculate accuracy (percentage of matching predictions)
    matching = sum(1 for a, b in zip(fp32_preds, int8_preds) if a == b)
    accuracy = matching / test_data_count * 100 if test_data_count > 0 else 0

    # Calculate latency
    import time
    latencies_fp32 = []
    latencies_int8 = []

    for x in test_data[:5]:
        start = time.perf_counter()
        fp32_sess.run(None, {input_name: x})
        latencies_fp32.append((time.perf_counter() - start) * 1000)

    for x in test_data[:5]:
        start = time.perf_counter()
        int8_sess.run(None, {input_name: x})
        latencies_int8.append((time.perf_counter() - start) * 1000)

    results = {
        "fp32_size_bytes": fp32_path.stat().st_size,
        "int8_size_bytes": int8_path.stat().st_size,
        "size_reduction_percent": (fp32_path.stat().st_size - int8_path.stat().st_size) / fp32_path.stat().st_size * 100,
        "fp32_mean_latency_ms": np.mean(latencies_fp32) if latencies_fp32 else 0,
        "int8_mean_latency_ms": np.mean(latencies_int8) if latencies_int8 else 0,
        "fp32_std_latency_ms": float(np.std(latencies_fp32)) if latencies_fp32 else 0,
        "int8_std_latency_ms": float(np.std(latencies_int8)) if latencies_int8 else 0,
        "fp32_p95_latency_ms": float(np.percentile(latencies_fp32, 95)) if latencies_fp32 else 0,
        "int8_p95_latency_ms": float(np.percentile(latencies_int8, 95)) if latencies_int8 else 0,
        "accuracy_percent": accuracy,
        "num_test_samples": test_data_count,
        "provider": provider
    }

    logger.info(f"FP32 vs INT8 comparison:")
    logger.info(f"  Size reduction: {results['size_reduction_percent']:.1f}%")
    logger.info(f"  FP32 mean latency: {results['fp32_mean_latency_ms']:.2f} ms")
    logger.info(f"  INT8 mean latency: {results['int8_mean_latency_ms']:.2f} ms")
    logger.info(f"  Accuracy (argmax agreement): {results['accuracy_percent']:.1f}%")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fp32_model, int8_model = prepare_quantized_model()
    print(f"FP32 model: {fp32_model}")
    print(f"INT8 model: {int8_model}")