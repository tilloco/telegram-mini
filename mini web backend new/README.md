# Law Quiz Mini App — Backend

FastAPI backend for the Telegram Mini App version of the law quiz.

## What this does

- Verifies that requests really come from your Telegram Mini App (not someone
  faking it) using the official Telegram `initData` check
- Serves quiz content: Subjects → Modules → Materials (PDFs) and Questions
- Serves PDF study materials so the frontend can display them inline
- Grades quiz answers and tracks per-user progress
- Enforces the same 3-free-questions-per-day limit as the bot

## Running locally

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate          (Windows)
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in `TELEGRAM_BOT_TOKEN` (same token
   your bot uses). Leave `DATABASE_URL` empty to use local SQLite — no
   Postgres install needed for development.

3. Run it:
   ```
   uvicorn app.main:app --reload
   ```

4. Open http://127.0.0.1:8000/docs — this is FastAPI's interactive API
   explorer. You can test every endpoint from there before the frontend exists.

## Important: testing auth locally

The `/auth/telegram` endpoint only accepts *real* `initData` signed by
Telegram, so you can't easily fake a login from the `/docs` page alone.
Once the frontend exists and is opened inside actual Telegram, this will
work automatically — Telegram injects real `initData` into the page.
For now, focus on testing the other endpoints' shapes via `/docs`, and we'll
wire up real auth testing once you open the Mini App in Telegram for the
first time.

## Deploying to Render (same flow as your other projects)

1. Push this folder to a new GitHub repo
2. On Render: New → Web Service → connect the repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a free Postgres database on Render, copy its Internal Connection
   String into this service's `DATABASE_URL` environment variable
6. Add `TELEGRAM_BOT_TOKEN` as an environment variable too
7. Deploy — then visit `https://<your-service>.onrender.com/docs` to confirm
   it's alive

## Known simplification (worth revisiting later)

Progress currently just increments forward. Your planned rule — a free user
who gets cut off mid-module restarts from question 1 next day — isn't
enforced yet. Easy to add once we build the frontend flow and can see exactly
where that reset should trigger.

## Folder structure

```
app/
  main.py          - app entry point, wires everything together
  config.py        - reads settings from environment variables
  database.py      - DB engine/session setup
  dependencies.py  - shared FastAPI dependencies (e.g. get_current_user)
  models/          - SQLAlchemy database table definitions
  schemas/         - Pydantic request/response shapes
  routers/         - the actual API endpoints, grouped by feature
  utils/           - Telegram auth verification, session tokens
```
