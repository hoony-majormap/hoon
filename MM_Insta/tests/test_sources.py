"""새 소재 경로 — 캐릿 마이크로 트렌드 · 메이저맵 콘텐츠 DB · 리서처 · 트렌드 소재 고르기 (네트워크 없이)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from mm_insta import llm, pipeline
from mm_insta.agents import researcher
from mm_insta.models import ResearchNote, Topic
from mm_insta.sources import notion


def rich(text):
    return [{"plain_text": text}]


def micro_page(pid="p1", title="포켓몬 화석박물관"):
    return {"id": pid, "properties": {
        "트렌드": {"type": "title", "title": rich(title)},
        "요약": {"type": "rich_text", "rich_text": rich("• 12월 국립광주과학관 전시\n• 엑스에서 2천 회 재게시")},
        "링크": {"type": "url", "url": "https://x.com/pokemonkrmkt/status/1"},
        "날짜": {"type": "date", "date": {"start": "2026-10-14"}},
        "출처": {"type": "multi_select", "multi_select": [{"name": "엑스"}]},
    }}


def mm_page(cid, title, fmt="리스트·추천형"):
    return {"id": f"mm{cid}", "properties": {
        "콘텐츠 ID": {"type": "number", "number": cid},
        "제목": {"type": "title", "title": rich(title)},
        "한줄요약": {"type": "rich_text", "rich_text": rich("요약")},
        "카테고리": {"type": "select", "select": {"name": "학과탐구"}},
        "콘텐츠 형식": {"type": "select", "select": {"name": fmt}},
        "관련 학과·직업": {"type": "rich_text", "rich_text": rich("고생물학자")},
        "조회수": {"type": "number", "number": 1173},
    }}


def test_micro_trend_page_becomes_careet_topic():
    t = notion.careet_page_topic(micro_page())
    assert t.track == "trend" and t.source_name == "캐릿" and t.source_type == "캐릿 마이크로 트렌드"
    assert t.key_points == ["12월 국립광주과학관 전시", "엑스에서 2천 회 재게시"]
    assert t.published == "2026-10-14" and t.keywords == ["엑스"]


def test_related_contents_links_majormap_and_skips_notices(monkeypatch):
    seen = {}

    def fake_query(db_id, body):
        seen["db"], seen["body"] = db_id, body
        return [mm_page(1, "이벤트 안내", fmt="이벤트·공지"), mm_page(533, "지구과학Ⅰ 연계도서"), mm_page(240, "지구과학교육과")]

    monkeypatch.setattr(notion, "_query", fake_query)
    out = notion.related_contents(["고생물학", "고생물학", " 화석 "], limit=2)
    assert seen["db"] == notion.MM_CONTENT_DB_ID
    terms = {f[k]["contains"] for f in seen["body"]["filter"]["or"] for k in f if k != "property"}
    assert terms == {"고생물학", "화석"}  # 중복·공백 정리
    assert [r.id for r in out] == [533, 240]
    assert out[0].url == "https://majormap.net/content/533" and out[0].views == 1173


def test_related_contents_without_terms_does_not_query(monkeypatch):
    monkeypatch.setattr(notion, "_query", lambda *a: pytest.fail("쿼리하면 안 됨"))
    assert notion.related_contents([" "]) == []


# ── 리서처: 검색 결과에 실제로 나온 URL만, 캐릿은 빼고 ─────────────
class FakeMessages:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def block(**kw):
    return SimpleNamespace(**kw)


def test_researcher_keeps_only_searched_non_careet_urls(monkeypatch):
    search = block(type="web_search_tool_result", content=[
        block(url="https://zdnet.co.kr/view/?no=1"), block(url="https://www.careet.net/2001")])
    text = block(type="text", text="메모", citations=[block(url="https://www.khan.co.kr/article/1/")])
    messages = FakeMessages([
        SimpleNamespace(stop_reason="pause_turn", content=[search]),  # 서버 도구가 길어져 한 번 끊김
        SimpleNamespace(stop_reason="end_turn", content=[text]),
    ])
    monkeypatch.setattr(llm, "_client", SimpleNamespace(messages=messages))
    pack = researcher.ResearchPack(notes=[
        ResearchNote(claim="12월 중순 개막", source="ZDNet Korea", date="2026-10-14", url="https://zdnet.co.kr/view/?no=1"),
        ResearchNote(claim="천연기념물", source="경향신문", date="2026-09-04", url="https://www.khan.co.kr/article/1"),
        ResearchNote(claim="지어낸 출처", source="어딘가", date="", url="https://made-up.example/x"),
        ResearchNote(claim="캐릿 기사", source="캐릿", date="", url="https://www.careet.net/2001"),
    ], angle="게임 속 vs 진짜", search_terms=["고생물학"])
    captured = {}
    monkeypatch.setattr(llm, "structured", lambda **kw: captured.update(kw) or pack)

    out = researcher.research(Topic(id="t", title="포켓몬 화석박물관", track="trend"))
    assert [n.source for n in out.notes] == ["ZDNet Korea", "경향신문"]
    assert len(messages.calls) == 2 and messages.calls[1]["messages"][1]["role"] == "assistant"
    assert messages.calls[0]["tools"][0]["name"] == "web_search"
    assert "https://zdnet.co.kr/view/?no=1" in captured["user"]


# ── 트렌드 소재 고르기: 리서치가 안 붙으면 다음 후보 ──────────────
def test_trend_topic_skips_candidates_without_research(monkeypatch):
    a, b = Topic(id="a", title="A", track="trend"), Topic(id="b", title="B", track="trend")
    monkeypatch.setattr(notion, "candidates", lambda track, used: iter([a, b]))
    note = ResearchNote(claim="사실", source="경향신문", date="2026-10-17", url="https://khan.co.kr/1")
    packs = {"a": researcher.ResearchPack(notes=[], angle="", search_terms=[]),
             "b": researcher.ResearchPack(notes=[note], angle="각도", search_terms=["통계학과"])}
    monkeypatch.setattr(researcher, "research", lambda t: packs[t.id])
    asked = {}
    monkeypatch.setattr(notion, "related_contents", lambda terms, limit: asked.setdefault("terms", terms) and [])
    args = SimpleNamespace(topic_file=None, page=None, offline=None)

    topic = pipeline.load_topic(args, "trend", None)
    assert topic.id == "b" and topic.research == [note] and topic.angle == "각도"
    assert asked["terms"] == ["통계학과"]


def test_trend_topic_gives_up_when_nothing_researchable(monkeypatch):
    monkeypatch.setattr(notion, "candidates", lambda track, used: iter([Topic(id=str(i), title="x", track="trend") for i in range(5)]))
    monkeypatch.setattr(researcher, "research", lambda t: researcher.ResearchPack(notes=[], angle="", search_terms=[]))
    args = SimpleNamespace(topic_file=None, page=None, offline=None)
    with pytest.raises(RuntimeError, match="캐릿만으로는 게시하지 않음"):
        pipeline.load_topic(args, "trend", None)
