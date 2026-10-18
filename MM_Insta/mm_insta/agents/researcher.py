"""①-b 리서처 — 캐릿 소재에 캐릿 밖 근거를 붙인다 (Claude 웹 검색 서버 도구).

캐릿 기사는 출발점일 뿐 그대로 올리지 않는다. 같은 주제를 공공기관·언론·공식 발표로 다시 확인하고,
고등학생에게 쓸모 있는 사실(배경 지식·주의할 점·관련 학과)을 덧붙인다.
검색 결과에 실제로 나온 URL만 남기고, 캐릿 링크는 리서치로 치지 않는다 (G5가 다시 검사).
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .. import llm
from ..config import CAREET_DOMAINS, MODEL_RESEARCH, WEB_SEARCH_TOOL
from ..models import ResearchNote, Topic
from . import prompts


class ResearchPack(BaseModel):
    notes: list[ResearchNote] = Field(description="3~8개, 캐릿이 아닌 출처만")
    angle: str = Field(description="캐릿 유행과 리서치를 섞어 고등학생에게 유익하게 만드는 각도 한 줄")
    search_terms: list[str] = Field(description="메이저맵 콘텐츠를 찾을 검색어 2~4개 (학과명·분야·핵심 개념)")


def _norm(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def _search(topic: Topic) -> tuple[str, set[str]]:
    """웹 검색으로 조사 → (조사 메모, 검색 결과에 실제로 나온 URL)."""
    user = {"role": "user", "content": prompts.research_user(topic)}
    content, texts, urls = [], [], set()
    for _ in range(4):  # 서버 도구가 길어지면 pause_turn — 받은 그대로 돌려보내 이어 쓰게 한다
        resp = llm.client().messages.create(
            model=MODEL_RESEARCH,
            max_tokens=8000,
            system=prompts.RESEARCH_SYSTEM,
            messages=[user, {"role": "assistant", "content": content}] if content else [user],
            tools=[{"type": WEB_SEARCH_TOOL, "name": "web_search", "max_uses": 8}],
        )
        if resp.stop_reason == "refusal":
            raise llm.LLMRefusal(f"{MODEL_RESEARCH} 리서치 거절")
        for block in resp.content:
            if block.type == "web_search_tool_result" and isinstance(block.content, list):
                urls.update(_norm(r.url) for r in block.content)
            elif block.type == "text":
                texts.append(block.text)
                urls.update(_norm(c.url) for c in block.citations or [] if getattr(c, "url", None))
        content += resp.content
        if resp.stop_reason != "pause_turn":
            break
    return "\n".join(texts), urls


def research(topic: Topic) -> ResearchPack:
    memo, urls = _search(topic)
    pack = llm.structured(
        model=MODEL_RESEARCH,
        system=prompts.RESEARCH_PACK_SYSTEM,
        user=prompts.research_pack_user(topic, memo, sorted(urls)),
        schema=ResearchPack,
        effort="low",
    )
    pack.notes = [n for n in pack.notes
                  if _norm(n.url) in urls and not any(d in n.url for d in CAREET_DOMAINS)]
    return pack
