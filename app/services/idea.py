import json
import random
from pathlib import Path

TOPIC_FILE = Path(__file__).resolve().parents[1] / "seed" / "topic_bank.json"


def load_topic_bank():
    if not TOPIC_FILE.exists():
        return []
    with TOPIC_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def pick_topic() -> str:
    topics = load_topic_bank()
    if not topics:
        return "Неизвестная тема"
    return random.choice(topics)
