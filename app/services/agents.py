import json
import random
from typing import List, Optional, Tuple

from app import crud
from app.models import FactBank
from app.services import idea as idea_service
from app.services.llm import LLMClient
from app.services.llm.schemas import (
    FactItem,
    FactPack,
    JudgeVerdict,
    ObjectSpec,
    ScriptSpec,
    Storyboard,
)
from app.services.script import normalize_text, validate_voiceover
from app.services.storyboard import default_storyboard
from app.services.style_linter import lint_script
from app.settings import settings

OBJECT_TYPES = ["philosophy_text", "artwork", "marketing_case", "historical_episode"]

BANNED_SCHEMES = [
    "это не ... а ...",
    "речь не о ... речь о ...",
    "дело не в ... дело в ...",
    "суть не в ... а в ...",
    "вопрос не в ... вопрос в ...",
    "проблема не в ... проблема в ...",
    "важно не ... а ...",
    "главное не ... а ...",
    "не столько ... сколько ...",
    "скорее ... чем ...",
]


def _series_prompt(series) -> str:
    if not series:
        return ""
    return series.prompt_preamble or ""


def select_series(session):
    series_list = crud.list_series(session)
    if not series_list:
        return None
    if settings.SERIES_MODE == "random":
        return random.choice(series_list)
    total_jobs = len(crud.list_jobs(session, limit=1000))
    return series_list[total_jobs % len(series_list)]


def generate_object_spec(session, job_id) -> ObjectSpec:
    series = select_series(session)
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        topic = idea_service.pick_topic()
        return ObjectSpec(
            object_type=random.choice(OBJECT_TYPES),
            object_title=topic,
            object_context="Краткий контекст без неподтвержденных фактов.",
            intended_takeaway="Понять ключевую идею и увидеть свежий угол.",
            angle="Разбор через деталь и мотивацию.",
            constraints=[
                "Без выдуманных фактов",
                "Без антитезных схем",
                "Без абстракций как действующих лиц",
            ],
        )

    system = (
        "Ты Researcher. Сформируй ObjectSpec для короткого выпуска. "
        "Русский язык. Конкретный объект: кейс/картина/книга/идея/эпизод. "
        "Не выдумывай факты. 2-3 предложения контекста, без дат и имен без источника."
    )
    user = {
        "object_types": OBJECT_TYPES,
        "series_preamble": _series_prompt(series),
        "constraints": [
            "Запрещены антитезные схемы и нейрошаблоны",
            "Запрещены абстракции как действующие лица",
            "Без псевдо-уточнений и общего тумана",
            "Нужна конкретная деталь объекта",
        ],
        "banned_schemes": BANNED_SCHEMES,
    }
    data = client.generate_json(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        schema=ObjectSpec.model_json_schema(),
        validator=ObjectSpec,
        repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
        model=settings.LLM_MODEL_RESEARCHER or settings.YANDEX_MODEL,
    )
    object_spec = ObjectSpec.model_validate(data)
    if object_spec.object_type not in OBJECT_TYPES:
        raise ValueError(f"Недопустимый object_type: {object_spec.object_type}")
    return object_spec


def _factbank_to_factitem(fact: FactBank) -> FactItem:
    return FactItem(
        id=f"fb-{fact.id}",
        claim=fact.claim,
        source_title=fact.source_title,
        source_author="",
        source_year=None,
        source_locator=fact.source_locator or "",
        source_url=fact.source_url or "",
        evidence_snippet=fact.evidence_snippet or "",
        reliability=fact.reliability or "B",
        notes="",
    )


def generate_factpack(session, job_id, object_spec: ObjectSpec) -> FactPack:
    client = LLMClient(job_id=job_id)
    if settings.FACT_MODE == "bank_only" or not client.is_enabled():
        tags = [object_spec.object_type]
        tags.extend([object_spec.object_title.lower()])
        facts = crud.get_fact_bank_by_tags(session, tags, limit=5)
        return FactPack(facts=[_factbank_to_factitem(fact) for fact in facts])

    system = (
        "Ты Sourcer. Сформируй FactPack только из проверяемых фактов с источниками. "
        "Каждый факт должен иметь источник, URL и короткий фрагмент доказательства до 25 слов."
    )
    user = {
        "object": object_spec.model_dump(),
        "rules": [
            "Не придумывай факты",
            "Если нет источника, не включай факт",
            "Сделай 3-5 фактов",
        ],
    }
    data = client.generate_json(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        schema=FactPack.model_json_schema(),
        validator=FactPack,
        repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
        model=settings.LLM_MODEL_RESEARCHER or settings.YANDEX_MODEL,
    )
    return FactPack.model_validate(data)


def _fact_ids(factpack: FactPack) -> List[str]:
    return [fact.id for fact in factpack.facts]


def _fact_sources(factpack: FactPack) -> List[str]:
    sources = []
    for fact in factpack.facts:
        if fact.source_title:
            sources.append(fact.source_title)
        if fact.source_author:
            sources.append(fact.source_author)
    return sources


def _script_prompt(object_spec: ObjectSpec, factpack: FactPack, series) -> dict:
    return {
        "object": object_spec.model_dump(),
        "facts": [fact.model_dump() for fact in factpack.facts],
        "series_preamble": _series_prompt(series),
        "rules": {
            "language": "ru",
            "voiceover_words": "70-110",
            "no_antithesis": True,
            "no_abstract_agents": True,
            "no_semicolons": True,
            "no_long_dash": True,
            "no_fake_facts": True,
            "fact_mode": settings.FACT_MODE,
        },
        "banned_schemes": BANNED_SCHEMES,
    }


def _has_disallowed_specifics(text: str) -> bool:
    if any(char.isdigit() for char in text or ""):
        return True
    if "«" in text or "»" in text:
        return True
    for marker in ["глава", "страница", "том", "г." ]:
        if marker in text.lower():
            return True
    return False


def generate_script_spec(
    session,
    job_id,
    object_spec: ObjectSpec,
    factpack: FactPack,
    series,
) -> Tuple[ScriptSpec, dict, List[str], bool]:
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        voiceover = (
            f"Перед нами {object_spec.object_title}. "
            "Этот объект показывает, как мысль превращается в форму. "
            "Смотрим на деталь: материал, масштаб, поверхность. "
            "Она задает ритм и решает, на чем держится впечатление. "
            "Логика проста: каждая грань работает на одно ощущение. "
            "В центре действие, украшение отступает. "
            "Такой подход дисциплинирует внимание и оставляет след. "
            "Он помогает увидеть, что идея живет в конструкции. "
            "Мы видим, как зрителя ведут от первой точки к выводу. "
            "В конце остается ясный вывод: смысл строится через конкретное устройство."
        )
        script = ScriptSpec(
            hook=f"Почему {object_spec.object_title} работает сильнее, чем кажется?",
            voiceover_text=voiceover,
            on_screen_captions=[
                "Объект",
                "Деталь",
                "Материал",
                "Ритм",
                "Внимание",
                "Вывод",
            ],
            cta="Хочешь больше разборов - подпишись.",
            object_title=object_spec.object_title,
            fact_ids_used=[],
            on_screen_sources=[],
        )
        style_payload = {
            "issues": lint_script(
                script.hook,
                script.voiceover_text,
                script.on_screen_captions,
                script.cta,
            )
        }
        verdict = {
            "score_total": 60,
            "originality": 60,
            "clarity": 70,
            "factual_discipline": 100,
            "style": 60,
            "must_fix": style_payload["issues"],
            "pass": not style_payload["issues"],
        }
        return script, verdict, style_payload, False

    max_iters = 2
    fact_ids = _fact_ids(factpack)

    for attempt in range(max_iters):
        writer_system = (
            "Ты Writer. Напиши ScriptSpec для вертикального видео. "
            "Никаких нейрошаблонов, никаких антитез, живой русский. "
            "Конкретная деталь объекта обязательна."
        )
        writer_user = _script_prompt(object_spec, factpack, series)
        if fact_ids:
            writer_user["fact_ids_required"] = fact_ids
        else:
            writer_user["fact_ids_required"] = []
            writer_user["note"] = "FactPack пустой: никаких дат, имен, названий книг и цитат."

        script_data = client.generate_json(
            [
                {"role": "system", "content": writer_system},
                {"role": "user", "content": json.dumps(writer_user, ensure_ascii=False)},
            ],
            schema=ScriptSpec.model_json_schema(),
            validator=ScriptSpec,
            repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
            model=settings.LLM_MODEL_WRITER or settings.YANDEX_MODEL,
        )
        script = ScriptSpec.model_validate(script_data)

        editor_system = (
            "Ты Editor. Отредактируй ScriptSpec: лучше ритм, чище стиль, без штампов. "
            "Не добавляй новых фактов. Не используй антитезы."
        )
        editor_user = {
            "script": script.model_dump(),
            "rules": writer_user["rules"],
            "banned_schemes": BANNED_SCHEMES,
        }
        edited_data = client.generate_json(
            [
                {"role": "system", "content": editor_system},
                {"role": "user", "content": json.dumps(editor_user, ensure_ascii=False)},
            ],
            schema=ScriptSpec.model_json_schema(),
            validator=ScriptSpec,
            repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
            model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
        )
        script = ScriptSpec.model_validate(edited_data)

        issues = []
        if not validate_voiceover(script.voiceover_text):
            issues.append("voiceover_text должен быть 70-110 слов")
        if not (6 <= len(script.on_screen_captions) <= 8):
            issues.append("on_screen_captions должен быть 6-8 строк")

        if fact_ids:
            if not set(script.fact_ids_used).issubset(set(fact_ids)):
                issues.append("fact_ids_used содержит неизвестные id")
            if not script.on_screen_sources:
                issues.append("on_screen_sources должны быть заполнены")
            elif len(script.on_screen_sources) > 2:
                issues.append("on_screen_sources должен быть 1-2 строки")
            else:
                allowed_sources = _fact_sources(factpack)
                if not any(source in " ".join(allowed_sources) for source in script.on_screen_sources):
                    issues.append("on_screen_sources не соответствуют FactPack")
        else:
            if script.fact_ids_used:
                issues.append("fact_ids_used должны быть пустыми, когда FactPack пуст")
            if script.on_screen_sources:
                issues.append("on_screen_sources должны быть пустыми, когда FactPack пуст")
            if _has_disallowed_specifics(script.voiceover_text + " " + script.hook):
                issues.append("конкретика запрещена без FactPack")

        style_issues = lint_script(
            script.hook,
            script.voiceover_text,
            script.on_screen_captions,
            script.cta,
        )
        issues.extend(style_issues)

        judge_system = "Ты Judge. Оцени текст по критериям, верни verdict JSON."
        judge_user = {
            "script": script.model_dump(),
            "issues": issues,
            "object": object_spec.model_dump(),
            "facts": [fact.model_dump() for fact in factpack.facts],
        }
        verdict_data = client.generate_json(
            [
                {"role": "system", "content": judge_system},
                {"role": "user", "content": json.dumps(judge_user, ensure_ascii=False)},
            ],
            schema=JudgeVerdict.model_json_schema(),
            validator=JudgeVerdict,
            repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
            model=settings.LLM_MODEL_JUDGE or settings.YANDEX_MODEL,
        )
        verdict = JudgeVerdict.model_validate(verdict_data)

        must_fix = list(dict.fromkeys(issues + verdict.must_fix))
        if verdict.pass_ and not must_fix:
            style_payload = {"issues": style_issues}
            return script, verdict.model_dump(by_alias=True), style_payload, False

        if attempt == max_iters - 1:
            style_payload = {"issues": style_issues}
            return script, verdict.model_dump(by_alias=True), style_payload, False

        rewrite_system = (
            "Ты Writer. Перепиши ScriptSpec с учетом must_fix. "
            "Не добавляй новых фактов и не используй антитезы."
        )
        rewrite_user = {
            "script": script.model_dump(),
            "must_fix": must_fix,
            "rules": writer_user["rules"],
        }
        script_data = client.generate_json(
            [
                {"role": "system", "content": rewrite_system},
                {"role": "user", "content": json.dumps(rewrite_user, ensure_ascii=False)},
            ],
            schema=ScriptSpec.model_json_schema(),
            validator=ScriptSpec,
            repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
            model=settings.LLM_MODEL_WRITER or settings.YANDEX_MODEL,
        )
        script = ScriptSpec.model_validate(script_data)

    style_payload = {"issues": style_issues}
    return script, verdict.model_dump(by_alias=True), style_payload, False


def generate_storyboard(session, job_id, object_spec: ObjectSpec, script: ScriptSpec) -> Storyboard:
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        return default_storyboard(object_spec.object_title)

    system = "Ты Storyboard. Сформируй 3 сцены, 8 сек каждая, вертикальный формат."
    user = {
        "object": object_spec.model_dump(),
        "script": script.model_dump(),
        "rules": [
            "3 сцены",
            "duration_sec=8",
            "учитывай объект и ключевую деталь",
        ],
    }
    data = client.generate_json(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        schema=Storyboard.model_json_schema(),
        validator=Storyboard,
        repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
        model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
    )
    storyboard = Storyboard.model_validate(data)
    if len(storyboard.scenes) != 3:
        raise ValueError("Storyboard должен содержать 3 сцены")
    for scene in storyboard.scenes:
        scene.duration_sec = 8
    return storyboard


def compute_digests(script: ScriptSpec) -> Tuple[str, str]:
    return normalize_text(script.hook), normalize_text(script.voiceover_text)
