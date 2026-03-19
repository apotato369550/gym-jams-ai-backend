#!/usr/bin/env python3
"""Test script for /generate_gym_chat_completions endpoint."""

import json
import httpx
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load fixture data
user_profile_path = PROJECT_ROOT / "data" / "user_profile.json"

with open(user_profile_path) as f:
    user_profile = json.load(f)

# Prepare request payload with hardcoded sample messages
messages = [
    {
        "role": "user",
        "content": "Hey Jim! I only have 15 minutes today and I'm at home. What can I do?"
    }
]

payload = {
    "messages": messages,
    "user_profile": user_profile
}

# Make request
client = httpx.Client()
response = client.post("http://localhost:8000/generate_gym_chat_completions", json=payload)

# Print response
print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Write result to file
results_dir = PROJECT_ROOT / "results" / "gym_chat"
results_dir.mkdir(parents=True, exist_ok=True)
result_file = results_dir / "latest.json"

with open(result_file, "w") as f:
    json.dump(response.json(), f, indent=2)

print(f"\nResult saved to: {result_file}")
