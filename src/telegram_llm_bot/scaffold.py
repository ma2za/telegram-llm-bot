import argparse
from pathlib import Path

ROOT_ENV = """MONGO_HOST=localhost
MONGO_PORT=27017
CHAT_HISTORY_BACKEND=sqlite
SQLITE_HISTORY_PATH=.tmp/chat_history.sqlite3
CHAT_HISTORY_MAX_MESSAGES=20

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:0.8b
OLLAMA_NUM_CTX=1024
OLLAMA_NUM_PREDICT=256
OLLAMA_TEMPERATURE=0.2
OLLAMA_TOOLS_ENABLED=true
OLLAMA_THINK=false
OLLAMA_HEALTH_TIMEOUT=5

SEARCHAPI_API_KEY=
SEARCHAPI_TIMEOUT=20
SEARCHAPI_SAFE=active
SEARCHAPI_HL=en
SEARCHAPI_GL=us

LOCAL_TRANSCRIPTION_MODEL=small
LOCAL_TRANSCRIPTION_COMPUTE_TYPE=int8
LOCAL_TRANSCRIPTION_DEVICE=cpu
LOCAL_TRANSCRIPTION_BEAM_SIZE=5
LOCAL_TRANSCRIPTION_CPU_THREADS=4

MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=telegram-llm-bot
MINIO_HEALTH_TIMEOUT=5
"""

BOT_ENV = """TELEGRAM_BOT_TOKEN=
BOT_NAME=telegram-llm-bot
BOT_CONFIG_FILE=bot.yml

# Optional when LLM_PROVIDER=beam
BEAM_TOKEN=
BEAM_URL=
BEAM_APP_NAME=telegram-llm-bot
"""

BOT_CONFIG = """start: Hello. Send me a message and I will reply.
system: |
  You are a concise, practical assistant in a Telegram chat.
  Answer the user's latest message directly first.
  Use short paragraphs or bullets when they make the answer easier to scan.
  Ask one clarifying question only when a correct answer depends on missing information.
  Say when you are uncertain instead of inventing facts.
  Use available tools for arithmetic, dates, times, and current information.
  Keep replies compact unless the user asks for detail.
"""


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists. Use --force to overwrite it.")
    path.write_text(content, encoding="utf-8")


def init_project(target: Path, force: bool = False) -> list[Path]:
    target.mkdir(parents=True, exist_ok=True)
    files = [
        (target / ".env", ROOT_ENV),
        (target / "bot.env", BOT_ENV),
        (target / "bot.yml", BOT_CONFIG),
    ]
    for path, content in files:
        write_file(path, content, force)
    return [path for path, _ in files]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    files = init_project(Path(args.target), force=args.force)
    for path in files:
        print(f"Created {path}")


if __name__ == "__main__":
    main()
