# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run dev server
uvicorn app.main:app --reload

# Install dependencies
pip install -r requirements.txt

# Spin up local MariaDB (for dev/test)
docker run -d -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=gym_jams \
  mariadb:11

# Quick smoke test
curl -X POST "http://127.0.0.1:8000/chat?prompt=hello"
```

## Architecture

FastAPI backend with async MySQL (via SQLAlchemy + aiomysql) and LLM inference through OpenRouter.

**Request flow:**
- `app/main.py` — entrypoint; registers routers, handles startup (DB table creation via `Base.metadata.create_all`)
- `app/routes/` — API route modules; inject `AsyncSession` via `Depends(get_db)`
- `app/db/session.py` — async engine + `get_db()` dependency
- `app/db/models.py` — SQLAlchemy ORM models using `DeclarativeBase`
- `app/core/config.py` — constructs `DB_URL` from env vars; imported by session

**LLM calls** are made directly in `app/main.py`'s `/chat` endpoint via `httpx` to OpenRouter. Future LLM logic should go in `app/services/llm.py` (noted in README, not yet implemented).

**DB startup behavior:** connection failure is non-fatal — the app logs the error and continues without DB access.

## Environment

`.env` lives at the project root. Required vars:

```
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=meta-llama/llama-3-8b-instruct
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=gym_jams
APP_ENV=dev
```

## Adding Routes

Create a new file in `app/routes/`, define an `APIRouter`, then register it in `app/main.py` with `app.include_router(...)`. Use `get_db` dependency for DB access. Add new ORM models to `app/db/models.py` — they are auto-created on startup (no migration tooling yet).
