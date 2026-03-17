# Gym Jams AI Backend

FastAPI backend service for Gym Jams.
Handles AI inference (via OpenRouter), API routing, and database persistence.

---

## 📦 Project Structure

```
gym-jams-ai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entrypoint
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # env loading + config values
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # SQLAlchemy async engine/session
│   │   └── models.py        # ORM models
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── example.py       # API routes
│   │
│   └── services/
│       ├── __init__.py
│       └── llm.py           # OpenRouter calls
│
├── .env                     # environment variables (NOT committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Create virtual environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Configure environment variables

Create `.env` in root:

```
# ========================
# App
# ========================
APP_ENV=dev

# ========================
# OpenRouter (LLM)
# ========================
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=meta-llama/llama-3-8b-instruct

# ========================
# Database 
# ========================
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=gym_jams

```

---

## 🚀 Run the server

From project root:

```bash
uvicorn app.main:app --reload
```

Docs:

```
http://127.0.0.1:8000/docs
```

---

## 🗄️ Database Notes

### Local Development (recommended)

Run MariaDB locally:

```bash
docker run -d -p 3306:3306 \
-e MYSQL_ROOT_PASSWORD=root \
-e MYSQL_DATABASE=gym_jams \
mariadb:11
```

Used for:

* development
* testing
* migrations

---

### School Database

The DCISM MySQL instance:

* accessible via **phpMyAdmin**
* often **blocked from direct external access**
* typically only reachable internally

Use workflow:

```
local dev → export SQL → import via phpMyAdmin
```

---

## 🧪 Quick Test

```bash
curl -X POST "http://127.0.0.1:8000/chat?prompt=hello"
```

---

## 🔒 Notes

* `.env` is ignored via `.gitignore`
* never commit credentials
* use environment switching for dev/prod

---

## 📌 Future Improvements

* Alembic migrations
* structured logging
* retries + circuit breakers
* streaming responses (LLM)

---
