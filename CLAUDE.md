# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Two local processes, no Docker (Docker will be reintroduced later):

- **`server-express/`** — Node/Express, the only thing the browser talks to. Serves the static frontend from `server-express/public/` and reverse-proxies everything under `/api/*` to the Flask API (`http-proxy-middleware`, target `http://127.0.0.1:5000` by default, overridable via `API_TARGET` env var).
- **`server-flask/`** — Python/Flask, the API and data layer. Binds to `127.0.0.1` only (not meant to be reached directly by the browser — Express is the front door). Owns SQLite directly.

This split exists specifically so SQLite has a single writer process. Don't add direct SQLite access from the Express side — go through the Flask API instead.

- SQLite file lives at `data/radiocalico.db` (repo root, gitignored, created on first run by `init_db()` in `server-flask/app.py`). Path is overridable via `DB_PATH` env var.
- No migration system — schema changes mean editing the `CREATE TABLE IF NOT EXISTS` statements in `server-flask/app.py` directly.
- `server-flask/app.py` uses Flask's `g` + `teardown_appcontext` for per-request SQLite connections (stdlib `sqlite3`, no ORM) — follow this pattern for new routes that touch the DB.
- API surface is JSON under `/api/*` (currently `/api/health`, `/api/items`). Follow the existing convention: `jsonify` responses, 400 with `{"error": ...}` for validation failures.
- No build step for the frontend — `server-express/public/` is served as-is by Express's static middleware.

## Git workflow

- Never commit or push directly to `main`. `main` only moves via a merge or rebase of a feature branch.
- All feature work happens on a branch named `feature-<featurename>`. Ask the user for the feature name before creating the branch — don't invent one.
- If it's unclear whether a change counts as a new feature (vs. something that belongs on the current branch), ask first rather than assuming.
- Never push without prompting for my permission.
- Always ask if I would like to see the contents of a given commit before a push operation.
- When in doubt, always ask for my feedback before touching anything git related. 

## Commands

**Flask API** (from `server-flask/`):
```
python3 -m venv .venv          # one-time setup
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py        # runs on http://127.0.0.1:5000, debug mode on
```

**Express web server** (from `server-express/`):
```
npm install                    # one-time setup
npm start                      # runs on http://localhost:3000
npm run dev                    # same, with --watch for auto-restart
```

Both must be running for the app to work — start Flask first, then Express (Express proxies to it but doesn't fail hard at startup if it's down; requests will just fail until Flask is up).

No test suite or linter is configured yet.

Manual smoke test (through Express, the real entry point):
```
curl http://localhost:3000/api/health
curl -X POST http://localhost:3000/api/items -H 'Content-Type: application/json' -d '{"name":"foo"}'
curl http://localhost:3000/api/items
```
