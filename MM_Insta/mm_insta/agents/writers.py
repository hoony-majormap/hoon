"""② 팩트 추출기 · ③ 작가 May·Polar — LLM 서브에이전트 (트랙별 프롬프트·스키마)."""
from __future__ import annotations

from .. import llm
from ..config import MODEL_FACTS, MODEL_WRITER
from ..models import Fact, FactSheet, Topic, TrendWriterOutput, WriterOutput
from . import prompts


def extract_facts(topic: Topic) -> list[Fact]:
    trend = topic.track == "trend"
    sheet = llm.structured(
        model=MODEL_FACTS,
        system=prompts.FACTS_TREND_SYSTEM if trend else prompts.FACTS_SYSTEM,
        user=prompts.facts_user(topic),
        schema=FactSheet,
        effort="medium",
    )
    if not sheet.facts and not trend:  # 입시 편은 수치 없이 만들지 않는다
        raise RuntimeError("수치 근거가 비어 있습니다 → 다른 소재로 교체 필요")
    return sheet.facts


def write_script(
    topic: Topic, facts: list[Fact], kicker: str, next_label: str, feedback: list[str] | None = None
) -> WriterOutput | TrendWriterOutput:
    trend = topic.track == "trend"
    return llm.structured(
        model=MODEL_WRITER,
        system=prompts.WRITER_TREND_SYSTEM if trend else prompts.WRITER_SYSTEM,
        user=prompts.writer_user(topic, facts, kicker, next_label, feedback),
        schema=TrendWriterOutput if trend else WriterOutput,
        effort="high",
    )
