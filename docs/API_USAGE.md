# API Usage Guide

A friendly walkthrough of the gym-jams API. If you've never used a REST API before, start at the top — this doc assumes nothing.

> Replace `http://YOUR-EC2-HOST` with your real server, e.g. `http://ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com`. For local development, use `http://localhost:8000`.

---

## 0. The 60-second crash course

**REST API.** A REST API is a website that returns data instead of webpages. You "hit" a URL the same way your browser does, but you get back JSON instead of HTML.

**JSON.** A text format for structured data. Looks like `{"key": "value", "list": [1, 2, 3]}`. Think Python dicts, but text.

**HTTP method.** The verb you use:
- `GET` — "give me this"
- `POST` — "here's some data, do something with it"

**Headers.** Extra metadata you send along with a request. Two we use:
- `Content-Type: application/json` — "the body of this request is JSON"
- `Authorization: Bearer <token>` — "I'm logged in, here's my proof"

**Body.** The JSON payload you send with a `POST`.

**Status code.** A number the server returns to tell you what happened:
- `2xx` (200, 201) — success
- `4xx` (400, 401, 409, 422) — your fault (bad input, not logged in, etc.)
- `5xx` (500, 502) — server's fault

**Token (JWT).** A string the server gives you when you log in. Send it back on every protected request via the `Authorization` header. Treat it like a password — don't paste it in screenshots.

**curl.** A command-line tool to make HTTP requests. Works on macOS, Linux, WSL, Git Bash. There's a `curl` and a Postman version of every example below.

---

## 1. The endpoints at a glance

| Method | Path                              | Auth required? | Purpose                                    |
|--------|-----------------------------------|----------------|--------------------------------------------|
| GET    | `/`                               | no             | Sanity check, returns `{"status":"ok"}`    |
| GET    | `/health`                         | no             | Health check                               |
| POST   | `/register_user`                  | no             | Create an account                          |
| POST   | `/login_user`                     | no             | Get a JWT token                            |
| POST   | `/analyze_workout`                | **yes**        | Get AI feedback on a single workout        |
| POST   | `/generate_gym_profile`           | **yes**        | Generate a personality-style gym archetype |
| POST   | `/analyze_workout_history`        | **yes**        | AI summary across multiple workouts        |
| POST   | `/generate_gym_chat_completions`  | **yes**        | Chat with the gym AI (uses your `user_profile` for personalized replies) |
| POST   | `/chat`                           | **yes**        | Lightweight stateless chat with Coach J, the fitness agent (no profile needed) |

All AI endpoints accept two flags in their JSON body:
- `"test": true` → returns mock data instantly, no LLM call (great for trying things out)
- `"debug": true` → returns both the parsed and raw LLM response

---

## 2. Walkthrough — the auth flow

### Step 1: Register

```bash
curl -X POST http://YOUR-EC2-HOST/register_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "supersecret123",
    "name": "Alice"
  }'
```

What each piece does:
- `-X POST` — use the POST method
- `-H "Content-Type: application/json"` — header saying "the body below is JSON"
- `-d '{...}'` — the JSON body

Expected response (`200`):
```json
{"user_id": 1, "email": "alice@example.com"}
```

If the email is taken you get `409`:
```json
{"detail": "Email already registered"}
```

### Step 2: Log in

```bash
curl -X POST http://YOUR-EC2-HOST/login_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "supersecret123"
  }'
```

Expected response:
```json
{
  "user_id": 1,
  "email": "alice@example.com",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Copy the `token`.** You'll send it on every protected call. It's valid for 24 hours.

### Step 3: Hit a protected endpoint

Send the token in the `Authorization` header. Format is exactly: `Authorization: Bearer <token>` (note the space).

```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."   # paste your real token

curl -X POST http://YOUR-EC2-HOST/analyze_workout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "test": true,
    "workout": {
      "date": "2026-04-27",
      "exercises": [
        {"name": "Bench Press", "sets": 3, "reps": 8, "weight_kg": 60}
      ],
      "notes": "felt strong today"
    },
    "user_profile": {
      "name": "Alice",
      "age_range": "19-24",
      "height_cm": 165,
      "weight_kg": 60,
      "location": "Manila",
      "activity_level": "active",
      "goal": "gain_muscle",
      "intent": "build strength",
      "constraints": []
    }
  }'
```

`"test": true` returns mock data, so this works even before the LLM is wired up. Drop it for a real call.

If you forget the `Authorization` header, you get `401`:
```json
{"detail": "Missing or malformed Authorization header. Expected: 'Bearer <token>'"}
```

---

## 3. Reference — every protected endpoint

### `/analyze_workout`

```json
{
  "test": false,
  "debug": false,
  "workout": {
    "date": "2026-04-27",
    "exercises": [{"name": "Squat", "sets": 5, "reps": 5, "weight_kg": 80}],
    "notes": "leg day"
  },
  "user_profile": { ... see below ... }
}
```

### `/generate_gym_profile`

```json
{
  "test": false,
  "debug": false,
  "user_profile": { ... }
}
```

### `/analyze_workout_history`

```json
{
  "test": false,
  "debug": false,
  "history": {
    "range": "week",
    "sessions": [
      {"date": "2026-04-20", "exercises": [...], "notes": null},
      {"date": "2026-04-22", "exercises": [...], "notes": null}
    ]
  },
  "user_profile": { ... }
}
```

### `/chat`

Lightweight conversation with Coach J. You send the full message history each turn — the server is stateless, so the client is responsible for remembering the conversation.

```json
{
  "test": false,
  "debug": false,
  "messages": [
    {"role": "user", "content": "what's a good warmup for leg day?"},
    {"role": "assistant", "content": "Hey! 5 min easy bike, then bodyweight squats..."},
    {"role": "user", "content": "cool, what's a solid first working set?"}
  ]
}
```

Response:
```json
{"message": "For squats, start with 5 reps at about 60% of your top set..."}
```

### `/generate_gym_chat_completions`

```json
{
  "test": false,
  "debug": false,
  "messages": [
    {"role": "user", "content": "what's a good warmup for leg day?"}
  ],
  "user_profile": { ... }
}
```

### The `user_profile` object (used everywhere)

```json
{
  "name": "Alice",
  "age_range": "19-24",
  "height_cm": 165,
  "weight_kg": 60,
  "location": "Manila",
  "activity_level": "active",
  "goal": "gain_muscle",
  "intent": "build strength for volleyball",
  "constraints": ["no squat rack at home"]
}
```

Allowed values:
- `age_range`: `"15-18"`, `"19-24"`, `"25-30"`, `"30+"`
- `activity_level`: `"mostly_inactive"`, `"lightly_active"`, `"active"`, `"very_active"`
- `goal`: `"lose_weight"`, `"gain_muscle"`, `"maintain"`, `"improve_endurance"`, `"just_be_healthier"`

---

## 4. Using Postman (visual alternative to curl)

If you prefer a GUI:

1. **Install Postman**: https://www.postman.com/downloads/
2. **Import the collection**: in Postman, click `Import` → drag in `docs/postman_collection.json` from this repo. You'll see a folder called `gym-jams API`.
3. **Set the `baseUrl` variable**: click the collection name → `Variables` tab → set `baseUrl` to `http://YOUR-EC2-HOST`. Save.
4. **Run "Register"** then **"Login"**. The Login request has a small test script that automatically saves your token into the collection variable `token`. After that, every protected request uses `{{token}}` automatically — you don't have to copy/paste.
5. **Hit any AI endpoint.** Edit the body in the `Body → raw → JSON` tab.

### Postman steps without the collection (manual)

1. New request → method dropdown → `POST` → URL `http://YOUR-EC2-HOST/login_user`
2. **Headers** tab → add `Content-Type: application/json`
3. **Body** tab → `raw` → choose `JSON` from the dropdown → paste your JSON
4. Click `Send`. Copy `token` from the response.
5. New request → `POST http://YOUR-EC2-HOST/analyze_workout`
6. **Headers** tab → add `Content-Type: application/json` AND `Authorization: Bearer <paste-token>`
7. **Body** tab → raw JSON → paste payload → `Send`

---

## 5. Error codes — what they mean and what to do

| Code | Meaning                          | What you probably did wrong                                          |
|------|----------------------------------|----------------------------------------------------------------------|
| 200  | OK                               | Nothing — celebrate                                                  |
| 401  | Unauthorized                     | Forgot the `Authorization` header, token expired (24h), or typo'd it |
| 409  | Conflict                         | Email already registered (during `/register_user`)                   |
| 422  | Unprocessable Entity             | Your JSON body is missing a field or has the wrong type. Read the `detail` — it lists the exact field |
| 500  | Internal Server Error            | Server bug or LLM failure. Check server logs                         |
| 502  | Bad Gateway                      | The FastAPI service is down. SSH in and `sudo systemctl status gym-jams` |

---

## 6. FAQ

**My token stopped working.** It expired (24h). Log in again to get a new one.

**`test: true` works but real calls hang.** The OpenRouter LLM is slow or your `OPENROUTER_API_KEY` is missing/wrong. nginx already waits up to 120s; longer than that = real failure.

**Do I need to be logged in to register?** No. `/register_user` and `/login_user` are public. Only the AI endpoints require a token.

**Can I see all available endpoints in a browser?** Yes — visit `http://YOUR-EC2-HOST/docs` for the auto-generated Swagger UI.
