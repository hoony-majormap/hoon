"""게이트가 '통과시켜야 할 것은 통과, 막아야 할 것은 막는지' 검사 (DoD §9.4)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from mm_insta.gates.text_gates import g1_facts, g2_similarity, g3_tone_limits
from mm_insta.models import FactSheet, WriterOutput, resolve, to_script
from mm_insta.sources.local import load_topic

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ["trend_2028_rules", "skku_2027_jungsi"]


def load(name: str):
    topic = load_topic(ROOT / "fixtures/topics" / f"{name}.json")
    demo = ROOT / "fixtures/demo" / name
    facts = FactSheet.model_validate_json((demo / "facts.json").read_text()).facts
    draft = WriterOutput.model_validate_json((demo / "writer.json").read_text())
    return topic, to_script(topic, facts, draft, "MON · 입시 뉴스 브리핑")


@pytest.mark.parametrize("name", DEMOS)
def test_demo_fixtures_pass_all_text_gates(name):
    topic, script = load(name)
    for gate in (g1_facts(script, topic), g2_similarity(script, topic), g3_tone_limits(script)):
        assert gate["pass"], gate["violations"]


def slide(script, layout):
    return next(s for s in script["slides"] if s["layout"] == layout)


def test_g1_blocks_typed_number():
    topic, script = load("trend_2028_rules")
    slide(script, "big_number")["line"] = "10명 중 9명은 수시로 뽑아요"
    r = g1_facts(script, topic)
    assert not r["pass"] and any("숫자를 직접 씀" in v for v in r["violations"])


def test_g1_blocks_unknown_fact_ref():
    topic, script = load("trend_2028_rules")
    slide(script, "detail")["change"]["after"] = "{f99}"
    r = g1_facts(script, topic)
    assert any("없는 팩트 참조" in v for v in r["violations"])


def test_g1_blocks_hallucinated_fact_value():
    topic, script = load("trend_2028_rules")
    script["facts"][0]["value"] = "81.5%"  # 원문에 없는 숫자
    r = g1_facts(script, topic)
    assert any("소재 원문에 없음" in v for v in r["violations"])


def test_g1_allows_grade_names_and_warns_on_derived():
    topic, script = load("trend_2028_rules")
    r = g1_facts(script, topic)
    assert r["pass"]
    assert any("바꿔 말하기" in w for w in r["warnings"])  # f3 '10명 중 8명'


def test_g1_hashtag_number_must_exist_in_facts():
    topic, script = load("trend_2028_rules")
    script["hashtags"][3] = "#2030입시"
    assert not g1_facts(script, topic)["pass"]


def test_g2_blocks_copied_sentence():
    topic, script = load("skku_2027_jungsi")
    script["caption"] = topic.key_points[1]
    r = g2_similarity(script, topic)
    assert not r["pass"] and r["max_overlap_ratio"] > 0


def test_g3_blocks_length_banned_and_structure():
    topic, script = load("trend_2028_rules")
    s = copy.deepcopy(script)
    slide(s, "hook")["headline"][0] = "수능 한 방으로 역전하는 시대"
    slide(s, "action")["steps"].pop()
    slide(s, "cta")["dialogue"] = [{"who": "may", "text": "이거 모르면 망한다"}] * 3
    v = g3_tone_limits(s)["violations"]
    assert any("headline[0]" in m for m in v)
    assert any("steps" in m and "≠ 3" in m for m in v)
    assert any("금칙어" in m for m in v)
    assert any("말풍선 3개" in m for m in v)


def test_resolve_substitutes_fact_values():
    facts = {"f1": {"value": "80.8%"}}
    assert resolve("수시 {f1}, 없는 {f2}", facts) == "수시 80.8%, 없는 {f2}"


def test_writer_schema_is_structured_output_compatible():
    """작가·팩트 스키마가 SDK의 구조화 출력 변환을 통과하는지 (API 키 없이 확인)."""
    from anthropic import transform_schema

    for model in (WriterOutput, FactSheet):
        schema = transform_schema(model)
        assert json.dumps(schema)
