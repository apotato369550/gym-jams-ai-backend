#!/usr/bin/env python3
"""Test script for /analyze_workout_history endpoint."""

import argparse
import json
import httpx
from pathlib import Path
from datetime import datetime

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

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--test", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

# Prepare request payload
payload = {
    "history": workout_history,
    "user_profile": user_profile
}

# Conditionally inject test/debug flags
if args.test:
    payload["test"] = True
if args.debug:
    payload["debug"] = True

# Make request
client = httpx.Client(timeout=60.0)
response = client.post("http://localhost:8000/analyze_workout_history", json=payload)

# Print response
print(f"Status Code: {response.status_code}")
data = response.json()
if "formatted" in data:
    print("\n[formatted]")
    print(json.dumps(data["formatted"], indent=2))
    print("\n[raw]")
    print(json.dumps(data["raw"], indent=2))
else:
    print(json.dumps(data, indent=2))

# Write result to file
results_dir = PROJECT_ROOT / "results" / "workout_history_analysis"
results_dir.mkdir(parents=True, exist_ok=True)

if args.test:
    result_file = results_dir / "mock_latest.json"
else:
    result_file = results_dir / (datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + "_test_workout_history.json")

with open(result_file, "w") as f:
    json.dump(response.json(), f, indent=2)

print(f"\nResult saved to: {result_file}")
