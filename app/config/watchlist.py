from pathlib import Path

import yaml


CONFIG_PATH = Path("config/watchlist.yaml")


def load_watchlist_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def get_symbols(group: str) -> list[str]:
    config = load_watchlist_config()
    return config.get(group, [])
