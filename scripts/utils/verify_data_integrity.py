#!/usr/bin/env python3
"""Data integrity checker for gym-jams MySQL database."""

import sys
import os
from pathlib import Path
from datetime import datetime

import mysql.connector
from mysql.connector import errors
from dotenv import load_dotenv


def load_env_vars():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }


def connect_db(config):
    """Establish MySQL connection."""
    return mysql.connector.connect(**config)


def run_orphan_checks(cursor, checks):
    """Run all orphan detection queries."""
    results = []

    for table_name, query in checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "OK" if count == 0 else "WARN"
            results.append((table_name, count, status))
        except errors.ProgrammingError:
            results.append((table_name, "TABLE_MISSING", "SKIP"))

    return results


def format_table(results):
    """Format results as aligned ASCII table."""
    lines = []

    # Header
    lines.append("Data Integrity Check — {} {:%H:%M:%S}".format(
        datetime.now().strftime("%Y-%m-%d"),
        datetime.now()
    ))

    # Column widths
    col_table = 28
    col_orphaned = 13
    col_status = 6

    # Separator
    sep = "+" + "-" * (col_table + 2) + "+" + "-" * (col_orphaned + 2) + "+" + "-" * (col_status + 2) + "+"
    lines.append(sep)

    # Header row
    header = "| " + "Table".ljust(col_table) + " | " + "Orphaned Rows".ljust(col_orphaned) + " | " + "Status".ljust(col_status) + " |"
    lines.append(header)
    lines.append(sep)

    # Data rows
    for table_name, count, status in results:
        count_str = str(count)
        row = "| " + table_name.ljust(col_table) + " | " + count_str.ljust(col_orphaned) + " | " + status.ljust(col_status) + " |"
        lines.append(row)

    lines.append(sep)

    # Summary
    ok_count = sum(1 for _, _, s in results if s == "OK")
    warn_count = sum(1 for _, _, s in results if s == "WARN")
    skip_count = sum(1 for _, _, s in results if s == "SKIP")
    summary = f"Summary: {ok_count} OK, {warn_count} WARN, {skip_count} SKIP"
    lines.append(summary)

    return "\n".join(lines), warn_count


def main():
    """Main entry point."""
    try:
        config = load_env_vars()
    except Exception as e:
        print(f"Error loading environment variables: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = connect_db(config)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    checks = [
        ("workout_sessions", "SELECT COUNT(*) FROM workout_sessions ws WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = ws.user_id)"),
        ("workout_exercises", "SELECT COUNT(*) FROM workout_exercises we WHERE NOT EXISTS (SELECT 1 FROM workout_sessions ws WHERE ws.id = we.session_id)"),
        ("chat_messages", "SELECT COUNT(*) FROM chat_messages cm WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = cm.user_id)"),
        ("gym_profiles", "SELECT COUNT(*) FROM gym_profiles gp WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = gp.user_id)"),
        ("user_profiles", "SELECT COUNT(*) FROM user_profiles up WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = up.user_id)"),
        ("workout_analysis_results", "SELECT COUNT(*) FROM workout_analysis_results war WHERE NOT EXISTS (SELECT 1 FROM workout_sessions ws WHERE ws.id = war.session_id)"),
    ]

    try:
        results = run_orphan_checks(cursor, checks)
    except Exception as e:
        print(f"Error running orphan checks: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    output, warn_count = format_table(results)
    print(output)

    sys.exit(1 if warn_count > 0 else 0)


if __name__ == "__main__":
    main()
