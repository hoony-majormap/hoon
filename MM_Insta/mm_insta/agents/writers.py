"""② 팩트 추출기 · ③ 작가 May·Polar — LLM 서브에이전트."""
from __future__ import annotations

from .. import llm
from ..config import MODEL_FACTS, MODEL_WRITER
from ..models import Fact, FactSheet, Topic, WriterOutput
from . import prompts


def extract_facts(topic: Topic) -> list[Fact]:
    sheet = llm.structured(
        model=MODEL_FACTS,
        system=prompts.FACTS_SYSTEM,
        user=prompts.facts_user(topic),
        schema=FactSheet,
        effort="medium",
    )
    facts = sheet.facts
    if not facts:
        raise RuntimeError("수치 근거가 비어 있습니다 → 소재 '보류' 대상")
    return facts


def write_script(
    topic: Topic, facts: list[Fact], kicker: str, next_teaser: str, feedback: list[str] | None = None
) -> WriterOutput:
    return llm.structured(
        model=MODEL_WRITER,
        system=prompts.WRITER_SYSTEM,
        user=prompts.writer_user(topic, facts, kicker, next_teaser, feedback),
        schema=WriterOutput,
        effort="high",
    )
