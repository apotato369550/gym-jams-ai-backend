#!/usr/bin/env python3
"""Test script for /analyze_workout endpoint."""

import json
import httpx
from pathlib import Path
from datetime import datetime

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load fixture data
user_profile_path = PROJECT_ROOT / "data" / "user_profile.json"
workout_session_path = PROJECT_ROOT / "data" / "sample_workout_data" / "workout_session.json"

with open(user_profile_path) as f:
    user_profile = json.load(f)

with open(workout_session_path) as f:
    workout_session = json.load(f)

# Prepare request payload
payload = {
    "workout": workout_session,
    "user_profile": user_profile
}

# Make request
client = httpx.Client(timeout=60.0)
response = client.post("http://localhost:8000/analyze_workout", json=payload)

# Print response
print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Write result to file
results_dir = PROJECT_ROOT / "results" / "workout_analysis"
results_dir.mkdir(parents=True, exist_ok=True)
result_file = results_dir / (datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + "_test_analyze_workout.json")

with open(result_file, "w") as f:
    json.dump(response.json(), f, indent=2)

print(f"\nResult saved to: {result_file}")
