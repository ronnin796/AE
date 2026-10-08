#!/usr/bin/env python3
"""End-to-end inference tests for AetherEdge

Tests the full inference pipeline:
1. Server inference service loads INT8 model
2. Runs inference on sample input
3. Returns correct output shape and latency
4. Inference metrics stored in database
"""

import pytest
import sys
from pathlib import Path
import numpy as np

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.inference_service import InferenceService, InferenceRequest, get_inference_service


class TestInferenceService:
    """Test suite for inference service"""

    def setup_method(self):
        """Setup for each test"""
        self.service = InferenceService()
        # Reset global instance
        global _inference_service
        import app.services.inference_service as isv
        isv._inference_service = None

    @pytest.mark.asyncio
    async def test_service_can_load_model(self):
        """Test that service can find and load a model"""
        # The service should find model_int8.onnx if it exists
        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        session = self.service._get_or_load_session(model_path)
        assert session is not None
        assert len(session.get_inputs()) > 0
        assert len(session.get_outputs()) > 0

    @pytest.mark.asyncio
    async def test_run_inference_returns_valid_result(self):
        """Test that inference returns a valid result with correct shape"""
        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        request = InferenceRequest(
            request_id="test-001",
            model_id="model_int8",
            input=np.random.rand(1, 784).tolist(),
            input_shape=[1, 784],
        )

        result = await self.service.run_inference(request, model_path=model_path)

        assert result.success, f"Inference should succeed, got error: {result.error}"
        assert result.inference_time_ms > 0, "Latency should be > 0"
        assert len(result.output) == 10, f"Expected 10 outputs, got {len(result.output)}"
        assert result.output_shape == [1, 10], f"Expected shape [1, 10], got {result.output_shape}"

    @pytest.mark.asyncio
    async def test_inference_deterministic_with_same_input(self):
        """Test that same input produces same output"""
        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        # Create deterministic input
        input_data = np.zeros((1, 784), dtype=np.float32).tolist()

        request1 = InferenceRequest("det-001", "model_int8", input_data, [1, 784])
        request2 = InferenceRequest("det-002", "model_int8", input_data, [1, 784])

        result1 = await self.service.run_inference(request1, model_path=model_path)
        result2 = await self.service.run_inference(request2, model_path=model_path)

        assert result1.success and result2.success
        assert result1.output == result2.output, "Same input should produce same output"

    @pytest.mark.asyncio
    async def test_inference_latency_reasonable(self):
        """Test that inference latency is reasonable (< 100ms for this model)"""
        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        request = InferenceRequest(
            request_id="lat-001",
            model_id="model_int8",
            input=np.random.rand(1, 784).tolist(),
            input_shape=[1, 784],
        )

        result = await self.service.run_inference(request, model_path=model_path)

        assert result.success
        assert result.inference_time_ms < 100, f"Latency {result.inference_time_ms}ms should be < 100ms"

    @pytest.mark.asyncio
    async def test_get_result_retrieves_stored_result(self):
        """Test that get_result retrieves previously stored result"""
        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        request = InferenceRequest(
            request_id="store-001",
            model_id="model_int8",
            input=np.random.rand(1, 784).tolist(),
            input_shape=[1, 784],
        )

        result = await self.service.run_inference(request, model_path=model_path)
        retrieved = await self.service.get_result("store-001")

        assert retrieved is not None
        assert retrieved.request_id == result.request_id
        assert retrieved.output == result.output

    @pytest.mark.asyncio
    async def test_module_level_run_inference(self):
        """Test module-level run_inference function"""
        from app.services.inference_service import run_inference

        model_path = Path(__file__).parent.parent.parent / "ml" / "models" / "example-model" / "model_int8.onnx"

        if not model_path.exists():
            pytest.skip("INT8 model not found - run quantize.py first")

        result = await run_inference(
            request_id="module-001",
            model_id="model_int8",
            input_data=np.random.rand(1, 784).tolist(),
            input_shape=[1, 784],
        )

        assert result.success
        assert len(result.output) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])