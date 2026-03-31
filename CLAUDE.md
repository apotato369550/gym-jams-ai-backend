# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Commands

```bash
# Run dev server
uvicorn app.main:app --reload

# Install dependencies
pip install -r requirements.txt

# Spin up MySQL via Docker (use 127.0.0.1, not localhost)
docker run -d --name gym-jams-db \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=gym_jams_db \
  -p 3306:3306 \
  mysql:8.0

# Reset DB tables (drop + recreate all 8)
python scripts/utils/initialize_sql_tables.py

# Seed 3 test personas
python scripts/utils/seed_sql_tables.py

# End-to-end auth test
python scripts/utils/test_users.py

# AI endpoint tests (--test = mock, --debug = raw+formatted)
python scripts/testing/test_analyze_workout.py --test --debug
python scripts/testing/test_generate_gym_profile.py --test
python scripts/testing/test_analyze_workout_history.py --test
python scripts/testing/test_generate_gym_chat_completions.py --test

# Verify no orphaned rows
python scripts/utils/verify_data_integrity.py
```

## Architecture

FastAPI backend with async MySQL (SQLAlchemy + aiomysql) and LLM inference via OpenRouter.

**Request flow:**
- `app/main.py` — entrypoint; registers routers; handles startup (`Base.metadata.create_all`); contains `/register_user` and `/login_user` directly (not in routes/)
- `app/routes/` — 4 AI route modules; each uses `call_llm` → `extract_json_content` → `build_response` pipeline
- `app/db/session.py` — async engine + `get_db()` dependency
- `app/db/models.py` — 8 ORM models: `User`, `UserProfile`, `GymProfile`, `WorkoutSession`, `WorkoutExercise`, `WorkoutAnalysisResult`, `WorkoutHistorySummary`, `ChatMessage`
- `app/core/config.py` — constructs `DB_URL` from env vars
- `app/services/llm.py` — `call_llm()` (raw OpenRouter call), `extract_json_content()` (parses LLM JSON from content string, handles markdown fences + fallbacks), `extract_text_content()` (free-text extraction for chat), `build_response()` (wraps formatted/raw based on debug flag)
- `app/schemas/` — Pydantic models: `WorkoutSession`, `WorkoutExercise`, `WorkoutHistory`, `UserProfile`, `ChatMessage`, `ChatRequest` (ChatRequest has `test` and `debug` bool fields)

**AI endpoint pattern (all 4 routes):**
Each request model has `test: bool = False` and `debug: bool = False`.
- `test=True` → load from `data/mock/<endpoint>.json`, return immediately (no OpenRouter call)
- `debug=True` → return `{"formatted": ..., "raw": ...}` instead of just formatted
- Normal → `call_llm` → `extract_json_content` → return structured dict

**Exception: `generate_gym_chat_completions`** — uses `extract_text_content` (not JSON parsing) and returns `{"message": str}`. Its `test`/`debug` fields live on `ChatRequest` in `app/schemas/chat.py`.

**Exception: `generate_gym_profile`** — currently accepts `GenerateGymProfileRequest` (wraps `user_profile: UserProfile` + `test` + `debug`), not a flat `UserProfile` body.

**Auth (in `app/main.py`):**
- `/register_user` — bcrypt hash via `passlib`, inserts `User`, returns `{user_id, email}`, 409 on duplicate email
- `/login_user` — verifies bcrypt, returns `{user_id, email, token}` (JWT HS256, 24h expiry)
- JWT secret from `JWT_SECRET` env var

**DB startup behavior:** connection failure is non-fatal — logs error and continues.

## Environment

`.env` at project root. Required vars:

```
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=meta-llama/llama-3-8b-instruct
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=gym_jams_db
APP_ENV=dev
JWT_SECRET=
```

Note: `DB_HOST=127.0.0.1` required for Docker TCP binding (not `localhost`).

## Scripts

**`scripts/utils/`** — dev/ops utilities, use `mysql-connector-python` directly:
- `initialize_sql_tables.py` — drops all 8 tables (FK checks disabled), recreates in dependency order. Idempotent.
- `seed_sql_tables.py` — inserts 3 personas: Maria Santos (beginner/no-equipment), Jake Reyes (bulker/gym), Ana Cruz (endurance/runner). Passwords bcrypt-hashed.
- `test_users.py` — register → login → analyze_workout → gym_chat → DB cleanup. Reports PASS/FAIL per step.
- `verify_data_integrity.py` — runs orphan queries on 6 tables, prints summary table, exits 1 on WARN.

**`scripts/testing/`** — per-endpoint test scripts. All support `--test` (mock mode) and `--debug` (split output). Results saved to `results/<subdir>/`. Mock runs write to `mock_latest.json`.

## Adding Routes

Create file in `app/routes/`, define `APIRouter`, register in `app/main.py`. For AI routes: add `test: bool = False` and `debug: bool = False` to the request model, add a `MOCK_PATH` constant, follow the `call_llm` → `extract_json_content` → `build_response` pattern. Add mock file to `data/mock/`.

## DB Notes

No migration tooling. Schema changes: update `app/db/models.py` + re-run `initialize_sql_tables.py`. `create_all` on startup only creates missing tables — does not alter existing ones.
