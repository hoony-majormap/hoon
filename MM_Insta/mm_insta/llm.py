"""Claude API 호출 공통부: 구조화 출력(Pydantic) + 시스템 프롬프트 캐싱 + 거절 시 서버측 폴백."""
from __future__ import annotations

import anthropic
from pydantic import BaseModel

FALLBACK_BETA = "server-side-fallback-2026-07-01"

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


class LLMRefusal(RuntimeError):
    pass


def structured(
    *,
    model: str,
    system: str,
    user: str,
    schema: type[BaseModel],
    effort: str = "medium",
    max_tokens: int = 16000,
) -> BaseModel:
    """system은 매일 같으므로 캐시하고, 소재·피드백처럼 바뀌는 내용은 user에만 넣는다."""
    response = client().beta.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        output_config={"effort": effort},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise LLMRefusal(f"{model} 거절: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"{model} 출력이 max_tokens({max_tokens})에서 잘렸습니다.")
    return response.parsed_output
