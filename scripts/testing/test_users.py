#!/usr/bin/env python3
"""
End-to-end CLI test script for gym-jams FastAPI backend.
Tests user registration, login, workout analysis, and chat completions.
Cleans up test data from database on exit.

Usage: python scripts/utils/test_users.py
"""

import httpx
import uuid
import json
import os
import sys
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv


# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
WORKOUT_SESSION_PATH = PROJECT_ROOT / "data" / "sample_workout_data" / "workout_session.json"
USER_PROFILE_PATH = PROJECT_ROOT / "data" / "user_profile.json"

# Load env vars
load_dotenv(ENV_PATH)

# API base URL
API_BASE_URL = "http://127.0.0.1:8000"

# DB connection details from env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "gym_jams")

# Test data
TEST_EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"


def load_fixture(path):
    """Load JSON fixture file."""
    with open(path, "r") as f:
        return json.load(f)


def test_step_1_register():
    """Step 1: Register user."""
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME,
    }
    try:
        response = httpx.post(
            f"{API_BASE_URL}/register_user",
            json=payload,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("user_id")
            email = data.get("email")
            print(f"[PASS] Step 1: register_user — user_id={user_id}")
            return user_id, True
        else:
            print(f"[FAIL] Step 1: register_user — status {response.status_code}: {response.text}")
            return None, False
    except Exception as e:
        print(f"[FAIL] Step 1: register_user — {e}")
        return None, False


def test_step_2_login():
    """Step 2: Login user."""
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }
    try:
        response = httpx.post(
            f"{API_BASE_URL}/login_user",
            json=payload,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print(f"[PASS] Step 2: login_user — token received")
            return token, True
        else:
            print(f"[FAIL] Step 2: login_user — status {response.status_code}: {response.text}")
            return None, False
    except Exception as e:
        print(f"[FAIL] Step 2: login_user — {e}")
        return None, False


def test_step_3_analyze_workout():
    """Step 3: Analyze workout."""
    try:
        workout_session = load_fixture(WORKOUT_SESSION_PATH)
        user_profile = load_fixture(USER_PROFILE_PATH)
        payload = {
            "workout": workout_session,
            "user_profile": user_profile,
        }
        response = httpx.post(
            f"{API_BASE_URL}/analyze_workout",
            json=payload,
            timeout=30.0,
        )
        if response.status_code == 200:
            print(f"[PASS] Step 3: analyze_workout — status 200")
            return True
        else:
            print(f"[FAIL] Step 3: analyze_workout — status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Step 3: analyze_workout — {e}")
        return False


def test_step_4_chat_completions():
    """Step 4: Generate gym chat completions."""
    try:
        user_profile = load_fixture(USER_PROFILE_PATH)
        payload = {
            "messages": [{"role": "user", "content": "What should I eat after leg day?"}],
            "user_profile": user_profile,
        }
        response = httpx.post(
            f"{API_BASE_URL}/generate_gym_chat_completions",
            json=payload,
            timeout=30.0,
        )
        if response.status_code == 200:
            print(f"[PASS] Step 4: generate_gym_chat_completions — status 200")
            return True
        else:
            print(f"[FAIL] Step 4: generate_gym_chat_completions — status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Step 4: generate_gym_chat_completions — {e}")
        return False


def cleanup_db(user_id):
    """Step 5: Clean up test data from database."""
    if user_id is None:
        print(f"[SKIP] Step 5: cleanup — no user_id to clean")
        return True

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        cursor = conn.cursor()

        # Delete in order (handle missing tables gracefully)
        delete_statements = [
            ("DELETE FROM workout_exercises WHERE session_id IN (SELECT id FROM workout_sessions WHERE user_id = %s)", user_id),
            ("DELETE FROM workout_sessions WHERE user_id = %s", user_id),
            ("DELETE FROM chat_messages WHERE user_id = %s", user_id),
            ("DELETE FROM gym_profiles WHERE user_id = %s", user_id),
            ("DELETE FROM user_profiles WHERE user_id = %s", user_id),
            ("DELETE FROM users WHERE id = %s", user_id),
        ]

        for stmt, param in delete_statements:
            try:
                cursor.execute(stmt, (param,))
            except mysql.connector.Error:
                # Table might not exist; continue
                pass

        conn.commit()
        cursor.close()
        conn.close()

        print(f"[PASS] Step 5: cleanup — user {user_id} deleted")
        return True
    except Exception as e:
        print(f"[FAIL] Step 5: cleanup — {e}")
        return False


def main():
    """Run all test steps."""
    print("Starting gym-jams end-to-end test...\n")

    # Step 1: Register
    user_id, step1_passed = test_step_1_register()

    # Step 2: Login
    token, step2_passed = test_step_2_login()

    # Step 3: Analyze workout
    step3_passed = test_step_3_analyze_workout()

    # Step 4: Chat completions
    step4_passed = test_step_4_chat_completions()

    # Step 5: Cleanup
    step5_passed = cleanup_db(user_id)

    # Summary
    passed = sum([step1_passed, step2_passed, step3_passed, step4_passed, step5_passed])
    total = 5
    print(f"\nResults: {passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
