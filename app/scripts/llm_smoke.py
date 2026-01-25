import json
import sys

from app.services.llm import LLMClient
from app.services.llm.schemas import ScriptSpec
from app.settings import settings


def main() -> int:
    client = LLMClient()
    if not client.is_enabled():
        print("LLM not configured")
        return 1

    system = (
        "Ты Writer. Верни только JSON строго по схеме ScriptSpec. "
        "Русский язык, 70-110 слов в voiceover_text, 6-8 строк captions."
    )
    user = {
        "idea": {
            "object_title": "Старая вывеска на фасаде",
            "object_context": "Короткий контекст без дат и имен.",
            "angle": "Разбор через деталь",
        },
        "facts": [
            {
                "id": "fact-1",
                "claim": "Вывеска выполнена в контрастной цветовой схеме.",
                "source_title": "Архив городских вывесок",
                "source_url": "https://example.com/source-1",
            },
            {
                "id": "fact-2",
                "claim": "Композиция вывески построена на вертикальном ритме.",
                "source_title": "Каталог визуальных решений",
                "source_url": "https://example.com/source-2",
            },
        ],
        "fact_ids_required": ["fact-1", "fact-2"],
        "rules": {
            "language": "ru",
            "voiceover_words": "70-110",
            "captions_lines": "6-8",
            "caption_max_len": 42,
            "caption_source_required": True,
            "no_antithesis": True,
            "no_abstract_agents": True,
        },
    }

    data = client.generate_json(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        schema=ScriptSpec.model_json_schema(),
        validator=ScriptSpec,
        model=settings.LLM_MODEL_WRITER or None,
        repair_model=settings.LLM_MODEL_EDITOR or None,
    )
    script = ScriptSpec.model_validate(data)
    print(f"ok hook={script.hook}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
