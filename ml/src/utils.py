#!/usr/bin/env python3
"""Utility functions for AetherEdge ML tooling

Common utilities for model preparation, quantization, and benchmarking.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_metadata(model_dir: Path) -> Dict[str, Any]:
    """Load model metadata JSON file.

    Args:
        model_dir: Path to model directory

    Returns:
        Dictionary with model metadata
    """
    metadata_path = model_dir / "metadata.json"
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}")
        return {}

    with open(metadata_path, 'r') as f:
        return json.load(f)


def save_metadata(model_dir: Path, metadata: Dict[str, Any]) -> None:
    """Save metadata to JSON file.

    Args:
        model_dir: Path to model directory
        metadata: Dictionary with model metadata
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = model_dir / "metadata.json"

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")


def get_model_size(model_path: Path) -> int:
    """Get model file size in bytes.

    Args:
        model_path: Path to model file

    Returns:
        File size in bytes
    """
    return model_path.stat().st_size


def format_size(bytes_size: int) -> str:
    """Format byte size to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging with standard format.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

if __name__ == "__main__":
    # Test utility functions
    logger = setup_logging()
    test_path = Path("/tmp/test_model")
    metadata = {"model": "test", "format": "onnx"}
    save_metadata(test_path, metadata)
    loaded = load_metadata(test_path)
    print(f"Loaded metadata: {loaded}")
    print(f"Test completed successfully")
