"""LLM 호출부 배선 검사 — 실제 API 대신 가짜 클라이언트로 요청 형태와 재작성 루프를 확인."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from mm_insta import llm, pipeline
from mm_insta.models import FactSheet, WriterOutput

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "fixtures/demo/trend_2028_rules"


class FakeMessages:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn", stop_details=None, parsed_output=self.outputs.pop(0))


def fake_client(monkeypatch, outputs):
    messages = FakeMessages(outputs)
    monkeypatch.setattr(llm, "_client", SimpleNamespace(beta=SimpleNamespace(messages=messages)))
    return messages


def test_request_shape(monkeypatch):
    facts = FactSheet.model_validate_json((DEMO / "facts.json").read_text())
    messages = fake_client(monkeypatch, [facts])
    out = llm.structured(model="claude-sonnet-5-5", system="SYS", user="U", schema=FactSheet)
    call = messages.calls[0]
    assert out is facts
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["output_format"] is FactSheet
    assert call["fallbacks"] == "default" and llm.FALLBACK_BETA in call["betas"]


def test_rewrite_once_with_gate_feedback(monkeypatch, tmp_path):
    facts = FactSheet.model_validate_json((DEMO / "facts.json").read_text())
    good = WriterOutput.model_validate_json((DEMO / "writer.json").read_text())
    bad = good.model_copy(deep=True)
    bad.big_number.line = "10명 중 9명은 수시로 뽑아요"  # G1 위반
    messages = fake_client(monkeypatch, [facts, bad, good])
    monkeypatch.setattr("mm_insta.render.renderer.render", lambda script, out: ([], {"gate": "G4", "pass": True, "violations": [], "warnings": []}))

    code = pipeline.main([
        "--topic-file", str(ROOT / "fixtures/topics/trend_2028_rules.json"),
        "--date", "2026-10-19",
        "--out", str(tmp_path),
    ])
    report = json.loads((tmp_path / "gate_report.json").read_text())
    assert code == 0
    assert [a["attempt"] for a in report["attempts"]] == [1, 2]
    retry_prompt = messages.calls[2]["messages"][0]["content"]
    assert "자동 검수에서 탈락" in retry_prompt and "숫자를 직접 씀" in retry_prompt
