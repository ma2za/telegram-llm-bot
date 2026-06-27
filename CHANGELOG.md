# Changelog

## 0.4.0

- Add `telegram-llm-bot-doctor` for local configuration diagnostics.
- Add `/help` and `/settings` bot commands.
- Expand `/model` to show Ollama context size.
- Return clearer user-facing messages for Ollama and SQLite runtime failures.
- Update Docker Compose for the SQLite/Ollama-first path.
- Add Ruff lint and format checks to CI.

## 0.3.0

- Add GitHub Actions CI for Python 3.11 and 3.12.
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
