"""Inference service for remote model execution"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from dataclasses import dataclass


class InferenceRequest(BaseModel):
    """Request to run inference on a model"""
    request_id: str
    model_id: str
    input: list[float]
    input_shape: list[int]


@dataclass
class InferenceResult:
    """Result of an inference request"""
    request_id: str
    node_id: str
    model_id: str
    timestamp: int
    output: list[float]
    output_shape: list[int]
    inference_time_ms: float
    success: bool
    error: Optional[str] = None


class InferenceService:
    """Service for managing inference requests"""

    def __init__(self):
        self._results: dict[str, InferenceResult] = {}

    async def run_inference(
        self,
        request: InferenceRequest,
        node_id: str = "edge-node-1",
    ) -> InferenceResult:
        """
        Run inference on the specified model.

        In Part I, this is a simplified implementation that:
        - Records the request
        - Simulates output
        - Returns a result

        Part II will include:
        - Actual model loading
        - Model registry integration
        - Real inference execution
        - Result streaming
        """
        timestamp = int(datetime.utcnow().timestamp())

        # Simulate inference output (in Part II, this will run actual model)
        output = request.input.copy()  # Simplified: echo input
        output_shape = [1, len(output)]

        # Simulate a small inference latency
        import asyncio
        await asyncio.sleep(0.05)  # 50ms simulated

        result = InferenceResult(
            request_id=request.request_id,
            node_id=node_id,
            model_id=request.model_id,
            timestamp=timestamp,
            output=output,
            output_shape=output_shape,
            inference_time_ms=50.0,
            success=True,
        )

        self._results[request.request_id] = result
        return result

    async def get_result(self, request_id: str) -> Optional[InferenceResult]:
        """Get a previously stored inference result"""
        return self._results.get(request_id)


# Module-level service instance
_inference_service = InferenceService()


async def run_inference(
    request_id: str,
    model_id: str,
    input_data: list[float],
    input_shape: list[int],
) -> InferenceResult:
    """Module-level function to run inference"""
    request = InferenceRequest(
        request_id=request_id,
        model_id=model_id,
        input=input_data,
        input_shape=input_shape,
    )
    return await _inference_service.run_inference(request)