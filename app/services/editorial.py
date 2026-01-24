from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.settings import settings


@lru_cache(maxsize=1)
def load_editorial_config() -> Dict[str, List[dict]]:
    path = Path(__file__).resolve().parents[2] / "config" / "editorial.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {"rubrics": []}


def list_rubrics() -> List[dict]:
    return load_editorial_config().get("rubrics", [])


def select_rubric(job_index: int) -> Optional[dict]:
    rubrics = list_rubrics()
    if not rubrics:
        return None
    if settings.SERIES_MODE == "random":
        import random

        return random.choice(rubrics)
    return rubrics[job_index % len(rubrics)]
