import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from telegram_llm_bot.paths import BASE_CHATBOT_DIR, PROJECT_DIR

DEFAULT_BOT_CONFIG_FILE = BASE_CHATBOT_DIR / "config.yml"


@dataclass
class BotConfig:
    path: Path
    start: str
    system: str


def project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_DIR / path


def bot_config_path() -> Path:
    configured = os.getenv("BOT_CONFIG_FILE")
    return project_path(configured) if configured else DEFAULT_BOT_CONFIG_FILE


def load_bot_config(path: Path = None) -> BotConfig:
    config_path = path or bot_config_path()
    if not config_path.exists():
        raise ValueError(f"Bot config file does not exist: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}

    start = str(data.get("start") or "").strip()
    system = str(data.get("system") or "").strip()
    if not start or not system:
        raise ValueError("Bot config must define non-empty start and system values")
    return BotConfig(path=config_path, start=start, system=system)
