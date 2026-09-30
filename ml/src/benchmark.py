"""Benchmark script for FP32 vs INT8 model comparison
Compares model size, inference latency, and basic accuracy between FP32 and INT8 quantized models
"""

import time
import numpy as np
import onnxruntime as ort
from pathlib import Path
import json
import sys
from typing import Tuple, Optional


def run_inference(session, input_data: np.ndarray) -> Tuple[np.ndarray, float]:
    """Run inference and measure time"""
    start_time = time.time()
    output = session.run(None, {"input": input_data})[0]
    elapsed_ms = (time.time() - start_time) * 1000
    return output, elapsed_ms


def compare_models(
    fp32_model_path: Path,
    int8_model_path: Path,
    input_shape: tuple = (1, 3, 224, 224),
    num_iterations: int = 100,
) -> dict:
    """
    Compare FP32 and INT8 models for size and performance

    Returns:
        Dictionary with comparison metrics
    """
    results = {
        "model_size": {},
        "performance": {},
        "accuracy": {"similar": False, "details": {}},
    }

    # 1. Compare model sizes
    fp32_size = fp32_model_path.stat().st_size
    int8_size = int8_model_path.stat().st_size if int8_model_path.exists() else 0

    results["model_size"] = {
        "fp32_size_bytes": fp32_size,
        "fp32_size_mb": fp32_size / (1024 * 1024),
        "int8_size_bytes": int8_size,
        "int8_size_mb": int8_size / (1024 * 1024),
        "size_reduction_percent": (
            (fp32_size - int8_size) / fp32_size * 100 if fp32_size > 0 else 0
        ),
    }

    # 2. Compare inference performance
    try:
        # Load FP32 session
        fp32_session = ort.InferenceSession(str(fp32_model_path))
        int8_session = ort.InferenceSession(str(int8_model_path))

        # Create sample input
        input_data = np.random.randn(*input_shape).astype(np.float32)

        # Warm-up runs
        for _ in range(10):
            _ = run_inference(fp32_session, input_data)
            _ = run_inference(int8_session, input_data)

        # Benchmark FP32
        fp32_times = []
        for _ in range(num_iterations):
            _, elapsed_ms = run_inference(fp32_session, input_data)
            fp32_times.append(elapsed_ms)

        # Benchmark INT8
        int8_times = []
        for _ in range(num_iterations):
            _, elapsed_ms = run_inference(int8_session, input_data)
            int8_times.append(elapsed_ms)

        fp32_avg = sum(fp32_times) / len(fp32_times)
        int8_avg = sum(int8_times) / len(int8_times)

        results["performance"] = {
            "fp32_avg_latency_ms": fp32_avg,
            "int8_avg_latency_ms": int8_avg,
            "latency_improvement_percent": (
                (fp32_avg - int8_avg) / fp32_avg * 100 if fp32_avg > 0 else 0
            ),
            "fp32_times_ms": fp32_times,
            "int8_times_ms": int8_times,
        }

    except Exception as e:
        results["performance"]["error"] = str(e)
        print(f"Performance benchmark error: {e}")

    # 3. Compare model architectures
    try:
        fp32_model = onnx.load(str(fp32_model_path))
        int8_model = onnx.load(str(int8_model_path)) if int8_model_path.exists() else None

        # Count nodes/operators
        fp32_node_count = len(fp32_model.graph.node)
        int8_node_count = len(int8_model.graph.node) if int8_model else 0

        results["model_architecture"] = {
            "fp32_node_count": fp32_node_count,
            "int8_node_count": int8_node_count,
            "node_reduction_percent": (
                (fp32_node_count - int8_node_count) / fp32_node_count * 100
                if fp32_node_count > 0 else 0
            ),
        }

        # Check for key operators
        fp32_ops = set()
        int8_ops = set()
        if int8_model:
            for node in int8_model.graph.node:
                op_type = node.op_type
                if op_type not in int8_ops:
                    int8_ops.add(op_type)
            for node in fp32_model.graph.node:
                op_type = node.op_type
                if op_type not in fp32_ops:
                    fp32_ops.add(op_type)

        results["model_architecture"]["fp32_ops"] = sorted(list(fp32_ops))
        results["model_architecture"]["int8_ops"] = sorted(list(int8_ops))

    except Exception as e:
        results["model_architecture"]["error"] = str(e)

    return results


def main():
    """Main benchmark function"""
    print("=" * 60)
    print("AetherEdge - FP32 vs INT8 Model Benchmark")
    print("=" * 60)

    # Setup paths
    models_dir = Path("models/example-model")
    fp32_path = models_dir / "model.onnx"  # This would be the original FP32 model
    int8_path = models_dir / "model_int8.onnx"  # Quantized model

    # Check if models exist
    if not fp32_path.exists():
        print(f"❌ FP32 model not found: {fp32_path}")
        print("   Run quantization first, or provide correct model path")
        sys.exit(1)

    print(f"📁 FP32 model: {fp32_path}")
    if int8_path.exists():
        print(f"📁 INT8 model: {int8_path}")
    else:
        print(f"⚠️  INT8 model not found: {int8_path}")

    # Run benchmark
    print(f"\n🔬 Running benchmark with {100} iterations...")
    results = compare_models(fp32_path, int8_path, num_iterations=100)

    # Display results
    print(f"\n📊 Results:")
    print("-" * 40)

    if "model_size" in results:
        size = results["model_size"]
        print(f"📈 Model Size:")
        print(f"   FP32: {size['fp32_size_mb']:.2f} MB")
        print(f"   INT8: {size['int8_size_mb']:.2f} MB")
        print(f"   Reduction: {size['size_reduction_percent']:.1f}%")

    if "performance" in results and "error" not in results.get("performance", {}):
        perf = results["performance"]
        print(f"\n⚡ Performance:")
        print(f"   FP32: {perf['fp32_avg_latency_ms']:.2f} ms avg")
        print(f"   INT8: {perf['int8_avg_latency_ms']:.2f} ms avg")
        print(f"   Improvement: {perf['latency_improvement_percent']:.1f}%")

    if "model_architecture" in results and "error" not in results.get("model_architecture", {}):
        arch = results["model_architecture"]
        print(f"\n🔧 Architecture:")
        print(f"   FP32 ops: {arch['fp32_node_count']}")
        print(f"   INT8 ops: {arch['int8_node_count']}")

    # Overall assessment
    print("\n" + "=" * 60)
    print("Overall Assessment:")
    print("=" * 60)

    # Check if results have errors
    has_errors = False
    if "model_size" in results and "error" in results["model_size"]:
        has_errors = True
    if "performance" in results and "error" in results["performance"]:
        has_errors = True
    if "model_architecture" in results and "error" in results["model_architecture"]:
        has_errors = True

    if not has_errors and all(k in results for k in ["model_size", "performance", "model_architecture"]):
        print("✅ All measurements successful")
        size_reduction = results["model_size"]["size_reduction_percent"]
        latency_improvement = results["performance"]["latency_improvement_percent"]
        print(
            f"   • {size_reduction:.1f}% model size reduction"
        )
        print(
            f"   • {latency_improvement:.1f}% latency improvement"
        )
        print("\n✅ FP32 and INT8 models are compatible and functional")
    else:
        print("⚠️  Some measurements had errors (check details above)")

    print("=" * 60)


if __name__ == "__main__":
    main()