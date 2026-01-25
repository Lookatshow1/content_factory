import json
import random
from typing import List, Optional, Tuple

from app import crud
from app.models import FactCard
from app.services import idea as idea_service
from app.services.editorial import select_rubric
from app.services.llm import LLMClient
from app.services.llm.schemas import (
    FactItem,
    FactPack,
    IdeaSpec,
    JudgeVerdict,
    ScriptSpec,
    Storyboard,
)
from app.services.script import normalize_text, trim_voiceover, validate_voiceover
from app.services.storyboard import default_storyboard
from app.services.style_guard import lint_script, validate_captions_length
from app.settings import settings


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


def _rubric_for_job(session) -> Optional[dict]:
    total_jobs = len(crud.list_jobs(session, limit=1000))
    return select_rubric(total_jobs)


def generate_idea_spec(session, job_id) -> IdeaSpec:
    rubric = _rubric_for_job(session) or {
        "id": "default",
        "name": "Свободный разбор",
        "domain": "culture",
        "goal": "Дать четкий вывод",
        "structure": [],
        "banned_moves": [],
        "source_requirements": "",
        "claims_without_source": [],
    }
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        topic = idea_service.pick_topic()
        return IdeaSpec(
            rubric_id=rubric["id"],
            rubric_name=rubric["name"],
            domain=rubric["domain"],
            object_title=topic,
            object_context="Краткий контекст без неподтвержденных фактов.",
            intended_takeaway="Зритель унесет ясный вывод за 30 секунд.",
            angle="Разбор через конкретную деталь.",
            constraints=[
                "Без выдуманных фактов",
                "Без антитезных схем",
                "Без абстракций как действующих лиц",
            ],
        )

    system = (
        "Ты Researcher. Сформируй IdeaSpec для короткого выпуска. "
        "Русский язык. Конкретный объект: кейс/картина/книга/идея/эпизод. "
        "Не выдумывай факты. 2-3 предложения контекста, без дат и имен без источника."
    )
    user = {
        "rubric": rubric,
        "constraints": [
            "Запрещены антитезные схемы и нейрошаблоны",
            "Запрещены абстракции как действующие лица",
            "Без псевдо-уточнений и общего тумана",
            "Нужна конкретная деталь объекта",
        ],
    }
    data = client.generate_json(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        schema=IdeaSpec.model_json_schema(),
        validator=IdeaSpec,
        repair_model=settings.LLM_MODEL_EDITOR or settings.YANDEX_MODEL,
        model=settings.LLM_MODEL_RESEARCHER or settings.YANDEX_MODEL,
    )
    return IdeaSpec.model_validate(data)


def _factcard_to_items(card: FactCard, limit: int = 2) -> List[FactItem]:
    items = []
    for idx, claim in enumerate(card.claim_lines[:limit]):
        sources = (card.sources or [])[:3]
        if not sources:
            continue
        first = sources[0] if sources else {"title": "", "url": "", "date": None}
        items.append(
            FactItem(
                id=f"fc-{card.id}-{idx}",
                claim=claim,
                sources=sources,
                source_title=first.get("title", ""),
                source_url=first.get("url", ""),
                reliability="B",
                notes="",
            )
        )
    return items


def build_factpack(session, idea_spec: IdeaSpec) -> FactPack:
    tags = [idea_spec.domain, idea_spec.object_title.lower()]
    cards = crud.get_fact_cards(session, idea_spec.domain, tags, limit=50)
    random.shuffle(cards)
    facts: List[FactItem] = []
    for card in cards:
        facts.extend(_factcard_to_items(card))
        if len(facts) >= 10:
            break
    if len(facts) < 6:
        raise ValueError("FACTS_MISSING")
    return FactPack(facts=facts[:10])


def _fact_ids(factpack: Optional[FactPack]) -> List[str]:
    if not factpack or not factpack.facts:
        return []
    return [fact.id for fact in factpack.facts]


def _fact_sources(factpack: Optional[FactPack]) -> List[str]:
    if not factpack or not factpack.facts:
        return []
    sources = []
    for fact in factpack.facts:
        for source in fact.sources or []:
            if isinstance(source, dict):
                title = source.get("title")
            else:
                title = getattr(source, "title", None)
            if title:
                sources.append(title)
    return sources


def _fact_claims(factpack: Optional[FactPack]) -> List[str]:
    if not factpack or not factpack.facts:
        return []
    return [fact.claim for fact in factpack.facts]


def _script_prompt(idea_spec: IdeaSpec, factpack: FactPack, series, no_facts: bool) -> dict:
    payload = {
        "idea": idea_spec.model_dump(),
        "facts": [fact.model_dump() for fact in factpack.facts] if not no_facts else [],
        "allowed_sources": _fact_sources(factpack) if not no_facts else [],
        "allowed_claims": _fact_claims(factpack) if not no_facts else [],
        "series_preamble": _series_prompt(series),
        "fact_mode": "no_facts" if no_facts else "factpack",
        "rules": {
            "language": "ru",
            "voiceover_words": "70-110",
            "captions_lines": "6-8",
            "caption_max_len": 42,
            "caption_source_required": True,
            "no_antithesis": True,
            "no_abstract_agents": True,
            "no_semicolons": True,
            "no_long_dash": True,
            "no_fake_facts": True,
            "claims_used_required": True,
        },
    }
    if no_facts:
        payload["rules"]["no_specifics"] = True
    return payload


def _has_disallowed_specifics(text: str) -> bool:
    if any(char.isdigit() for char in text or ""):
        return True
    if "«" in text or "»" in text:
        return True
    for marker in ["глава", "страница", "том", "г."]:
        if marker in text.lower():
            return True
    return False


def generate_script_spec(
    session,
    job_id,
    idea_spec: IdeaSpec,
    factpack: FactPack,
    series,
) -> Tuple[ScriptSpec, dict, dict, bool]:
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        voiceover = (
            f"Перед нами {idea_spec.object_title}. "
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
            hook=f"Почему {idea_spec.object_title} работает сильнее, чем кажется?",
            voiceover_text=voiceover,
            on_screen_captions=[
                "Объект",
                "Деталь",
                "Материал",
                "Ритм",
                "Внимание",
                "Вывод",
                "Источник: архив",
            ],
            cta="Хочешь больше разборов - подпишись.",
            object_title=idea_spec.object_title,
            fact_ids_used=[],
            on_screen_sources=[],
            claims_used=[],
        )
        style_payload = {
            "issues": lint_script(script.hook, script.voiceover_text, script.on_screen_captions, script.cta)
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

    if factpack is None:
        factpack = FactPack(facts=[])
    no_facts = not factpack.facts
    fact_ids = _fact_ids(factpack)

    def _validate(script: ScriptSpec) -> Tuple[List[str], List[str], List[str]]:
        issues = []
        validation_issues = []
        if not validate_voiceover(script.voiceover_text):
            validation_issues.append("voiceover_text должен быть 70-110 слов")
        if not (6 <= len(script.on_screen_captions) <= 8):
            validation_issues.append("on_screen_captions должен быть 6-8 строк")
        ok_len, caption_issues = validate_captions_length(script.on_screen_captions)
        if not ok_len:
            validation_issues.extend(caption_issues)
        if not script.on_screen_captions or "источник" not in script.on_screen_captions[-1].lower():
            validation_issues.append("последний caption должен содержать слово 'источник'")
        issues.extend(validation_issues)
        if no_facts:
            if script.fact_ids_used:
                validation_issues.append("fact_ids_used должен быть пустым без FactPack")
            if script.claims_used:
                validation_issues.append("claims_used должен быть пустым без FactPack")
            if script.on_screen_sources:
                validation_issues.append("on_screen_sources должен быть пустым без FactPack")
            if _has_disallowed_specifics(script.voiceover_text + " " + script.hook):
                validation_issues.append("конкретика запрещена без FactPack")
            issues.extend(validation_issues)
        else:
            if not set(script.fact_ids_used).issubset(set(fact_ids)):
                validation_issues.append("fact_ids_used содержит неизвестные id")
            if not script.fact_ids_used:
                validation_issues.append("fact_ids_used должен быть заполнен")
            fact_claims = _fact_claims(factpack)
            if not script.claims_used:
                validation_issues.append("claims_used должен быть заполнен")
            if not set(script.claims_used).issubset(set(fact_claims)):
                validation_issues.append("claims_used содержит неизвестные claims")
            if not script.on_screen_sources:
                validation_issues.append("on_screen_sources должны быть заполнены")
            elif len(script.on_screen_sources) > 2:
                validation_issues.append("on_screen_sources должен быть 1-2 строки")
            else:
                allowed_sources = _fact_sources(factpack)
                if not any(source in " ".join(allowed_sources) for source in script.on_screen_sources):
                    validation_issues.append("on_screen_sources не соответствуют FactPack")
            issues.extend(validation_issues)
        style_issues = lint_script(
            script.hook,
            script.voiceover_text,
            script.on_screen_captions,
            script.cta,
        )
        issues.extend(style_issues)
        return issues, style_issues, validation_issues

    def _judge(script: ScriptSpec, issues: List[str]) -> JudgeVerdict:
        judge_system = "Ты Judge. Оцени текст по критериям, верни verdict JSON."
        judge_user = {
            "script": script.model_dump(),
            "issues": issues,
            "idea": idea_spec.model_dump(),
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
        return JudgeVerdict.model_validate(verdict_data)

    def _writer_pass(must_fix: Optional[List[str]] = None) -> ScriptSpec:
        writer_system = (
            "Ты Writer. Напиши ScriptSpec для вертикального видео. "
            "Никаких нейрошаблонов, никаких антитез, живой русский. "
            "Конкретная деталь объекта обязательна. "
            "Заполни claims_used тезисами из FactPack. "
            "Длина voiceover_text строго 70-110 слов, если больше - сокращай. "
            "claims_used должен использовать только значения из allowed_claims. "
            "on_screen_sources должен быть 1-2 строки и содержать только значения из allowed_sources."
        )
        writer_user = _script_prompt(idea_spec, factpack, series, no_facts=no_facts)
        if not no_facts:
            writer_user["fact_ids_required"] = fact_ids
        if must_fix:
            writer_user["must_fix"] = must_fix
        if no_facts:
            writer_user["must_avoid"] = ["даты", "имена", "цитаты", "книги и главы", "цифры"]
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
        return ScriptSpec.model_validate(script_data)

    def _editor_pass(script: ScriptSpec, must_fix: Optional[List[str]] = None) -> ScriptSpec:
        editor_system = (
            "Ты Editor. Отредактируй ScriptSpec: лучше ритм, чище стиль, без штампов. "
            "Не добавляй новых фактов. Не используй антитезы. "
            "Длина voiceover_text строго 70-110 слов, если больше - сокращай. "
            "Сохраняй claims_used только из allowed_claims и on_screen_sources только из allowed_sources."
        )
        editor_user = {
            "script": script.model_dump(),
            "rules": _script_prompt(idea_spec, factpack, series, no_facts=no_facts)["rules"],
            "allowed_sources": _fact_sources(factpack) if not no_facts else [],
            "allowed_claims": _fact_claims(factpack) if not no_facts else [],
            "must_fix": must_fix or [],
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
        return ScriptSpec.model_validate(edited_data)

    # First pass
    script = _editor_pass(_writer_pass())
    issues, style_issues, validation_issues = _validate(script)
    verdict = _judge(script, issues)
    must_fix = list(dict.fromkeys(issues + verdict.must_fix))
    if verdict.pass_ and not must_fix:
        return (
            script,
            verdict.model_dump(by_alias=True),
            {"issues": style_issues, "validation_issues": validation_issues},
            False,
        )

    # Second pass with must_fix
    script = _editor_pass(_writer_pass(must_fix), must_fix=must_fix)
    issues, style_issues, validation_issues = _validate(script)
    verdict = _judge(script, issues)
    must_fix = list(dict.fromkeys(issues + verdict.must_fix))
    if verdict.pass_ and not must_fix:
        return (
            script,
            verdict.model_dump(by_alias=True),
            {"issues": style_issues, "validation_issues": validation_issues},
            False,
        )

    if validation_issues == ["voiceover_text должен быть 70-110 слов"]:
        trimmed = trim_voiceover(script.voiceover_text)
        if trimmed != script.voiceover_text:
            script.voiceover_text = trimmed
            issues, style_issues, validation_issues = _validate(script)
            verdict = _judge(script, issues)
            must_fix = list(dict.fromkeys(issues + verdict.must_fix))
            if verdict.pass_ and not must_fix:
                return (
                    script,
                    verdict.model_dump(by_alias=True),
                    {"issues": style_issues, "validation_issues": validation_issues},
                    False,
                )

    if validation_issues and not no_facts:
        allowed_sources = _fact_sources(factpack)
        allowed_claims_map = {fact.id: fact.claim for fact in factpack.facts}
        if allowed_sources:
            script.on_screen_sources = allowed_sources[:2]
        if script.fact_ids_used:
            script.claims_used = [
                allowed_claims_map[fid]
                for fid in script.fact_ids_used
                if fid in allowed_claims_map
            ]
        issues, style_issues, validation_issues = _validate(script)
        verdict = _judge(script, issues)
        must_fix = list(dict.fromkeys(issues + verdict.must_fix))
        if verdict.pass_ and not must_fix:
            return (
                script,
                verdict.model_dump(by_alias=True),
                {"issues": style_issues, "validation_issues": validation_issues},
                False,
            )

    return (
        script,
        verdict.model_dump(by_alias=True),
        {"issues": must_fix, "validation_issues": validation_issues},
        True,
    )


def generate_storyboard(session, job_id, idea_spec: IdeaSpec, script: ScriptSpec) -> Storyboard:
    client = LLMClient(job_id=job_id)
    if not client.is_enabled():
        return default_storyboard(idea_spec.object_title)

    system = "Ты Storyboard. Сформируй 3 сцены, 8 сек каждая, вертикальный формат."
    user = {
        "idea": idea_spec.model_dump(),
        "script": script.model_dump(),
        "rules": ["3 сцены", "duration_sec=8", "учитывай объект и ключевую деталь"],
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
