#!/usr/bin/env python3
"""
Seed script for dev/test. Inserts 3 test personas into MySQL.
Each persona has a distinct fitness goal, workouts, profiles, and chat history.
"""

import json
from pathlib import Path
from datetime import datetime
import mysql.connector
from passlib.context import CryptContext

# Resolve .env location
ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"])


def load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def seed_database():
    """Seed the database with 3 test personas."""
    env = load_env()

    # Database config
    db_config = {
        "host": env.get("DB_HOST", "localhost"),
        "user": env.get("DB_USER", "root"),
        "password": env.get("DB_PASSWORD", "root"),
        "database": env.get("DB_NAME", "gym_jams"),
    }

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Persona 1: Maria Santos (beginner, no equipment)
        print("\n=== Seeding Persona 1: Maria Santos ===")

        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            ("Maria Santos", "maria@gymjams.test", hash_password("TestPass123!")),
        )
        maria_user_id = cursor.lastrowid
        print(f"[OK] Seeded: User (Maria) — ID {maria_user_id}")

        # Insert user profile
        maria_constraints = [
            "no gym",
            "student budget",
            "busy weekdays",
            "dorm living",
            "limited equipment",
        ]
        cursor.execute(
            """INSERT INTO user_profiles
               (user_id, name, age_range, height_cm, weight_kg, location, activity_level, goal, intent, constraints)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                maria_user_id,
                "Maria Santos",
                "19-24",
                158.00,
                72.00,
                "Quezon City",
                "lightly_active",
                "lose_weight",
                "I want to feel more confident and have energy to get through long study days without feeling sluggish.",
                json.dumps(maria_constraints),
            ),
        )
        print("[OK] Seeded: UserProfile (Maria)")

        # Insert gym profile
        maria_modalities = ["bodyweight exercises", "home workouts", "outdoor activities"]
        cursor.execute(
            """INSERT INTO gym_profiles
               (user_id, archetype, read_description, modalities_youll_enjoy, first_week_suggestion, watch_out_for)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                maria_user_id,
                "The Dorm Dynamo",
                "Maria is a driven college student eager to upgrade her physical game without breaking the bank. Energetic, entrepreneurial, and resourceful.",
                json.dumps(maria_modalities),
                "Dedicate 20 minutes, 3 times a week, to gentle morning exercises like push-ups, squats, and jumping jacks in your dorm room.",
                "Don't get too hard on yourself on busy weekdays. Prioritize sleep over exercise.",
            ),
        )
        print("[OK] Seeded: GymProfile (Maria)")

        # Session 1: Morning session before class
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (maria_user_id, "2026-03-20", "Morning session before class"),
        )
        maria_session1_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Maria Session 1) — ID {maria_session1_id}")

        # Exercises for Maria Session 1
        exercises_maria_s1 = [
            ("Push-ups", 3, 10, None, None),
            ("Bodyweight squats", 3, 15, None, None),
            ("Jumping jacks", None, None, None, 5.0),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_maria_s1:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (maria_session1_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Maria Session 1)")

        # Analysis for Maria Session 1
        maria_s1_muscle_groups = ["chest", "legs", "cardio"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                maria_session1_id,
                None,
                75,
                json.dumps(maria_s1_muscle_groups),
                120,
                3,
                "Solid start for a busy student! Keep the momentum.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Maria Session 1)")

        # Session 2: Evening dorm workout
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (maria_user_id, "2026-03-23", "Evening dorm workout"),
        )
        maria_session2_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Maria Session 2) — ID {maria_session2_id}")

        # Exercises for Maria Session 2
        exercises_maria_s2 = [
            ("Push-ups", 3, 12, None, None),
            ("Bodyweight squats", 3, 20, None, None),
            ("Plank", None, None, None, 1.0),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_maria_s2:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (maria_session2_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Maria Session 2)")

        # Analysis for Maria Session 2
        maria_s2_muscle_groups = ["chest", "core", "legs"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                maria_session2_id,
                None,
                96,
                json.dumps(maria_s2_muscle_groups),
                140,
                4,
                "Progress! More reps than last session.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Maria Session 2)")

        # Chat messages for Maria
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                maria_user_id,
                "user",
                "I only have 15 minutes today, what can I do?",
                None,
            ),
        )
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                maria_user_id,
                "assistant",
                "Try: 30s jumping jacks, 10 squats, 10 push-ups, 30s plank. Repeat twice. Done in 15 minutes!",
                None,
            ),
        )
        print("[OK] Seeded: ChatMessages (Maria)")

        # Persona 2: Jake Reyes (bulker, gym access)
        print("\n=== Seeding Persona 2: Jake Reyes ===")

        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            ("Jake Reyes", "jake@gymjams.test", hash_password("TestPass123!")),
        )
        jake_user_id = cursor.lastrowid
        print(f"[OK] Seeded: User (Jake) — ID {jake_user_id}")

        # Insert user profile
        jake_constraints = ["limited time on weekends"]
        cursor.execute(
            """INSERT INTO user_profiles
               (user_id, name, age_range, height_cm, weight_kg, location, activity_level, goal, intent, constraints)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                jake_user_id,
                "Jake Reyes",
                "19-24",
                175.00,
                68.00,
                "Makati",
                "active",
                "gain_muscle",
                "I want to bulk up and look bigger before summer. I have gym access 4 days a week.",
                json.dumps(jake_constraints),
            ),
        )
        print("[OK] Seeded: UserProfile (Jake)")

        # Insert gym profile
        jake_modalities = ["weight training", "compound lifts", "progressive overload"]
        cursor.execute(
            """INSERT INTO gym_profiles
               (user_id, archetype, read_description, modalities_youll_enjoy, first_week_suggestion, watch_out_for)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                jake_user_id,
                "The Urban Lifter",
                "Jake is a young professional in the making who wants to pack on mass efficiently. Disciplined and goal-oriented.",
                json.dumps(jake_modalities),
                "Start a 4-day upper/lower split. Monday: bench + rows. Tuesday: squat + deadlift. Repeat Thursday/Friday.",
                "Don't skip leg day. Aesthetic gains plateau without lower body strength.",
            ),
        )
        print("[OK] Seeded: GymProfile (Jake)")

        # Session 1: Upper body day A
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (jake_user_id, "2026-03-19", "Upper body day A"),
        )
        jake_session1_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Jake Session 1) — ID {jake_session1_id}")

        # Exercises for Jake Session 1
        exercises_jake_s1 = [
            ("Bench press", 4, 8, 60.00, None),
            ("Dumbbell rows", 4, 10, 20.00, None),
            ("Overhead press", 3, 8, 40.00, None),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_jake_s1:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (jake_session1_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Jake Session 1)")

        # Analysis for Jake Session 1
        jake_s1_muscle_groups = ["chest", "back", "shoulders"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                jake_session1_id,
                2720.00,
                74,
                json.dumps(jake_s1_muscle_groups),
                280,
                7,
                "Strong upper body session. Volume is on track for hypertrophy.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Jake Session 1)")

        # Session 2: Lower body day B
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (jake_user_id, "2026-03-21", "Lower body day B"),
        )
        jake_session2_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Jake Session 2) — ID {jake_session2_id}")

        # Exercises for Jake Session 2
        exercises_jake_s2 = [
            ("Barbell squat", 4, 8, 80.00, None),
            ("Romanian deadlift", 3, 10, 60.00, None),
            ("Leg press", 3, 12, 100.00, None),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_jake_s2:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (jake_session2_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Jake Session 2)")

        # Analysis for Jake Session 2
        jake_s2_muscle_groups = ["quads", "hamstrings", "glutes"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                jake_session2_id,
                5760.00,
                86,
                json.dumps(jake_s2_muscle_groups),
                420,
                8,
                "Great lower body volume. Increase squat by 2.5kg next session.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Jake Session 2)")

        # Chat messages for Jake
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                jake_user_id,
                "user",
                "Should I eat before or after my morning workout?",
                None,
            ),
        )
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                jake_user_id,
                "assistant",
                "For muscle gain, eat before — a light meal with carbs and protein 45-60 mins pre-workout. Post-workout meal within 2 hours is equally important.",
                None,
            ),
        )
        print("[OK] Seeded: ChatMessages (Jake)")

        # Persona 3: Ana Cruz (endurance athlete)
        print("\n=== Seeding Persona 3: Ana Cruz ===")

        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            ("Ana Cruz", "ana@gymjams.test", hash_password("TestPass123!")),
        )
        ana_user_id = cursor.lastrowid
        print(f"[OK] Seeded: User (Ana) — ID {ana_user_id}")

        # Insert user profile
        ana_constraints = ["early morning only", "no heavy lifting", "outdoor preferred"]
        cursor.execute(
            """INSERT INTO user_profiles
               (user_id, name, age_range, height_cm, weight_kg, location, activity_level, goal, intent, constraints)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                ana_user_id,
                "Ana Cruz",
                "25-30",
                163.00,
                58.00,
                "BGC, Taguig",
                "very_active",
                "improve_endurance",
                "Training for a half marathon in June 2026. Need to balance running with strength work.",
                json.dumps(ana_constraints),
            ),
        )
        print("[OK] Seeded: UserProfile (Ana)")

        # Insert gym profile
        ana_modalities = ["running", "cycling", "functional strength"]
        cursor.execute(
            """INSERT INTO gym_profiles
               (user_id, archetype, read_description, modalities_youll_enjoy, first_week_suggestion, watch_out_for)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                ana_user_id,
                "The Road Warrior",
                "Ana is a focused endurance runner building toward a race goal. Structured, data-driven, and consistent.",
                json.dumps(ana_modalities),
                "Run 3x this week: one easy 5k, one tempo 4k, one long 8k. Add one 20-min bodyweight strength session.",
                "Watch your easy pace — most of your runs should feel conversational. Don't race your easy days.",
            ),
        )
        print("[OK] Seeded: GymProfile (Ana)")

        # Session 1: Tempo run
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (ana_user_id, "2026-03-18", "Tempo run"),
        )
        ana_session1_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Ana Session 1) — ID {ana_session1_id}")

        # Exercises for Ana Session 1
        exercises_ana_s1 = [
            ("Tempo run", None, None, None, 28.0),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_ana_s1:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (ana_session1_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Ana Session 1)")

        # Analysis for Ana Session 1
        ana_s1_muscle_groups = ["cardio", "legs"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                ana_session1_id,
                None,
                None,
                json.dumps(ana_s1_muscle_groups),
                310,
                7,
                "Strong tempo. 4k at pace is solid base for half marathon prep.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Ana Session 1)")

        # Session 2: Strength + core
        cursor.execute(
            "INSERT INTO workout_sessions (user_id, date, notes) VALUES (%s, %s, %s)",
            (ana_user_id, "2026-03-22", "Strength + core"),
        )
        ana_session2_id = cursor.lastrowid
        print(f"[OK] Seeded: WorkoutSession (Ana Session 2) — ID {ana_session2_id}")

        # Exercises for Ana Session 2
        exercises_ana_s2 = [
            ("Lunges", 3, 12, None, None),
            ("Plank", None, None, None, 2.0),
            ("Glute bridges", 3, 15, None, None),
        ]
        for name, sets, reps, weight_kg, duration_mins in exercises_ana_s2:
            cursor.execute(
                """INSERT INTO workout_exercises
                   (session_id, name, sets, reps, weight_kg, duration_mins)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (ana_session2_id, name, sets, reps, weight_kg, duration_mins),
            )
        print("[OK] Seeded: WorkoutExercises (Ana Session 2)")

        # Analysis for Ana Session 2
        ana_s2_muscle_groups = ["legs", "core", "glutes"]
        cursor.execute(
            """INSERT INTO workout_analysis_results
               (session_id, total_volume_kg, total_reps, muscle_groups_targeted, estimated_calories_burned, intensity_rating, observation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                ana_session2_id,
                None,
                81,
                json.dumps(ana_s2_muscle_groups),
                160,
                4,
                "Good supplementary work. Core strength will help running economy.",
            ),
        )
        print("[OK] Seeded: WorkoutAnalysisResult (Ana Session 2)")

        # Chat messages for Ana
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                ana_user_id,
                "user",
                "How do I avoid hitting the wall during my long run?",
                None,
            ),
        )
        cursor.execute(
            """INSERT INTO chat_messages (user_id, role, content, image_url)
               VALUES (%s, %s, %s, %s)""",
            (
                ana_user_id,
                "assistant",
                "Fuel every 45 minutes with a gel or banana during runs over 75 minutes. Run your long runs 60-90 seconds per km slower than race pace.",
                None,
            ),
        )
        print("[OK] Seeded: ChatMessages (Ana)")

        # Commit all changes
        conn.commit()
        print("\n=== Database seeding complete! ===\n")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        if conn.is_connected():
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if conn.is_connected():
            conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    seed_database()
