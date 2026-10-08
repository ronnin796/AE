"""Inference service for remote model execution

Part II: Real ONNX Runtime inference with INT8 quantization support
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    HAS_ONNXRUNTIME = True
except ImportError:
    HAS_ONNXRUNTIME = False
    logger.warning("onnxruntime not available - inference will be simulated")


class InferenceRequest:
    """Request to run inference on a model"""
    def __init__(self, request_id: str, model_id: str, input: list, input_shape: list):
        self.request_id = request_id
        self.model_id = model_id
        self.input = input
        self.input_shape = input_shape


class InferenceResult:
    """Result of an inference request"""
    def __init__(
        self,
        request_id: str,
        node_id: str,
        model_id: str,
        timestamp: int,
        output: list,
        output_shape: list,
        inference_time_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ):
        self.request_id = request_id
        self.node_id = node_id
        self.model_id = model_id
        self.timestamp = timestamp
        self.output = output
        self.output_shape = output_shape
        self.inference_time_ms = inference_time_ms
        self.success = success
        self.error = error


class InferenceService:
    """Service for running ONNX model inference on the server"""

    MODEL_DIR = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "example-model"

    def __init__(self):
        self._sessions: dict[str, ort.InferenceSession] = {}
        self._results: dict[str, InferenceResult] = {}

    def _get_or_load_session(self, model_path: Path) -> ort.InferenceSession:
        """Get or load an ONNX Runtime session for a model"""
        session_key = str(model_path)
        if session_key not in self._sessions:
            logger.info(f"Loading model from {model_path}")
            session = ort.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"]
            )
            self._sessions[session_key] = session
            logger.info(f"Model loaded: inputs={[i.name for i in session.get_inputs()]}, "
                       f"outputs={[o.name for o in session.get_outputs()]}")
        return self._sessions[session_key]

    async def run_inference(
        self,
        request,
        node_id: str = "edge-node-1",
        model_path: Optional[Path] = None,
    ) -> InferenceResult:
        """
        Run inference on the specified model using ONNX Runtime.

        Args:
            request: InferenceRequest with model_id, input, input_shape
            node_id: ID of the node making the request (default: simulation)
            model_path: Optional path to model file (uses built-in if None)

        Returns:
            InferenceResult with output and timing information
        """
        import asyncio
        import time

        timestamp = int(datetime.utcnow().timestamp())

        # Determine model path
        if model_path is None:
            # For edge-deployed models, look in standard locations
            model_path = self.MODEL_DIR / "model_int8.onnx"
            if not model_path.exists():
                model_path = self.MODEL_DIR / "model.onnx"

        if not model_path.exists():
            error_msg = f"Model not found at {model_path}"
            logger.error(error_msg)
            return InferenceResult(
                request_id=request.request_id,
                node_id=node_id,
                model_id=request.model_id,
                timestamp=timestamp,
                output=[],
                output_shape=[],
                inference_time_ms=0.0,
                success=False,
                error=error_msg,
            )

        try:
            # Get or load session
            session = self._get_or_load_session(model_path)

            # Prepare input
            input_name = session.get_inputs()[0].name
            input_array = np.array(request.input, dtype=np.float32).reshape(request.input_shape)

            # Run inference
            start_time = time.perf_counter()
            outputs = session.run(None, {input_name: input_array})
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000

            # Extract output
            output_data = outputs[0]
            output_list = output_data.flatten().tolist()
            output_shape = list(output_data.shape)

            logger.info(f"Inference complete: {latency_ms:.2f}ms, output_shape={output_shape}")

            result = InferenceResult(
                request_id=request.request_id,
                node_id=node_id,
                model_id=request.model_id,
                timestamp=timestamp,
                output=output_list,
                output_shape=output_shape,
                inference_time_ms=latency_ms,
                success=True,
            )

            self._results[request.request_id] = result
            return result

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return InferenceResult(
                request_id=request.request_id,
                node_id=node_id,
                model_id=request.model_id,
                timestamp=timestamp,
                output=[],
                output_shape=[],
                inference_time_ms=0.0,
                success=False,
                error=str(e),
            )

    async def get_result(self, request_id: str) -> Optional[InferenceResult]:
        """Get a previously stored inference result"""
        return self._results.get(request_id)


# Global service instance
_inference_service = None


def get_inference_service() -> InferenceService:
    """Get the global inference service instance"""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service


async def run_inference(
    request_id: str,
    model_id: str,
    input_data: list,
    input_shape: list,
    node_id: str = "edge-node-1",
    model_path: Optional[Path] = None,
) -> InferenceResult:
    """Module-level function to run inference"""
    service = get_inference_service()
    request = InferenceRequest(request_id, model_id, input_data, input_shape)
    return await service.run_inference(request, node_id, model_path)