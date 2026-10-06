# GChess

GChess is a Django chess web app built as a portfolio project. It supports local accounts, online games, invitations, ratings, chat, clocks, PGN analysis, and play against a Stockfish-powered bot.

## Features

- User registration, login, and player profiles.
- Online chess games between registered users.
- Direct, random, and shareable-link invitations.
- Server-side move validation with `python-chess`.
- Elo updates for finished multiplayer games.
- Draw offers, resignation, clocks, and timeout handling.
- In-game chat with unread counters.
- PGN/internal move analyzer with Stockfish feedback.
- Bot games with configurable Elo levels.
- Trainer chat and coach comments for played moves.

## Tech Stack

- Python 3
- Django 6
- SQLite for local development
- PostgreSQL for production through `DATABASE_URL`
- python-chess / chess
- Stockfish
- WhiteNoise for static files
- Gunicorn for production serving
- Render for deployment

## Screenshots

Add screenshots here before publishing the portfolio page:

- Home / dashboard
- Game board
- Invitation flow
- PGN analyzer
- Bot or trainer view

## Local Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` file from the example:

```bash
copy .env.example .env
```

Set at least:

```env
DJANGO_SECRET_KEY=your-local-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
DJANGO_SECURE_SSL_REDIRECT=False
STOCKFISH_PATH=C:\Users\lucas\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe
EMAIL_BACKEND=
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=GChess <noreply@example.com>
```

Run migrations and start the app:

```bash
python manage.py migrate
python manage.py runserver
```

Run checks and tests:

```bash
python manage.py check
python manage.py test
```

## Environment Variables

- `DJANGO_SECRET_KEY`: required. Use a long random value in production.
- `DJANGO_DEBUG`: `False` in production.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts, for example `gchess.onrender.com`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS origins, for example `https://gchess.onrender.com`.
- `DATABASE_URL`: PostgreSQL URL in production. If empty, local SQLite is used.
- `REDIS_URL`: Redis URL for the Django Channels channel layer in production.
- `STOCKFISH_PATH`: path to the Stockfish executable.
- `EMAIL_BACKEND`: optional email backend override. Leave empty to use SMTP when `EMAIL_HOST` is set, or console email when it is not.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: SMTP server settings for password recovery emails.
- `EMAIL_USE_TLS`, `EMAIL_USE_SSL`: SMTP security settings.
- `DEFAULT_FROM_EMAIL`: sender address used by password recovery emails.
- `DJANGO_SECURE_SSL_REDIRECT`: use `True` in production on Render.
- `DJANGO_SECURE_HSTS_SECONDS`: optional, defaults to `31536000` when `DEBUG=False`.

## Stockfish

Local development:

1. Download Stockfish for your OS.
2. Put the executable somewhere stable.
3. Set `STOCKFISH_PATH` in `.env`.

Render:

- `build.sh` tries to install Stockfish with `apt-get`.
- Set `STOCKFISH_PATH=/usr/games/stockfish` in Render when using the apt package.
- If Stockfish is not installed or the path is wrong, bot/analysis endpoints return a clear JSON error instead of crashing the app.
- If Render cannot install the package, deploy still continues; engine features stay unavailable until `STOCKFISH_PATH` points to a real binary.

## Deploy on Render

Create a Render Web Service connected to this repository.

Build command:

```bash
bash build.sh
```

Start command:

```bash
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

The included `Procfile` also defines:

```bash
web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

Recommended Render environment variables:

```env
DJANGO_SECRET_KEY=your-production-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-service-name.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service-name.onrender.com
DATABASE_URL=postgres://...
REDIS_URL=redis://...
DJANGO_SECURE_SSL_REDIRECT=True
STOCKFISH_PATH=/usr/games/stockfish
```

`build.sh` runs:

```bash
apt-get update
apt-get install -y stockfish
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

## Project Status

Portfolio-ready production preparation is in progress. The core game logic is preserved, and recent hardening focuses on deployment configuration, server-side validation, invitation safety, and regression tests.

## Next Improvements

- Add polished screenshots and a short demo video.
- Add persistent background job support if analysis grows slower.
- Improve real-time multiplayer with WebSockets.
- Add more chess rule regression tests.
- Package Stockfish installation more cleanly for production.
- Add CI for `manage.py check` and `manage.py test`.


## Trainer reliability (stage 1)

The chat sends the selected move prefix, player color and at most six recent
conversation messages (1600 characters each). History is browser-local and is
untrusted context; the current reconstructed board always wins. The server
reconstructs from the standard starting position, validates each move, and runs
Stockfish before asking Gemini. Custom PGN starting FENs are not supported by
this chat endpoint yet. Do not use this endpoint to coach a custom starting FEN.

`TRAINER_ANALYSIS_SECONDS=0.12` controls each search, clamped to 0.05-1.0 seconds.
One thread is used. A proposed legal move requires a second search. Fallback
reuses the analysis; the engine exits before the Gemini network request.
Four simultaneous position requests therefore budget about 0.48 CPU seconds
at the default, or 0.96 when all ask about a legal proposed move, plus process
startup/overhead. This is a budget estimate, not a hosting load measurement.
No engine pool or global concurrency queue is introduced in this stage.

Measure on the actual hosting CPU before raising the budget:

```sh
python manage.py trainer_benchmark --runs 3
```

The command prints installed UCI engine identity, elapsed time, depth, nodes,
best move and evaluation for two opening positions with a cold 16 MB hash,
one thread, three candidate lines and budgets 0.05/0.12/0.30/0.60 seconds.
Local Stockfish 19 measurements (6 samples per budget) were:

| Budget | Observed time | Depth range |
| --- | --- | --- |
| 0.05 s | 58-73 ms | 9-11 |
| 0.12 s | 129-135 ms | 11-13 |
| 0.30 s | 308-309 ms | 14-15 |
| 0.60 s | 608-610 ms | 15-17 |

Longer searches reached greater depth and changed some recommendations;
they do not prove tactical accuracy. 0.30 seconds costs about 2.5 times the
search CPU budget of 0.12. Keep the default until representative middlegame
and simultaneous-request tests on hosting justify changing it.
The official current release is Stockfish 19 (2026-10-06 check):
https://stockfishchess.org/download/
The apt package in `build.sh` is distribution-dependent, so this repository
cannot certify the deployed version. Run the command on hosting; if outdated,
install an official compatible binary and set `STOCKFISH_PATH`.

Gemini remains configurable using `GEMINI_MODEL`, `GEMINI_ENABLED`,
`GEMINI_API_KEY`, `GEMINI_TIMEOUT_SECONDS` (1-20, default 15),
`GEMINI_MAX_OUTPUT_TOKENS`, `GEMINI_CACHE_SECONDS`, and `GEMINI_TEMPERATURE`.
The existing default `gemini-2.5-flash-lite` is still listed, but Google restricts
2.5 model access to projects that used them previously. For a new project,
Google currently recommends 3.5 Flash-Lite or 3.8 Flash. Verify access and cost
for your project before changing the environment value:
https://ai.google.dev/gemini-api/docs/deprecations
No real billable Gemini request was made during this change.

The response includes `source`, `status`, `fen` and `answer`. Provider quota,
timeout, network, model access, empty and invalid responses produce a labelled
Stockfish fallback. HTTP chat failures and browser timeout are shown separately. The conversational upgrade below supersedes the automatic fallback behavior described in this stage.
Logs record provider failure category/model, never request text, API keys or
provider error bodies. SAN/UCI references outside supplied facts are rejected,
but this syntactic check cannot validate every natural-language tactical claim.

Manual checks: open the trainer, select black, move or navigate to a position,
ask for the recommendation, then ask a follow-up. Change position while waiting
and check the position notice. Set `GEMINI_ENABLED=False` for a labelled fallback.
Test a narrow phone viewport, long messages, Enter submission and failed network.
The browser gives up after 30 seconds; provider socket timeout defaults to 8.

Run isolated tests without touching the configured external test database:

```sh
python manage.py test games --settings=config.test_settings --noinput
```


## Conversational trainer

The configured local model remains `gemini-2.5-flash-lite`, with an 8 second
provider socket timeout. `GEMINI_MODEL` and `GEMINI_TIMEOUT_SECONDS` still control
these settings. No model migration, timeout increase, paid call or billing
change was made. Official models/pricing checked on 2026-10-06:
https://ai.google.dev/gemini-api/docs/models
https://ai.google.dev/gemini-api/docs/pricing
The 2.5 family has restricted legacy-project access. 3.5 Flash-Lite and
3.8 Flash are current options for new projects; upgrading requires verifying
project access and cost. No live news/search grounding is enabled.

The chat now answers general questions without requiring Stockfish. A small
multilingual router recognizes chess terms and move notation; unknown topics
are left to Gemini. Short follow-ups inherit the last user topic. Ambiguous
phrasing can be misclassified; naming the move or saying "in this position"
helps. Six recent messages are sent, with their position FEN. The browser keeps
a compact UCI move prefix for each successful exchange and supplies the earlier
prefix on follow-ups. The server reconstructs and reanalyzes that position.
Retry sends the exact original request, even if the board has since changed.
This is browser-local context, not an account-wide conversation store.

Questions about a named move among the last 16 played plies compare its actual
before/after positions, evaluation for the mover, best alternative and material.
This requires up to three short searches (approximately 0.36 seconds of search
budget at the 0.12 default). Searches remain estimates. Unknown historical
moves must not be explained as if verified. Current move recommendations still
use the real board and selected player color.

A provider failure returns `answer: null`, `source: unavailable`, its category,
`retryable: true`, and optional `engine_analysis`. Engine facts are separate from
the conversational answer and are offered only for a concrete chess question
where they help. General questions and failed explanatory follow-ups receive no
unrelated best-move recommendation. The input stays intact and the failure has
a retry button. Failed messages/engine notices are excluded from Gemini history.
Gemini can still fail with timeout, quota, network, restricted model access,
provider error, empty response or invalid/blocked/truncated content.

`games.gemini_service` logs category/model and elapsed milliseconds for success,
cache hits and failures. `games.trainer` logs overall category/topic/duration.
Neither records prompts, conversation text, answers, provider bodies or keys.
The context is sent to Gemini to answer, but not written to server logs.

Manual checks (restart Django and hard-refresh first):
- Play e4, ask "e4 fue buena?", then "Por que?". Move to a newer position and
  follow up again; the answer should refer to the original queried position.
- Ask about stars in space, then "Por que?". This should stay on that topic.
- Ask what NASA announced today. Gemini must say it cannot verify live news.
- Temporarily set `GEMINI_ENABLED=False` and restart: the question stays in the
  input and Retry appears. A general question has no engine recommendation.
  Restore the setting and restart; Retry retains the original position.

Automated provider failures use mocks; no quota-consuming calls are needed:
```sh
python manage.py test games --settings=config.test_settings --noinput
node scripts/test_trainer_client.cjs
```
The JavaScript test checks preserved input, exact retry payload, earlier-position
references and separation of engine facts. It uses a minimal DOM simulation,
not visual browser rendering. Prompt tests cannot prove every Gemini answer;
move-reference validation remains syntactic, not a proof of tactical prose.

Trainer reliability: Gemini uses a 15-second socket timeout by default and retries one transient timeout, connection failure, or HTTP 500/502/503/504 within a shared 25-second provider budget. Authentication, model and quota failures are not retried. The browser allows 45 seconds and shows a waiting notice after 4 seconds. Recent conversation includes up to 12 messages with their position metadata; retries preserve the original board. Explicit GEMINI_TIMEOUT_SECONDS environment settings override the default.

## Persistent storage and recovery

See [the migration and recovery runbook](docs/operacion-datos.md) before deploying or changing DATABASE_URL. Save the live SQLite data outside Render first. Production storage checks, /healthz/, export_data and restore_data are available; provisioning, migration and automated remote backups remain operational steps.
