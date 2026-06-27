# Telegram LLM Bot

A Python Telegram bot starter with local Ollama support, chat history backends, and optional Beam-hosted inference.

Current version: `0.2.0`.

The default local example uses `qwen2.5:0.5b`, an Ollama model listed at 398 MB with Q4_K_M quantization. It is a practical low-RAM default for CPU-only demos. Runtime memory still depends on your platform, context length, and Ollama settings, so this repo uses conservative defaults.

## Quickstart

Install Ollama, then pull the default low-RAM model:

```powershell
ollama pull qwen2.5:0.5b
```

Install the Python app:

```powershell
poetry install
```

Create the root env file:

```powershell
Copy-Item .env.example .env
```

Create the bot env file and add your Telegram token:

```powershell
Copy-Item src\telegram_llm_bot\bots\base_chatbot\.env.example src\telegram_llm_bot\bots\base_chatbot\.env
```

Run the non-network smoke check:

```powershell
poetry run telegram-llm-bot-smoke
```

Check the local Ollama provider:

```powershell
poetry run telegram-llm-bot-provider-check
```

Start the Telegram bot:

```powershell
poetry run telegram-llm-bot
```

## Configuration

Root `.env`:

```env
MONGO_HOST=localhost
MONGO_PORT=27017

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
```

Bot env at `src/telegram_llm_bot/bots/base_chatbot/.env`:

```env
TELEGRAM_BOT_TOKEN=
SETTINGS_FILE=telegram_llm_bot.bots.base_chatbot.settings
BOT_NAME=telegram-llm-bot
COLLECTION_NAME=users
```

Create a Telegram bot with BotFather, paste the token into `TELEGRAM_BOT_TOKEN`, and start a chat with your bot in Telegram.

## Providers

### Ollama

Default provider:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:0.5b
```

The app calls Ollama's local chat API at:

```text
http://localhost:11434/api/chat
```

### Echo

Use `echo` for smoke tests without Ollama, Beam, Telegram network calls, or API keys:

```env
LLM_PROVIDER=echo
```

### Beam

Beam is still supported as an optional advanced provider:

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

## Docker

The compose file starts MongoDB and the bot service:

```powershell
docker compose up --build
```

If Ollama runs on your host machine, set `OLLAMA_BASE_URL` to a host-reachable URL for your Docker environment.

## Development

Run checks:

```powershell
poetry run telegram-llm-bot-smoke
poetry run python -m unittest
poetry run python -m compileall -q src tests
poetry run python -m pip check
```

Fast install with uv is also supported after Poetry has created or refreshed the lock:

```powershell
uv venv --python 3.11 --seed
.\.venv\Scripts\python.exe -m pip install -e .
```

## Notes

- `qwen2.5:0.5b` is the default because it gives a useful local bot demo while keeping the model artifact well under 1 GB.
- The 1 GB target is practical low-RAM local usage, not a strict process memory guarantee.
- Do not commit `.env`, logs, model files, or Telegram tokens.
