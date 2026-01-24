from typing import List

from app.services.llm.schemas import Storyboard


def default_storyboard(object_title: str) -> Storyboard:
    scenes = [
        {
            "prompt": f"Вертикальная сцена с упором на объект: {object_title}",
            "duration_sec": 8,
            "style": "минимализм, крупные планы, спокойный свет",
            "negative_prompt": "лишние люди, хаос, перегруз деталями",
        },
        {
            "prompt": f"Символические детали вокруг объекта: {object_title}",
            "duration_sec": 8,
            "style": "тихий музейный свет, фактурные материалы",
            "negative_prompt": "яркие кислотные цвета, шум",
        },
        {
            "prompt": f"Финальный кадр с акцентом на смысл: {object_title}",
            "duration_sec": 8,
            "style": "чистая композиция, ровный свет",
            "negative_prompt": "размытость, артефакты",
        },
    ]
    return Storyboard(scenes=scenes)
