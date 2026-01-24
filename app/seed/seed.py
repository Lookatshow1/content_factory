import json
from pathlib import Path

from app.db import SessionLocal
from app.models import ContentSeries, FactBank, FactCard

SERIES = [
    {
        "name": "Кейс рекламы в одной сцене",
        "prompt_preamble": "Разбираем рекламу как мини-спектакль: сцена, конфликт, решение.",
    },
    {
        "name": "Философская идея через предмет",
        "prompt_preamble": "Идея раскрывается через конкретный предмет и его функцию.",
    },
    {
        "name": "Картина как инженерный чертёж смысла",
        "prompt_preamble": "Смотрим на картину как на конструкцию: узлы, связи, акценты.",
    },
    {
        "name": "Исторический эпизод как урок стратегии",
        "prompt_preamble": "Берем один эпизод и извлекаем стратегический вывод.",
    },
    {
        "name": "Маркетинговый трюк и его цена",
        "prompt_preamble": "Разбираем прием, эффект и скрытую цену.",
    },
]

TOPIC_FILE = Path(__file__).resolve().parent / "topic_bank.json"
FACT_CARDS_FILE = Path(__file__).resolve().parents[2] / "seed" / "fact_cards.jsonl"


def seed_series(session):
    if session.query(ContentSeries).count() > 0:
        return
    for item in SERIES:
        session.add(ContentSeries(**item))
    session.commit()


def seed_fact_bank(session):
    if session.query(FactBank).count() > 0:
        return
    placeholders = []
    for idx in range(1, 31):
        placeholders.append(
            FactBank(
                claim=f"Заглушка факта {idx}",
                source_title="",
                source_url="",
                source_locator="",
                evidence_snippet="",
                reliability="C",
                tags=["placeholder"],
            )
        )
    session.add_all(placeholders)
    session.commit()


def seed_fact_cards(session):
    if session.query(FactCard).count() > 0:
        return
    if not FACT_CARDS_FILE.exists():
        return
    items = []
    with FACT_CARDS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            items.append(
                FactCard(
                    domain=data.get("domain"),
                    title=data.get("title"),
                    claim_lines=data.get("claim_lines", []),
                    sources=data.get("sources", []),
                    tags=data.get("tags", []),
                    language=data.get("language", "ru"),
                )
            )
    session.add_all(items)
    session.commit()


def ensure_topic_bank():
    if TOPIC_FILE.exists():
        return
    topics = [f"Тема {idx}" for idx in range(1, 51)]
    TOPIC_FILE.write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ensure_topic_bank()
    session = SessionLocal()
    try:
        seed_series(session)
        seed_fact_bank(session)
        seed_fact_cards(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
