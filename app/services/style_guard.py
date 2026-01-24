import re
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import yaml


def _compile(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


@lru_cache(maxsize=1)
def load_style_guard():
    path = Path(__file__).resolve().parents[2] / "config" / "style_guard.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def lint_text(text: str) -> List[str]:
    if not text:
        return []
    data = load_style_guard()
    issues = []
    for pattern in _compile(data.get("banned_regex", [])):
        if pattern.search(text):
            issues.append(f"Запрещенная схема: {pattern.pattern}")
    for pattern in _compile(data.get("abstract_agent_regex", [])):
        if pattern.search(text):
            issues.append("Абстракция как действующее лицо")
    if "—" in text:
        issues.append("Запрещено длинное тире (—)")
    if ";" in text:
        issues.append("Запрещена точка с запятой")
    return list(dict.fromkeys(issues))


def lint_script(hook: str, voiceover: str, captions: List[str], cta: str) -> List[str]:
    issues = []
    issues.extend(lint_text(hook))
    issues.extend(lint_text(voiceover))
    for line in captions or []:
        issues.extend(lint_text(line))
    issues.extend(lint_text(cta))
    return list(dict.fromkeys(issues))


def validate_captions_length(captions: List[str]) -> Tuple[bool, List[str]]:
    data = load_style_guard()
    max_len = int(data.get("max_caption_len", 42))
    min_len = int(data.get("min_caption_len", 10))
    issues = []
    for line in captions or []:
        if len(line) > max_len:
            issues.append(f"caption длиннее {max_len} символов")
        if len(line) < min_len:
            issues.append(f"caption короче {min_len} символов")
    return (len(issues) == 0, list(dict.fromkeys(issues)))
