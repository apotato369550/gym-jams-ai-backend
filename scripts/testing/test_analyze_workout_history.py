#!/usr/bin/env python3
"""Test script for /analyze_workout_history endpoint."""

import json
import httpx
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load fixture data
user_profile_path = PROJECT_ROOT / "data" / "user_profile.json"
workout_history_path = PROJECT_ROOT / "data" / "sample_workout_history_data" / "workout_history.json"

with open(user_profile_path) as f:
    user_profile = json.load(f)

with open(workout_history_path) as f:
    workout_history = json.load(f)

# Prepare request payload
payload = {
    "history": workout_history,
    "user_profile": user_profile
}

# Make request
client = httpx.Client()
response = client.post("http://localhost:8000/analyze_workout_history", json=payload)

# Print response
print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Write result to file
results_dir = PROJECT_ROOT / "results" / "workout_history_analysis"
results_dir.mkdir(parents=True, exist_ok=True)
result_file = results_dir / "latest.json"

with open(result_file, "w") as f:
    json.dump(response.json(), f, indent=2)

print(f"\nResult saved to: {result_file}")
