"""
Centralized configuration loading for all bots.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from central config.yaml file."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# Global config instance - loaded once at import time
CONFIG = load_config()
