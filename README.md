# Telegram LLM Bot

[![CI](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml)

Local-first Telegram AI bot for text, voice, tools, web search, and self-hosted storage.

The default release runs `qwen3.5:0.8b` through Ollama, keeps chat history in SQLite, transcribes voice locally with `faster-whisper`, archives voice audio to MinIO, and exposes readiness checks for the services that usually break during local or Docker deployment.

## What It Does

| Area | Default |
| --- | --- |
| Chat provider | Ollama with `qwen3.5:0.8b` |
| Tool calling | Time, calculator, and optional SearchApi web search |
| Voice | Local faster-whisper transcription |
| Storage | SQLite chat history and MinIO voice archive |
| Operations | `/health`, smoke checks, doctor checks, provider probe |
| Deployment | Local Python or Docker Compose |

## Requirements

- Python 3.10 or newer
- Poetry
- Ollama
- Telegram bot token from BotFather
- Docker, if you want Compose-managed MinIO

Pull the default model before starting the bot:

```powershell
ollama pull qwen3.5:0.8b
```

## Quickstart

Install dependencies:

```powershell
poetry install
```

Create starter config files:

```powershell
poetry run telegram-llm-bot-init
```

Set your Telegram token in `bot.env`:

```env
TELEGRAM_BOT_TOKEN=
BOT_NAME=telegram-llm-bot
BOT_CONFIG_FILE=bot.yml
```

Start MinIO for voice audio archive:

```powershell
docker compose up -d minio
```

Check the local setup:

```powershell
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor --live
poetry run telegram-llm-bot-provider-check
```

Run the bot:

```powershell
poetry run telegram-llm-bot
```

Open Telegram and send a message to your bot.

## Configuration

`telegram-llm-bot-init` creates `.env`, `bot.env`, and `bot.yml`.

### Bot Identity

`bot.env` is for Telegram and bot process settings:

```env
TELEGRAM_BOT_TOKEN=
BOT_NAME=telegram-llm-bot
BOT_CONFIG_FILE=bot.yml
```

Do not commit `bot.env`.

### Prompt

`bot.yml` controls the user-facing start message and system prompt:

```yaml
start: Hello. Send me a message and I will reply.
system: |
  You are a concise, practical assistant in a Telegram chat.
  Answer the user's latest message directly first.
  Use short paragraphs or bullets when they make the answer easier to scan.
  Ask one clarifying question only when a correct answer depends on missing information.
  Say when you are uncertain instead of inventing facts.
  Use available tools for arithmetic, dates, times, and current information.
  Keep replies compact unless the user asks for detail.
```

### LLM

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:0.8b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
OLLAMA_TOOLS_ENABLED=true
OLLAMA_THINK=false
OLLAMA_HEALTH_TIMEOUT=5
```

Supported providers:

| Provider | Value | Use |
| --- | --- | --- |
| Ollama | `ollama` | Default local inference |
| Echo | `echo` | Fast smoke tests without model calls |
| Beam | `beam` | Optional remote inference path |

### Search

SearchApi is optional. Without `SEARCHAPI_API_KEY`, the model can still use local tools, but web search returns a configuration error.

```env
SEARCHAPI_API_KEY=
SEARCHAPI_TIMEOUT=20
SEARCHAPI_SAFE=active
SEARCHAPI_HL=en
SEARCHAPI_GL=us
```

### Voice

Voice messages are downloaded from Telegram, optionally archived to MinIO, transcribed locally, then sent through the normal text chat path. MinIO failures are logged and do not block transcription.

```env
LOCAL_TRANSCRIPTION_MODEL=small
LOCAL_TRANSCRIPTION_COMPUTE_TYPE=int8
LOCAL_TRANSCRIPTION_DEVICE=cpu
LOCAL_TRANSCRIPTION_BEAM_SIZE=5
LOCAL_TRANSCRIPTION_CPU_THREADS=4
```

### Storage

SQLite is the default chat history backend:

```env
CHAT_HISTORY_BACKEND=sqlite
SQLITE_HISTORY_PATH=.tmp/chat_history.sqlite3
CHAT_HISTORY_MAX_MESSAGES=20
```

MinIO is used for voice audio archive:

```env
MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=telegram-llm-bot
MINIO_HEALTH_TIMEOUT=5
```

MongoDB remains available for deployments that need it:

```env
CHAT_HISTORY_BACKEND=mongo
MONGO_HOST=localhost
MONGO_PORT=27017
```

## Telegram Commands

| Command | Purpose |
| --- | --- |
| `/help` | Show bot commands |
| `/my_id` | Show your Telegram user id |
| `/health` | Show non-secret runtime health |
| `/model` | Show provider, model, context, and history backend |
| `/settings` | Show non-secret active settings |
| `/session` | Show current session |
| `/new name` | Create or switch to a session |
| `/sessions` | List sessions |
| `/use name` | Switch to a session |
| `/delete name` | Delete a session |
| `/reset` | Clear the current session |
| `/reset_all` | Clear all sessions for your Telegram user |

## Health And Diagnostics

Use these before blaming Telegram, Ollama, MinIO, or the model:

```powershell
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor
poetry run telegram-llm-bot-doctor --live
poetry run telegram-llm-bot-provider-check
poetry run telegram-llm-bot-eval --mock
```

`telegram-llm-bot-smoke` validates local config without external service calls.

`telegram-llm-bot-doctor` checks required config and local storage.

`telegram-llm-bot-doctor --live` also checks live dependencies and reports severity:

```text
OK: dependency is configured and reachable
WARN: optional dependency is degraded
FAIL: required dependency blocks startup
```

`telegram-llm-bot-provider-check` sends one small prompt to the configured provider.

`telegram-llm-bot-eval --mock` runs deterministic assistant-behavior fixtures without a live
model. Run `telegram-llm-bot-eval` without `--mock` to test the configured provider locally.

`/health` reports provider/model status, history backend, active session, SQLite writability, Ollama reachability, and MinIO reachability. It does not print tokens, credentialed URLs, or raw secrets.

## Docker Compose

For local Docker deployment, keep Ollama on the host and run the bot plus MinIO with Compose.

Create Docker-oriented env:

```powershell
Copy-Item .env.docker.example .env
poetry run telegram-llm-bot-init --force
```

Make sure `.env` contains:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
CHAT_HISTORY_BACKEND=sqlite
MINIO_ENDPOINT_URL=http://minio:9000
```

Start services:

```powershell
docker compose up --build
```

MinIO uses its readiness endpoint as a healthcheck, and the bot service waits for healthy MinIO when started through Compose.

## Development

Run the test suite:

```powershell
poetry run python -m unittest
```

If using the in-project venv directly on Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover
```

Run the release gate:

```powershell
poetry run python -m unittest
poetry run telegram-llm-bot-eval --mock
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor
poetry run telegram-llm-bot-doctor --live
poetry run telegram-llm-bot-provider-check
poetry run ruff check .
poetry run ruff format --check .
poetry run python -m compileall -q src tests
poetry run python -m pip check
poetry check
docker compose config --quiet
poetry build
```

## Project Layout

```text
src/telegram_llm_bot/app.py                      Telegram entrypoint
src/telegram_llm_bot/doctor.py                   Config and readiness doctor
src/telegram_llm_bot/scaffold.py                 Local starter file generator
src/telegram_llm_bot/shared/chat.py              Provider dispatch and tool calls
src/telegram_llm_bot/shared/tools.py             Time, calculator, and web search tools
src/telegram_llm_bot/shared/readiness.py         SQLite, Telegram, Ollama, MinIO checks
src/telegram_llm_bot/shared/audio.py             Local faster-whisper transcription
src/telegram_llm_bot/shared/db/minio_storage.py  Async S3-compatible MinIO storage
src/telegram_llm_bot/shared/history/history.py   SQLite, memory, and Mongo history
src/telegram_llm_bot/bots/base_chatbot/          Default bot handlers and services
tests/                                           Unit tests
```

## Safety

- Do not commit `.env`.
- Do not commit `bot.env`.
- Do not commit logs.
- Do not commit model files.
- Rotate any Telegram token or API key that was pasted into public chat or committed by mistake.

## Version

Current version: `0.9.1`.
