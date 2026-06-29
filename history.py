import json
import os

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_HISTORY_ENTRIES = 100


def log_conversion(record: dict) -> None:
    history = _load_history()
    history.append(record)
    history = history[-MAX_HISTORY_ENTRIES:]  # keep file from growing forever
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except OSError:
        pass  # logging failures should never crash a conversion


def _load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_recent(n: int = 10) -> list:
    history = _load_history()
    return history[-n:][::-1]  # most recent first


def clear_history() -> None:
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
    except OSError:
        pass
