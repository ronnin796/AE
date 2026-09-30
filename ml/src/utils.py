```python
"""Utility functions for ML tooling"""
import json
import os
from pathlib import Path
from typing import Dict, Any


def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load model metadata from JSON file"""
    try:
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return {}
```

Save metadata to JSON file
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    ```

def get_model_info(model_path: Path) -> Dict[str, Any]:
    """Get basic model information"""
    if not model_path.exists():
        return {"error": "Model file not found"}

    stat = model_path.stat()
    return {
        "file_path": str(model_path),
        "file_size_bytes": stat.st_size,
        "file_size_mb": stat.st_size / (1024 * 1024),
        "modified_time": stat.st_mtime,
    }
```