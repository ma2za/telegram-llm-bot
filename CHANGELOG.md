# Changelog

## 0.2.0

- Add Ollama provider support with `qwen2.5:0.5b` as the default low-RAM local model.
- Add `LLM_PROVIDER=ollama`, `beam`, and `echo` dispatch.
- Add local smoke and provider-check commands.
- Add memory chat history backend for Mongo-free local development.
- Add env examples for root and bot-specific configuration.
- Refresh README around the Ollama-first quickstart.
- Fix config loading for `start_message` and `system_prompt`.
- Harden typing indicators against Telegram flood-control errors.
