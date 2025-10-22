#!/usr/bin/env python3
"""
Simple JSON API to list all available Skill Seeker configs.
Usage: python3 api/list_configs.py
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


def load_config_metadata(config_path: Path) -> Dict[str, Any]:
    """Load metadata from a config file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        return {
            "id": config_path.stem,
            "name": config.get("name", config_path.stem),
            "description": config.get("description", "No description available"),
            "base_url": config.get("base_url", ""),
            "max_pages": config.get("max_pages", 500),
            "categories": list(config.get("categories", {}).keys()) if config.get("categories") else [],
            "config_file": f"configs/{config_path.name}"
        }
    except Exception as e:
        return {
            "id": config_path.stem,
            "name": config_path.stem,
            "description": f"Error loading config: {str(e)}",
            "base_url": "",
            "error": True
        }


def list_configs() -> List[Dict[str, Any]]:
    """List all available configs in the configs/ directory."""
    repo_root = Path(__file__).parent.parent
    configs_dir = repo_root / "configs"

    if not configs_dir.exists():
        return []

    configs = []
    for config_file in sorted(configs_dir.glob("*.json")):
        metadata = load_config_metadata(config_file)
        configs.append(metadata)

    return configs


def generate_api_response() -> Dict[str, Any]:
    """Generate the full API response."""
    configs = list_configs()

    return {
        "version": "1.0.0",
        "total_configs": len(configs),
        "configs": configs,
        "api_endpoint": "/api/configs",
        "usage": {
            "list_all": "GET /api/configs",
            "get_config": "GET /api/configs/{id}"
        }
    }


if __name__ == "__main__":
    response = generate_api_response()
    print(json.dumps(response, indent=2))
