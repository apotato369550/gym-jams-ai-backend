"""
Initialize MySQL tables for gym-jams-ai-backend.

Drops and recreates all 8 tables from scratch.
Safe to re-run.

Usage:
    python scripts/utils/initialize_sql_tables.py
"""

import sys
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv
import os


def main():
    # Load .env from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Extract DB connection vars
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    connection = None
    cursor = None

    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
        )

        cursor = connection.cursor()

        # Disable foreign key checks for cleanup
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Drop tables in reverse FK dependency order
        tables_to_drop = [
            "chat_messages",
            "workout_history_summaries",
            "workout_analysis_results",
            "workout_exercises",
            "workout_sessions",
            "gym_profiles",
            "user_profiles",
            "users",
        ]

        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"[OK] Dropped: {table}")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        # Create tables in FK dependency order
        cursor.execute("""
            CREATE TABLE users (
                id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                name          VARCHAR(100)    NOT NULL,
                email         VARCHAR(255)    NOT NULL,
                password_hash VARCHAR(255)    NOT NULL,
                created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_users_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: users")

        cursor.execute("""
            CREATE TABLE user_profiles (
                id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                user_id         INT UNSIGNED    NOT NULL,
                name            VARCHAR(100)    NOT NULL,
                age_range       VARCHAR(20)     NOT NULL,
                height_cm       DECIMAL(6,2)    NOT NULL,
                weight_kg       DECIMAL(6,2)    NOT NULL,
                location        VARCHAR(255)    NOT NULL,
                activity_level  VARCHAR(50)     NOT NULL,
                goal            VARCHAR(100)    NOT NULL,
                intent          TEXT            NOT NULL,
                constraints     JSON            NOT NULL,
                created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_user_profiles_user_id (user_id),
                CONSTRAINT fk_user_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: user_profiles")

        cursor.execute("""
            CREATE TABLE gym_profiles (
                id                      INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                user_id                 INT UNSIGNED    NOT NULL,
                archetype               VARCHAR(255)    NOT NULL,
                read_description        TEXT            NOT NULL,
                modalities_youll_enjoy  JSON            NOT NULL,
                first_week_suggestion   TEXT            NOT NULL,
                watch_out_for           TEXT            NOT NULL,
                created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_gym_profiles_user_id (user_id),
                CONSTRAINT fk_gym_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: gym_profiles")

        cursor.execute("""
            CREATE TABLE workout_sessions (
                id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                user_id     INT UNSIGNED    NOT NULL,
                date        DATE            NOT NULL,
                notes       TEXT            NULL,
                created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                KEY idx_workout_sessions_user_id (user_id),
                CONSTRAINT fk_workout_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: workout_sessions")

        cursor.execute("""
            CREATE TABLE workout_exercises (
                id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                session_id      INT UNSIGNED    NOT NULL,
                name            VARCHAR(255)    NOT NULL,
                sets            SMALLINT UNSIGNED NULL,
                reps            SMALLINT UNSIGNED NULL,
                weight_kg       DECIMAL(6,2)    NULL,
                duration_mins   DECIMAL(6,2)    NULL,
                PRIMARY KEY (id),
                KEY idx_workout_exercises_session_id (session_id),
                CONSTRAINT fk_workout_exercises_session FOREIGN KEY (session_id) REFERENCES workout_sessions (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: workout_exercises")

        cursor.execute("""
            CREATE TABLE workout_analysis_results (
                id                        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
                session_id                INT UNSIGNED    NOT NULL,
                total_volume_kg           DECIMAL(10,2)   NULL,
                total_reps                INT UNSIGNED    NULL,
                muscle_groups_targeted    JSON            NOT NULL,
                estimated_calories_burned SMALLINT UNSIGNED NULL,
                intensity_rating          TINYINT UNSIGNED NULL,
                observation               TEXT            NULL,
                created_at                DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_workout_analysis_session_id (session_id),
                CONSTRAINT fk_workout_analysis_session FOREIGN KEY (session_id) REFERENCES workout_sessions (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: workout_analysis_results")

        cursor.execute("""
            CREATE TABLE workout_history_summaries (
                id                      INT UNSIGNED                    NOT NULL AUTO_INCREMENT,
                user_id                 INT UNSIGNED                    NOT NULL,
                range_period            ENUM('week','month','3months')  NOT NULL,
                consistency_score       DECIMAL(4,2)                    NULL,
                consistency_note        TEXT                            NULL,
                top_exercises           JSON                            NOT NULL,
                volume_trend            VARCHAR(100)                    NULL,
                volume_note             TEXT                            NULL,
                plateaus_detected       TEXT                            NULL,
                trajectory_suggestion   TEXT                            NULL,
                thing_youre_doing_well  TEXT                            NULL,
                created_at              DATETIME                        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                KEY idx_workout_history_user_id (user_id),
                CONSTRAINT fk_workout_history_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: workout_history_summaries")

        cursor.execute("""
            CREATE TABLE chat_messages (
                id          INT UNSIGNED                NOT NULL AUTO_INCREMENT,
                user_id     INT UNSIGNED                NOT NULL,
                role        ENUM('user','assistant')    NOT NULL,
                content     TEXT                        NOT NULL,
                image_url   VARCHAR(500)                NULL,
                created_at  DATETIME                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at  DATETIME                    NULL,
                PRIMARY KEY (id),
                KEY idx_chat_messages_user_id (user_id),
                KEY idx_chat_messages_deleted_at (deleted_at),
                CONSTRAINT fk_chat_messages_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Created: chat_messages")

        # Commit all changes
        connection.commit()
        print("\n[OK] All tables initialized successfully.")

    except mysql.connector.Error as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        if connection:
            connection.rollback()
        sys.exit(1)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
