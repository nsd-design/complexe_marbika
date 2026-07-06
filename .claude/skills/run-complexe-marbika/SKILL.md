---
name: run-complexe-marbika
description: Build, run, and drive the Complexe Marbika Django app. Use when asked to start the app, run its server, smoke-test it, log in and hit a page, check the attendance API, or verify a change works in the running app.
---

Complexe Marbika is a server-rendered **Django 5.1** app (salon / restaurant / pool
/ rentals / training back-office) with one DRF API (`pointage` attendance). Most
pages require login. You drive it by launching `runserver` and running the smoke
driver at `.claude/skills/run-complexe-marbika/driver.py`, which logs in through
the real CSRF-protected form and exercises a protected page + the API over HTTP.

All paths below are relative to the repo root (`D:\Projects\Python\complexe_marbika`).
Commands are written for the **Git Bash** shell (the Bash tool); a couple of
Windows-specific equivalents are noted inline.

## Prerequisites

- **Python 3.10** — already provisioned in the repo venv at `.venv/` (`.venv/Scripts/python.exe`, v3.10.9). No global install needed.
- **PostgreSQL** running locally with the database referenced in `.env` (`marbika_db` on `localhost:5432`). The app uses Postgres, not the stray empty `db.sqlite3`.
- **`.env`** present at repo root (it is — git-ignored, not committed). Supplies `SECRET_KEY`, `DEBUG`, `DB_*`, `ALLOWED_HOSTS`, loaded via `python-dotenv`.

Verify the environment is healthy (both should report OK / all-applied):

```bash
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py showmigrations | grep -c '\[X\]'
```

## Setup (one-time)

Dependencies are already installed in `.venv`. If starting from an empty venv:

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe manage.py migrate
```

The driver needs a login user. Create an idempotent smoke user (safe to re-run;
this is a dev DB):

```bash
.venv/Scripts/python.exe manage.py shell -c "
from employe.models import Employe
u,_ = Employe.objects.get_or_create(username='smoke_test', defaults={'first_name':'Smoke','last_name':'Test','telephone':'000','email':'smoke@test.local'})
u.set_password('smokepass123'); u.is_active=True; u.save()
print('smoke_test ready')
"
```

## Run (agent path)

**1. Launch the server in the background** (`--noreload` = single process, clean to kill):

```bash
.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload > "$TEMP/marbika_server.log" 2>&1 &
```

The Python process detaches and keeps serving on `http://127.0.0.1:8000`. Request
logs land in `$TEMP/marbika_server.log`. (When using the Bash tool, launch this
with `run_in_background: true`.)

**2. Drive it with the smoke driver** — it waits for readiness on its own, so no sleep needed:

```bash
.venv/Scripts/python.exe .claude/skills/run-complexe-marbika/driver.py
```

Expected output (exit code `0`; exit `1` if any check fails):

```
-> target: http://127.0.0.1:8000  user: smoke_test
[PASS] root redirects to /login/ when unauthenticated - status=302 location=/login/?next=/
[PASS] login form served with CSRF token - status=200
[PASS] login succeeds (302 away from login) - status=302 location=/
[PASS] authenticated dashboard renders - status=200
[PASS] attendance API rejects unauthenticated (401) - status=401
[PASS] token endpoint returns a token - token acquired
[PASS] attendance API returns JSON with token - status=200
----------------------------------------
RESULT: PASS - all smoke checks green
```

The driver targets `http://127.0.0.1:8000` / user `smoke_test` by default; override
with `--base`, `--user`, `--password` (or env `SMOKE_BASE` / `SMOKE_USER` / `SMOKE_PASS`).

**3. Stop the server** (matches the `runserver` command line; kills the venv launcher and its child interpreter):

```bash
powershell -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*runserver*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
```

### Poke it by hand

The DRF attendance API requires Token auth (`REST_FRAMEWORK` → `IsAuthenticated` +
`TokenAuthentication`). Unauthenticated requests get `401`; obtain a token first:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/attendance/api/v1/attendance/   # -> 401
TOKEN=$(curl -s -H "Content-Type: application/json" \
  -d '{"username":"smoke_test","password":"smokepass123"}' \
  http://127.0.0.1:8000/attendance/api/v1/token/ | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/attendance/api/v1/attendance/   # -> [] (JSON)
```

## Run (human path)

`.venv/Scripts/python.exe manage.py runserver` (no `--noreload`) then open
`http://127.0.0.1:8000/` in a browser and log in. Blocks the terminal; Ctrl-C to
stop. Useless headless — use the agent path above.

## Test

The `pointage` app has a real DRF test suite (`manage.py test pointage --noinput`,
~20 tests covering auth, the anti-duplicate check-in/out rule, and audit fields).
Other apps' `tests.py` are still empty stubs. `--noinput` auto-drops a stale
`test_marbika_db` left by an interrupted run. The driver remains the end-to-end
smoke test against the running server.

## Gotchas

- **`.venv/Scripts/python.exe` spawns a second `python.exe`.** The venv executable is a launcher that re-execs the base interpreter (`C:\Python310\python.exe`); the child is the one holding the server. Killing only the parent orphans it — the Stop-Process one-liner above matches the command line, so it catches both. `Ctrl-C` in the foreground kills the tree fine.
- **Windows console is cp1252.** Non-ASCII in stdout raises `UnicodeEncodeError` (`→` etc.). The driver prints ASCII only; keep it that way if you extend it.
- **Login needs the CSRF *form* token, not just the cookie.** Django checks `csrfmiddlewaretoken` (POST field, scraped from the login page HTML) against the `csrftoken` cookie. The driver does both; a plain `curl -d username=...` without the form token gets the login form re-rendered (200), not a 302.
- **Login "success" is a 302 away from `/login/`.** A wrong password re-renders the form with status **200** — so a 200 on the login POST means failure, not success. The driver asserts `302 && location != /login`.
- **Most views are `@login_required`** and redirect unauthenticated requests to `/login/?next=...` (302). The `pointage` DRF API is **not** open — it requires `Authorization: Token <t>` (401 otherwise); obtain a token via `POST /attendance/api/v1/token/`.

## Troubleshooting

- **`django.db.utils.OperationalError` / connection refused on startup**: PostgreSQL isn't running or `marbika_db` doesn't exist. Start Postgres and confirm the `DB_*` values in `.env`. `manage.py check` passes without a DB, but `showmigrations`/`runserver` requests need it.
- **Driver: `server never became reachable`**: the server didn't start. Read `$TEMP/marbika_server.log` — usually a DB error or port 8000 already in use.
- **Driver: login check FAILs with `status=200`**: the `smoke_test` user is missing or its password drifted. Re-run the Setup shell snippet to reset it.
- **`UnicodeEncodeError` when running your own `manage.py shell -c`**: avoid non-ASCII in printed strings, or set `PYTHONUTF8=1`.
