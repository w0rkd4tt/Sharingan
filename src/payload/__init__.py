"""
Configuration management
"""
import json
from pathlib import Path

def load_config(filename):
    config_path = Path(__file__).parent / filename
    with open(config_path) as f:
        return json.load(f)

CHECKING_CONFIG = load_config('Checking.json')
CRAWLING_CONFIG = load_config('Crawling.json')