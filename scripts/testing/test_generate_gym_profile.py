#!/usr/bin/env python3
"""Test script for /generate_gym_profile endpoint."""

import json
import httpx
from pathlib import Path
from datetime import datetime

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load fixture data
user_profile_path = PROJECT_ROOT / "data" / "user_profile.json"

with open(user_profile_path) as f:
    user_profile = json.load(f)

# Make request
client = httpx.Client(timeout=60.0)
response = client.post("http://localhost:8000/generate_gym_profile", json=user_profile)

# Print response
print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Write result to file
results_dir = PROJECT_ROOT / "results" / "gym_profiles"
results_dir.mkdir(parents=True, exist_ok=True)
result_file = results_dir / (datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + "_test_gym_profile.json")

with open(result_file, "w") as f:
    json.dump(response.json(), f, indent=2)

print(f"\nResult saved to: {result_file}")
