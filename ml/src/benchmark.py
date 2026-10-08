#!/usr/bin/env python3
"""Benchmark ONNX models (FP32 vs INT8) for AetherEdge

Part I: Basic benchmarking to measure inference time, model size, and accuracy
"""

import logging
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import setup_logging, format_size

logger = logging.getLogger(__name__)


def generate_test_data(num_samples: int, input_shape: Tuple[int, ...] = (1, 784)) -> List[np.ndarray]:
    """Generate test data for benchmarking.

    Args:
        num_samples: Number of test samples
        input_shape: Shape of input data

    Returns:
        List of numpy arrays
    """
    return [np.random.rand(*input_shape).astype(np.float32) for _ in range(num_samples)]


def run_inference_benchmark(
    model_path: Path,
    test_data: List[np.ndarray],
    warmup_runs: int = 10,
    num_runs: int = 100,
    provider: str = "CPUExecutionProvider"
) -> Dict[str, Any]:
    """Run inference benchmark on ONNX model.

    Args:
        model_path: Path to ONNX model
        test_data: List of test input arrays
        warmup_runs: Number of warmup runs
        num_runs: Number of benchmark runs
        provider: ONNX Runtime execution provider

    Returns:
        Dictionary with benchmark results
    """
    try:
        import onnxruntime as ort
    except ImportError as e:
        logger.error(f"onnxruntime not available: {e}")
        return {}

    # Create session
    session = ort.InferenceSession(str(model_path), providers=[provider])
    input_name = session.get_inputs()[0].name

    logger.info(f"Benchmarking {model_path} with {provider}")
    logger.info(f"Model size: {format_size(model_path.stat().st_size)}")

    # Warmup
    logger.info(f"Running {warmup_runs} warmup iterations...")
    for _ in range(warmup_runs):
        _ = session.run(None, {input_name: test_data[0]})

    # Benchmark
    logger.info(f"Running {num_runs} benchmark iterations...")
    latencies = []

    for i, sample in enumerate(test_data[:num_runs]):
        start = time.perf_counter()
        _ = session.run(None, {input_name: sample})
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to ms

    latencies = np.array(latencies)

    results = {
        "model_path": str(model_path),
        "model_size_bytes": model_path.stat().st_size,
        "model_size_human": format_size(model_path.stat().st_size),
        "provider": provider,
        "num_runs": num_runs,
        "warmup_runs": warmup_runs,
        "latency_ms": {
            "mean": float(np.mean(latencies)),
            "median": float(np.median(latencies)),
            "std": float(np.std(latencies)),
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        },
        "throughput": {
            "inferences_per_second": 1000 / np.mean(latencies) if np.mean(latencies) > 0 else 0
        }
    }

    logger.info(f"Mean latency: {results['latency_ms']['mean']:.2f} ms")
    logger.info(f"Throughput: {results['throughput']['inferences_per_second']:.1f} inferences/s")

    return results


def compare_models(
    fp32_path: Path,
    int8_path: Path,
    test_data: List[np.ndarray],
    num_runs: int = 100,
    provider: str = "CPUExecutionProvider"
) -> Dict[str, Any]:
    """Compare FP32 and INT8 models.

    Args:
        fp32_path: Path to FP32 model
        int8_path: Path to INT8 model
        test_data: Test data for benchmarking
        num_runs: Number of benchmark runs
        provider: ONNX Runtime provider

    Returns:
        Comparison results
    """
    logger.info("=" * 60)
    logger.info("MODEL COMPARISON: FP32 vs INT8")
    logger.info("=" * 60)

    # Benchmark FP32
    fp32_results = run_inference_benchmark(
        fp32_path, test_data, num_runs=num_runs, provider=provider
    )

    # Benchmark INT8
    int8_results = run_inference_benchmark(
        int8_path, test_data, num_runs=num_runs, provider=provider
    )

    # Calculate improvements
    if fp32_results and int8_results:
        speedup = fp32_results['latency_ms']['mean'] / int8_results['latency_ms']['mean'] if int8_results['latency_ms']['mean'] > 0 else 0
        size_reduction = (fp32_results['model_size_bytes'] - int8_results['model_size_bytes']) / fp32_results['model_size_bytes'] * 100

        comparison = {
            "fp32": fp32_results,
            "int8": int8_results,
            "comparison": {
                "speedup_factor": speedup,
                "latency_improvement_percent": (1 - 1/speedup) * 100 if speedup > 0 else 0,
                "size_reduction_percent": size_reduction,
                "size_reduction_bytes": fp32_results['model_size_bytes'] - int8_results['model_size_bytes']
            }
        }

        logger.info("=" * 60)
        logger.info("COMPARISON RESULTS:")
        logger.info(f"  Speedup factor: {speedup:.2f}x")
        logger.info(f"  Latency improvement: {comparison['comparison']['latency_improvement_percent']:.1f}%")
        logger.info(f"  Size reduction: {size_reduction:.1f}%")
        logger.info(f"  FP32 size: {fp32_results['model_size_human']}")
        logger.info(f"  INT8 size: {int8_results['model_size_human']}")
        logger.info("=" * 60)

        return comparison
    else:
        logger.error("Failed to run benchmarks")
        return {}


def run_full_benchmark(
    model_dir: Path = Path("models/example-model"),
    num_samples: int = 100,
    num_runs: int = 100,
    provider: str = "CPUExecutionProvider",
    output_file: Optional[Path] = None
) -> Dict[str, Any]:
    """Run complete benchmark suite.

    Args:
        model_dir: Directory containing models
        num_samples: Number of test samples
        num_runs: Number of benchmark runs
        provider: ONNX Runtime provider
        output_file: Optional file to save results

    Returns:
        Complete benchmark results
    """
    fp32_path = model_dir / "model.onnx"
    int8_path = model_dir / "model_int8.onnx"

    if not fp32_path.exists():
        logger.error(f"FP32 model not found at {fp32_path}")
        logger.info("Run export.py and quantize.py first")
        return {}

    if not int8_path.exists():
        logger.error(f"INT8 model not found at {int8_path}")
        logger.info("Run quantize.py first")
        return {}

    logger.info(f"Generating {num_samples} test samples...")
    test_data = generate_test_data(num_samples)

    results = compare_models(fp32_path, int8_path, test_data, num_runs, provider)

    if results and output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_full_benchmark()
    if results:
        print(json.dumps(results, indent=2))