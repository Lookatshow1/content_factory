from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ObjectSpec(BaseModel):
    object_type: str = Field(..., description="philosophy_text|artwork|marketing_case|historical_episode")
    object_title: str
    object_context: str
    intended_takeaway: str
    angle: str
    constraints: List[str]


class FactItem(BaseModel):
    id: str
    claim: str
    source_title: str
    source_author: str = ""
    source_year: Optional[int] = None
    source_locator: str
    source_url: str
    evidence_snippet: str
    reliability: str
    notes: str


class FactPack(BaseModel):
    facts: List[FactItem]


class ScriptSpec(BaseModel):
    hook: str
    voiceover_text: str
    on_screen_captions: List[str]
    cta: str
    object_title: str
    fact_ids_used: List[str]
    on_screen_sources: List[str]


class StoryboardScene(BaseModel):
    prompt: str
    duration_sec: int
    style: str
    negative_prompt: str


class Storyboard(BaseModel):
    scenes: List[StoryboardScene]


class JudgeVerdict(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    score_total: int
    originality: int
    clarity: int
    factual_discipline: int
    style: int
    must_fix: List[str]
    pass_: bool = Field(..., alias="pass")
