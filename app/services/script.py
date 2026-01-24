import re


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яЁё]+", text or ""))


def validate_voiceover(text: str) -> bool:
    words = count_words(text)
    return 70 <= words <= 110


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9а-яА-Я]+", " ", text.lower())
    return " ".join(cleaned.split())
