import re
from typing import List

BANNED_PATTERNS = [
    re.compile(r"это не .* а .*", re.IGNORECASE),
    re.compile(r"речь не о .* речь о .*", re.IGNORECASE),
    re.compile(r"дело не в .* дело в .*", re.IGNORECASE),
    re.compile(r"суть не в .* а в .*", re.IGNORECASE),
    re.compile(r"вопрос не в .* вопрос в .*", re.IGNORECASE),
    re.compile(r"проблема не в .* проблема в .*", re.IGNORECASE),
    re.compile(r"важно не .* а .*", re.IGNORECASE),
    re.compile(r"главное не .* а .*", re.IGNORECASE),
    re.compile(r"не столько .* сколько .*", re.IGNORECASE),
    re.compile(r"скорее .* чем .*", re.IGNORECASE),
]

ABSTRACT_AGENT = re.compile(
    r"\b(прошлое|память|история|хаос|форма|судьба|культура|рынок|общество|экономика|время|будущее)"
    r"\b\s+\b(любит|хочет|врёт|помнит|решает|знает|говорит|думает|шепчет|просит|требует|наказывает|награждает|обманывает)\b",
    re.IGNORECASE,
)


def lint_text(text: str) -> List[str]:
    issues = []
    if not text:
        return issues
    if "—" in text:
        issues.append("Запрещено длинное тире (—)")
    if ";" in text:
        issues.append("Запрещена точка с запятой")
    for pattern in BANNED_PATTERNS:
        if pattern.search(text):
            issues.append(f"Запрещенная схема: {pattern.pattern}")
    if ABSTRACT_AGENT.search(text):
        issues.append("Абстракция как действующее лицо")
    return issues


def lint_script(hook: str, voiceover: str, captions: List[str], cta: str) -> List[str]:
    issues = []
    issues.extend(lint_text(hook))
    issues.extend(lint_text(voiceover))
    for line in captions or []:
        issues.extend(lint_text(line))
    issues.extend(lint_text(cta))
    # deduplicate
    return list(dict.fromkeys(issues))
