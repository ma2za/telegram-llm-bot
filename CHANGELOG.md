# Changelog

## 0.5.0

- Add `telegram-llm-bot-init` to scaffold local `.env`, `bot.env`, and `bot.yml` files.
- Add `BOT_CONFIG_FILE` support so users can configure bot prompts outside package internals.
- Update environment loading to include local `bot.env` while preserving existing `.env` behavior.
- Update doctor to validate the active bot config and show detected env/config files.
- Update README and CI to use the scaffolded local setup path.

## 0.4.3

- Add a dummy Telegram token during CI env setup so `telegram-llm-bot-doctor` can validate example configuration without a real bot token.
- Keep doctor strict for missing, empty, and `replace-me` Telegram tokens.

## 0.4.2

- Restore support for Python 3.9 through 3.13.
- Remove LangChain from the default runtime path to avoid stale `numpy`, `numexpr`, and `greenlet` builds.
- Remove the legacy OpenAI SDK, `mmh3`, `pydantic-settings`, and Weaviate client from default dependencies.
- Add lightweight internal chat message classes used by providers and history storage.

## 0.4.1

- Limit package metadata and CI to Python 3.11.
- Avoid Python 3.12 installs with legacy compiled dependencies such as `numpy`, `greenlet`, and `aiohttp`.

## 0.4.0

- Add `telegram-llm-bot-doctor` for local configuration diagnostics.
- Add `/help` and `/settings` bot commands.
- Expand `/model` to show Ollama context size.
- Return clearer user-facing messages for Ollama and SQLite runtime failures.
- Update Docker Compose for the SQLite/Ollama-first path.
- Add Ruff lint and format checks to CI.

## 0.3.0

- Add GitHub Actions CI.
- Add SQLite chat history as the default persistent local backend.
- Keep `memory` and `mongo` history backends available.
- Add `/reset` to clear a user's chat history.
- Add `/model` to show active provider, model, and history backend without secrets.
- Update README and env examples for SQLite-first local setup.

## 0.2.0

- Add Ollama provider support with `qwen2.5:0.5b` as the default low-RAM local model.
- Add `LLM_PROVIDER=ollama`, `beam`, and `echo` dispatch.
- Add local smoke and provider-check commands.
- Add memory chat history backend for Mongo-free local development.
- Add env examples for root and bot-specific configuration.
- Refresh README around the Ollama-first quickstart.
- Fix config loading for `start_message` and `system_prompt`.
- Harden typing indicators against Telegram flood-control errors.
