# Gym Jams AI Backend

FastAPI backend for Gym Jams. Handles AI inference via OpenRouter, JWT auth, and MySQL persistence.

## Documentation

- 📘 **[API Usage Guide](docs/API_USAGE.md)** — undergrad-friendly walkthrough of every endpoint with curl + Postman examples. Start here if you've never hit a REST API before.
- 🚀 **[Deployment Quickstart](docs/DEPLOYMENT.md)** — one-shot EC2 deploy via `deploy/deploy.sh`, day-2 ops, troubleshooting.
- 📮 **[Postman Collection](docs/postman_collection.json)** — import into Postman; auto-saves your JWT after login.
- 🛠️ **[CLAUDE.md](CLAUDE.md)** — architecture notes, request flow, conventions for contributors and AI assistants.

## Quickstart

**Local development:** see [Setup](#setup) below.

**Deploy to EC2:** ([full guide](docs/DEPLOYMENT.md))
```bash
EC2_HOST=ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com \
PEM_PATH=./your-key.pem \
bash deploy/deploy.sh
```

**Hit the API:** ([full guide](docs/API_USAGE.md))
```bash
# Register, login, save the token, then call any AI endpoint with `Authorization: Bearer <token>`
curl -X POST http://YOUR-HOST/register_user -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"supersecret123","name":"Alice"}'
```

---

## Project Structure

```
gym-jams-ai-backend/
├── app/
│   ├── main.py                  # entrypoint, auth endpoints (/register_user, /login_user)
│   ├── core/config.py           # DB_URL construction from env
│   ├── db/
│   │   ├── session.py           # async SQLAlchemy engine + get_db()
│   │   └── models.py            # 8 ORM models (User, UserProfile, GymProfile, WorkoutSession, WorkoutExercise, WorkoutAnalysisResult, WorkoutHistorySummary, ChatMessage)
│   ├── routes/
│   │   ├── analyze_workout.py
│   │   ├── analyze_workout_history.py
│   │   ├── generate_gym_profile.py
│   │   ├── generate_gym_chat_completions.py
│   │   ├── chat.py
│   │   ├── user_profile.py
│   │   ├── gym_profile.py                    # GET only
│   │   ├── workout_sessions.py               # GET list + detail
│   │   ├── workout_history_summaries.py      # GET latest
│   │   └── chat_messages.py                  # GET (with 24h soft-delete reset)
│   ├── schemas/
│   │   ├── workout.py
│   │   ├── user_profile.py
│   │   └── chat.py
│   └── services/
│       ├── llm.py               # call_llm, extract_json_content, extract_text_content, build_response
│       └── chat_persistence.py  # save_turn + 24h soft-delete (expire_old_messages)
├── data/
│   ├── mock/                    # static mock responses (4 files, one per AI endpoint)
│   ├── sample_workout_data/
│   ├── sample_workout_history_data/
│   └── user_profile.json
├── scripts/
│   ├── testing/                 # per-endpoint test scripts (support --test and --debug flags)
│   │   ├── test_analyze_workout.py
│   │   ├── test_analyze_workout_history.py
│   │   ├── test_generate_gym_profile.py
│   │   └── test_generate_gym_chat_completions.py
│   └── utils/
│       ├── initialize_sql_tables.py   # drops and recreates all 8 tables
│       ├── seed_sql_tables.py         # seeds 3 test personas (Maria, Jake, Ana)
│       ├── test_users.py              # end-to-end auth test (register → login → cleanup)
│       └── verify_data_integrity.py   # checks for orphaned rows
├── results/                     # saved test outputs (gitignored)
├── prompts/                     # LLM system prompts
├── deploy/                      # EC2 deploy macro (deploy.sh) + nginx/systemd templates
├── docs/                        # API usage guide, deployment quickstart, Postman collection
├── requirements.txt
├── .env
└── README.md
```

---

## Setup

### 1. Clone and create venv

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. Configure .env

Create `.env` at project root with:

```
APP_ENV=dev
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=meta-llama/llama-3-8b-instruct
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gym_jams_db
JWT_SECRET=your_random_secret_string
```

Note: use `127.0.0.1` not `localhost` — Docker binds TCP, not Unix socket.

### 3. Start the MySQL database (Docker)

Docker packages MySQL into a container, isolated and easy to start/stop.

Pull the MySQL image:

```bash
docker pull mysql:8.0
```

Start the container:

```bash
docker run -d \
  --name gym-jams-db \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=gym_jams_db \
  -p 3306:3306 \
  mysql:8.0
```

Wait about 15 seconds for MySQL to initialize, then verify:

```bash
docker ps   # should show gym-jams-db running with 0.0.0.0:3306->3306/tcp
```

If you get a permission denied error on docker:

```bash
sudo usermod -aG docker $USER
# then log out and back in, or run: newgrp docker
```

### 4. Connect to MySQL from the command line (optional)

Once the container is running, you can inspect the database directly:

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p
# Enter your password when prompted
```

Useful commands once inside the MySQL shell:

```sql
SHOW DATABASES;              -- list all databases
USE gym_jams_db;             -- switch to the project database
SHOW TABLES;                 -- list all tables
DESCRIBE users;              -- show columns for a table
SELECT * FROM users;         -- view all rows in a table
EXIT;                        -- quit the shell
```

---

### 5. Initialize database tables

```bash
python scripts/utils/initialize_sql_tables.py
```

Safe to re-run — drops and recreates all tables.

### 6. (Optional) Seed sample data

```bash
python scripts/utils/seed_sql_tables.py
```

Inserts 3 test personas: Maria Santos (beginner), Jake Reyes (bulker), Ana Cruz (endurance runner).

### 7. Run the server

```bash
uvicorn app.main:app --reload
```

Docs: http://127.0.0.1:8000/docs

---

## API Endpoints

- **GET** `/` — health check
- **GET** `/health` — service alive
- **POST** `/register_user` — register with email/password/name
- **POST** `/login_user` — returns JWT token
- **POST** `/user_profile` / **GET** `/user_profile` — save/fetch your profile
- **POST** `/analyze_workout` — AI workout analysis (persists session + exercises + analysis)
- **POST** `/generate_gym_profile` — AI gym persona profile (upserts your gym profile)
- **POST** `/analyze_workout_history` — AI history trends (persists summary)
- **POST** `/generate_gym_chat_completions` — AI chat (persists turns; 24h auto-reset)
- **POST** `/chat` — lightweight Coach J chat (persists turns; 24h auto-reset)
- **GET** `/gym_profile` — fetch latest generated archetype
- **GET** `/workout_sessions` / **GET** `/workout_sessions/{id}` — list / detail
- **GET** `/workout_history_summaries?range=week|month|3months` — latest summary
- **GET** `/chat_messages` — paginated chat history (auto-resets every 24h via soft-delete)

All AI endpoints require `Authorization: Bearer <token>` (obtained from `/login_user`) and accept `test: bool` (mock mode — no LLM credits AND no DB writes) and `debug: bool` (returns raw + formatted).

**Data lifecycle.** Register → POST `/user_profile` → POST any AI endpoint (results saved automatically) → later, GET to read history. The `test=true` flag bypasses both the LLM and DB writes, so you can experiment freely without polluting your data.

Full request/response examples and Postman steps in **[docs/API_USAGE.md](docs/API_USAGE.md)**.

---

## Testing

### End-to-end auth test

```bash
python scripts/utils/test_users.py
```

### AI endpoint tests (no credits with --test)

```bash
python scripts/testing/test_analyze_workout.py --test
python scripts/testing/test_generate_gym_profile.py --test
python scripts/testing/test_analyze_workout_history.py --test
python scripts/testing/test_generate_gym_chat_completions.py --test

# Add --debug to see raw + formatted output side by side
python scripts/testing/test_analyze_workout.py --test --debug
```

### Data integrity check

```bash
python scripts/utils/verify_data_integrity.py
```

---

## Notes

- `.env` is gitignored — never commit credentials
- `results/` stores test outputs locally
- No migration tooling — schema changes require re-running `initialize_sql_tables.py`
