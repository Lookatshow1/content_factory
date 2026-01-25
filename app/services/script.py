import re


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яЁё]+", text or ""))


def validate_voiceover(text: str) -> bool:
    words = count_words(text)
    return 70 <= words <= 110


def trim_voiceover(text: str, max_words: int = 110) -> str:
    if not text:
        return text
    matches = list(re.finditer(r"[A-Za-zА-Яа-яЁё]+", text))
    if len(matches) <= max_words:
        return text
    end = matches[max_words - 1].end()
    trimmed = text[:end].rstrip()
    if trimmed and trimmed[-1] not in ".!?":
        trimmed += "."
    return trimmed


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9а-яА-Я]+", " ", text.lower())
    return " ".join(cleaned.split())
