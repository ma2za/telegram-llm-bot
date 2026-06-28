# Telegram LLM Bot

[![CI](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml)

Ollama-first Python starter for building a Telegram AI chatbot that runs locally, works with low-RAM CPU machines, and can be extended to hosted inference later.

The default example uses `qwen3.5:0.8b` through Ollama for low local memory use with tool support. Voice messages are transcribed locally with `faster-whisper` using Whisper `small` on CPU `int8`, and raw voice audio is stored in MinIO through the S3-compatible async boto stack.

## Why Use This

- Local-first Telegram AI bot with no paid LLM API required.
- Low-RAM default model: `qwen3.5:0.8b`.
- Provider switch via env: `ollama`, `beam`, or `echo`.
- Ollama tool calling with built-in datetime and calculator tools.
- Local voice-to-text with `faster-whisper`, no transcription API key required.
- Voice object storage in MinIO via async boto-compatible S3 calls.
- Smoke checks that do not call Telegram or external APIs.
- Config doctor for provider, history, and Telegram setup.
- `/health` command for non-secret runtime status.
- Local scaffold command that creates starter config files.
- Optional live provider check for Ollama.
- SQLite history for persistent Mongo-free local development.
- Named conversation sessions for separate topics.
- `/help`, `/health`, `/settings`, `/session`, `/new`, `/reset`, and `/model` commands for cleaner demos and debugging.
- Per-user session locking keeps concurrent Telegram replies ordered.
- Mongo history still available for deployed bots.
- Poetry package scripts for repeatable runs.

## Quickstart

Use Python 3.9 or newer.

Install Ollama and pull the default model:

```powershell
ollama pull qwen3.5:0.8b
```

Install the app:

```powershell
poetry install
```

Create local starter files:

```powershell
poetry run telegram-llm-bot-init
```

Create a Telegram bot with BotFather, then put the token in:

```text
bot.env
```

Run local checks:

```powershell
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor
poetry run telegram-llm-bot-provider-check
```

Start the bot:

```powershell
poetry run telegram-llm-bot
```

Open Telegram and message your bot.

## Configuration

`telegram-llm-bot-init` creates `.env`, `bot.env`, and `bot.yml`.

Root `.env`:

```env
MONGO_HOST=localhost
MONGO_PORT=27017
CHAT_HISTORY_BACKEND=sqlite
SQLITE_HISTORY_PATH=.tmp/chat_history.sqlite3

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:0.8b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
OLLAMA_TOOLS_ENABLED=true

LOCAL_TRANSCRIPTION_MODEL=small
LOCAL_TRANSCRIPTION_COMPUTE_TYPE=int8
LOCAL_TRANSCRIPTION_DEVICE=cpu
LOCAL_TRANSCRIPTION_BEAM_SIZE=5
LOCAL_TRANSCRIPTION_CPU_THREADS=4

MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=telegram-llm-bot
```

Bot env at `bot.env`:

```env
TELEGRAM_BOT_TOKEN=
BOT_NAME=telegram-llm-bot
BOT_CONFIG_FILE=bot.yml

BEAM_TOKEN=
BEAM_URL=
BEAM_APP_NAME=telegram-llm-bot
```

Bot config at `bot.yml`:

```yaml
start: Hello. Send me a message and I will reply.
system: You are a helpful assistant. Answer clearly and concisely.
```

The default `CHAT_HISTORY_BACKEND=sqlite` keeps local setup simple and persists chat history across restarts. Use Mongo when you want a deployed database backend, or `memory` for throwaway test runs.

## Sessions

Each Telegram user starts in the `default` session. Sessions keep separate chat history for topics like `work`, `ideas`, or `travel`.

```text
/session       show current session
/new work      create or switch to work
/sessions      list sessions
/use work      switch to work
/delete work   delete work
/reset         clear the current session
/reset_all     clear all your sessions
```

## Runtime Health

Use `/health` in Telegram to see the active provider, model, history backend, session, and whether the SQLite history directory is writable. The output avoids tokens and credentialed URLs.

## Providers

| Provider | Env value | Use case |
| --- | --- | --- |
| Ollama | `LLM_PROVIDER=ollama` | Default local bot with `qwen3.5:0.8b` |
| Echo | `LLM_PROVIDER=echo` | Fast smoke tests with no model/API calls |
| Beam | `LLM_PROVIDER=beam` | Optional hosted/self-hosted inference path |

### Ollama

The Ollama provider calls:

```text
http://localhost:11434/api/chat
```

Default low-RAM tool-capable settings:

```env
OLLAMA_MODEL=qwen3.5:0.8b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
OLLAMA_TOOLS_ENABLED=true
```

The built-in tool set includes current datetime lookup and safe arithmetic.

## Voice and Object Storage

Voice messages are downloaded from Telegram, stored in MinIO, transcribed locally, and then sent through the same session-aware chat flow as text messages.

Local transcription defaults:

```env
LOCAL_TRANSCRIPTION_MODEL=small
LOCAL_TRANSCRIPTION_COMPUTE_TYPE=int8
LOCAL_TRANSCRIPTION_DEVICE=cpu
LOCAL_TRANSCRIPTION_BEAM_SIZE=5
LOCAL_TRANSCRIPTION_CPU_THREADS=4
```

MinIO defaults:

```env
MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=telegram-llm-bot
```

### Beam

Beam support is kept as an optional advanced provider:

```env
LLM_PROVIDER=beam
BEAM_TOKEN=
BEAM_URL=https://apps.beam.cloud/{something}
BEAM_APP_NAME=telegram-llm-bot
```

Deploy the Beam app from:

```powershell
cd src\telegram_llm_bot\shared\llm\beam
beam deploy app.py
```

## Commands

```powershell
poetry run telegram-llm-bot-init
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor
poetry run telegram-llm-bot-doctor --live
poetry run telegram-llm-bot-provider-check
poetry run telegram-llm-bot
```

`telegram-llm-bot-init` creates local `.env`, `bot.env`, and `bot.yml` starter files.

`telegram-llm-bot-smoke` validates local configuration without calling Telegram or Ollama.

`telegram-llm-bot-doctor` checks Telegram, provider, and history configuration. Use `--live` to call Ollama and Mongo when configured.

`telegram-llm-bot-provider-check` sends a tiny prompt to the configured provider and prints the response.

`telegram-llm-bot` starts Telegram polling.

## Bot Commands

```text
/help    show bot commands
/my_id   show your Telegram user id
/health show runtime health
/model   show active provider, model, context, and history backend
/new     create or switch to a session
/session show current session
/sessions list your sessions
/use     switch to an existing session
/delete  delete a session
/reset   clear current session history
/reset_all clear all your sessions
/settings show active non-secret settings
```

## Docker

The compose file runs MinIO and the bot service, reads `.env` and `bot.env`, and uses SQLite by default. If Ollama runs on the host machine, use the Docker env example so the container can reach it:

```powershell
Copy-Item .env.docker.example .env
poetry run telegram-llm-bot-init --force
docker compose up --build
```

The Docker default uses:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
CHAT_HISTORY_BACKEND=sqlite
MINIO_ENDPOINT_URL=http://minio:9000
```

The image and Compose service use `telegram-llm-bot-smoke` as a health check.

## Development

Run the release checks:

```powershell
poetry run python -m unittest
poetry run telegram-llm-bot-smoke
poetry run telegram-llm-bot-doctor
poetry run telegram-llm-bot-provider-check
poetry run ruff check .
poetry run ruff format --check .
poetry run python -m compileall -q src tests
poetry run python -m pip check
poetry check
docker compose config --quiet
```

Build package artifacts:

```powershell
poetry build
```

Fast editable install with uv is also possible:

```powershell
uv venv --python 3.11 --seed
.\.venv\Scripts\python.exe -m pip install -e .
```

## Project Layout

```text
src/telegram_llm_bot/app.py                      Telegram entrypoint
src/telegram_llm_bot/shared/chat.py              LLM provider dispatch and tool calls
src/telegram_llm_bot/shared/audio.py             Local faster-whisper transcription
src/telegram_llm_bot/shared/db/minio_storage.py  Async S3-compatible MinIO storage
src/telegram_llm_bot/shared/history/history.py   SQLite/Memory/Mongo chat history
src/telegram_llm_bot/config.py                   Bot YAML config loading
src/telegram_llm_bot/bots/base_chatbot/          Default bot configuration
tests/test_chat_providers.py                     Provider unit tests
tests/test_doctor.py                             Config doctor unit tests
tests/test_text_service.py                       Error message unit tests
```

## Safety

- Do not commit `.env` files.
- Do not commit `bot.env`.
- Do not commit logs.
- Do not commit model files.
- Rotate any Telegram token that was pasted into public chat or committed by mistake.

## Version

Current version: `0.8.0`.
