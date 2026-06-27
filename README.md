# Telegram LLM Bot

[![CI](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ma2za/telegram-llm-bot/actions/workflows/ci.yml)

Ollama-first Python starter for building a Telegram AI chatbot that runs locally, works with low-RAM CPU machines, and can be extended to hosted inference later.

The default example uses `qwen2.5:0.5b` through Ollama. The model artifact is about 398 MB, so it is practical for small local demos while still giving useful assistant behavior. Runtime memory depends on Ollama, platform, context length, and concurrent traffic; this template keeps the default context and output limits conservative.

## Why Use This

- Local-first Telegram AI bot with no paid LLM API required.
- Low-RAM default model: `qwen2.5:0.5b`.
- Provider switch via env: `ollama`, `beam`, or `echo`.
- Smoke checks that do not call Telegram or external APIs.
- Config doctor for provider, history, and Telegram setup.
- Local scaffold command that creates starter config files.
- Optional live provider check for Ollama.
- SQLite history for persistent Mongo-free local development.
- `/help`, `/settings`, `/reset`, and `/model` commands for cleaner demos and debugging.
- Mongo history still available for deployed bots.
- Poetry package scripts for repeatable runs.

## Quickstart

Use Python 3.9 or newer.

Install Ollama and pull the default model:

```powershell
ollama pull qwen2.5:0.5b
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
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
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

## Providers

| Provider | Env value | Use case |
| --- | --- | --- |
| Ollama | `LLM_PROVIDER=ollama` | Default local bot with `qwen2.5:0.5b` |
| Echo | `LLM_PROVIDER=echo` | Fast smoke tests with no model/API calls |
| Beam | `LLM_PROVIDER=beam` | Optional hosted/self-hosted inference path |

### Ollama

The Ollama provider calls:

```text
http://localhost:11434/api/chat
```

Default low-RAM settings:

```env
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
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
/model   show active provider, model, context, and history backend
/reset   clear your chat history
/settings show active non-secret settings
```

## Docker

The compose file runs only the bot service and uses SQLite by default. If Ollama runs on the host machine, use the Docker env example so the container can reach it:

```powershell
Copy-Item .env.docker.example .env
docker compose up --build
```

The Docker default uses:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
CHAT_HISTORY_BACKEND=sqlite
```

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
src/telegram_llm_bot/shared/chat.py              LLM provider dispatch
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

Current version: `0.5.0`.
