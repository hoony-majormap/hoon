"""노션에서 오늘의 소재 1건을 고른다.

- 입시 (월·수·금): ① 「최근 입시 트렌드」 리포트의 주제 섹션 → 다 쓰면 ② 베리타스알파 기사 아카이브 DB
- 트렌드 (화·목): 「캐릿 아티클 아카이브」 DB (유행중·유행예감 우선, 유행지남 제외)

필요 환경변수: NOTION_TOKEN (아래 페이지·DB가 이 통합(integration)에 공유돼 있어야 함)
"""
from __future__ import annotations

import os
import re

import requests

from ..models import Topic

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# 2026-10-17_최근 입시 트렌드 — 2027 수능·의대·2028 개편과 메이저맵 시사점
REPORT_PAGE_ID = os.environ.get("NOTION_REPORT_PAGE_ID", "3fc6af6c-8bcc-816d-a0c6-c44ad8f126aa")
# 📚 베리타스알파 구독자 기사 아카이브 (2026.07.17~10.17)
ARCHIVE_DB_ID = os.environ.get("NOTION_ARCHIVE_DB_ID", "5a9f093b-a89f-4fc8-8de2-432e6fbb05dc")
# 캐릿 아티클 아카이브 (2024.10~2026.10)
CAREET_DB_ID = os.environ.get("NOTION_CAREET_DB_ID", "05d3c1f9-2bb8-4780-8357-75049e775a03")

# 고1·고2 관련 키워드
ADMISSIONS_KEYWORDS = ["2028 개편", "학생부 정성평가", "반도체·AI·첨단", "무전공·자유전공", "수능최저", "학종", "사탐런 대응"]
# 리포트에서 카드뉴스로 쓸 주제 섹션 ('1. …' ~ '6. …', 일정·시사점·참고자료 제외)
REPORT_SECTION = re.compile(r"^([1-6])\.\s*(.+)$")
CAREET_SKIP = {"유행지남"}
CAREET_PRIORITY = {"유행중": 0, "유행예감": 1, "일반": 2}


def _headers() -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN이 없습니다. .env 또는 GitHub Secrets에 설정하세요.")
    return {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}


def _plain(rich: list[dict]) -> str:
    return "".join(r.get("plain_text", "") for r in rich or [])


def _prop(props: dict, name: str):
    p = props.get(name) or {}
    kind = p.get("type")
    if kind == "title":
        return _plain(p["title"])
    if kind == "rich_text":
        return _plain(p["rich_text"])
    if kind == "url":
        return p.get("url") or ""
    if kind == "date":
        return (p.get("date") or {}).get("start") or ""
    if kind == "select":
        return (p.get("select") or {}).get("name") or ""
    if kind == "multi_select":
        return [o["name"] for o in p.get("multi_select") or []]
    if kind == "number":
        return p.get("number")
    return None


def _children(block_id: str) -> list[dict]:
    out, cursor = [], None
    while True:
        params = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        r = requests.get(f"{API}/blocks/{block_id}/children", headers=_headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        out += data["results"]
        if not data.get("has_more"):
            return out
        cursor = data["next_cursor"]


def _query(db_id: str, body: dict) -> list[dict]:
    out, cursor = [], None
    while True:
        payload = {**body, "page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        r = requests.post(f"{API}/databases/{db_id}/query", headers=_headers(), json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        out += data["results"]
        if not data.get("has_more") or len(out) >= 300:
            return out
        cursor = data["next_cursor"]


def _bullets(text: str) -> list[str]:
    return [b.strip(" •-\t") for b in re.split(r"\n|<br>", text or "") if b.strip(" •-\t")]


def _same(a: str, b: str) -> bool:
    return a.replace("-", "") == b.replace("-", "")


# ── 입시: 리포트 섹션 ───────────────────────────────────────────
def report_topics() -> list[Topic]:
    topics, current = [], None
    for block in _children(REPORT_PAGE_ID):
        kind = block["type"]
        if kind == "heading_2":
            current = None
            m = REPORT_SECTION.match(_plain(block[kind]["rich_text"]).strip())
            if m:
                current = Topic(
                    id=f"report:{REPORT_PAGE_ID}#{m.group(1)}",
                    track="admissions",
                    title=m.group(2).strip(),
                    source_name="메이저맵 입시 트렌드 리포트",
                    source_type="트렌드 리포트",
                    url="",
                    published="2026-10-17",
                    keywords=["트렌드 리포트"],
                )
                topics.append(current)
        elif kind == "bulleted_list_item" and current is not None:
            current.key_points.append(_plain(block[kind]["rich_text"]).strip())
    for t in topics:
        t.summary = t.key_points[0] if t.key_points else t.title
        t.evidence = [f"{t.title} = 베리타스알파·대교협·언론 보도 종합(메이저맵 트렌드 리포트), {t.published}"]
    return topics


# ── 입시: 베리타스 아카이브 ─────────────────────────────────────
def archive_topic(page_id: str) -> Topic:
    r = requests.get(f"{API}/pages/{page_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    page = r.json()
    props = page["properties"]
    sections: dict[str, list[str]] = {}
    current = None
    for block in _children(page_id):
        kind = block["type"]
        if kind.startswith("heading_"):
            current = _plain(block[kind]["rich_text"]).strip()
            sections.setdefault(current, [])
        elif kind in ("bulleted_list_item", "numbered_list_item", "paragraph") and current:
            text = _plain(block[kind]["rich_text"]).strip()
            if text:
                sections[current].append(text)
    title, published = _prop(props, "기사 제목"), _prop(props, "발행일")
    return Topic(
        id=page["id"],
        track="admissions",
        title=title,
        url=_prop(props, "링크"),
        published=published,
        summary=_prop(props, "핵심 요약"),
        keywords=_prop(props, "키워드") or [],
        key_points=sections.get("핵심 내용", []),
        check_points=sections.get("체크 포인트", []),
        evidence=[f"{title} = 베리타스알파, {published}"],
    )


def archive_candidates() -> list[str]:
    body = {
        "filter": {"or": [{"property": "키워드", "multi_select": {"contains": k}} for k in ADMISSIONS_KEYWORDS]},
        "sorts": [{"property": "발행일", "direction": "descending"}],
    }
    return [p["id"] for p in _query(ARCHIVE_DB_ID, body)]


# ── 트렌드: 캐릿 아카이브 ───────────────────────────────────────
def careet_topic(page: dict) -> Topic:
    props = page["properties"]
    title, published = _prop(props, "제목"), _prop(props, "날짜")
    points = _bullets(_prop(props, "요약"))
    return Topic(
        id=page["id"],
        track="trend",
        title=title,
        source_name="캐릿",
        source_type="캐릿 아카이브",
        url=_prop(props, "링크"),
        published=published,
        summary=points[0] if points else title,
        key_points=[p for p in points if not p.startswith("시사점")],
        keywords=[k for k in (_prop(props, "시리즈"), _prop(props, "분류")) if k],
        evidence=[f"{title} = 캐릿, {published}"],
    )


def careet_candidates() -> list[dict]:
    pages = _query(CAREET_DB_ID, {"sorts": [{"property": "날짜", "direction": "descending"}]})
    pages = [p for p in pages if _prop(p["properties"], "분류") not in CAREET_SKIP]
    # 최근 60건 안에서 유행중 → 유행예감 → 일반 순, 같은 등급이면 최신순
    recent = pages[:60]
    return sorted(recent, key=lambda p: CAREET_PRIORITY.get(_prop(p["properties"], "분류"), 3))


# ── 선택 ────────────────────────────────────────────────────────
def pick(track: str, used: set[str]) -> Topic:
    is_used = lambda tid: any(_same(tid, u) for u in used)  # noqa: E731
    if track == "trend":
        for page in careet_candidates():
            if not is_used(page["id"]):
                return careet_topic(page)
        raise RuntimeError("캐릿 아카이브에 아직 안 쓴 소재가 없습니다.")
    for t in report_topics():
        if not is_used(t.id) and t.key_points:
            return t
    for pid in archive_candidates():
        if not is_used(pid):
            return archive_topic(pid)
    raise RuntimeError("입시 소재(리포트·아카이브)를 모두 사용했습니다.")


def fetch(page_id: str, track: str) -> Topic:
    """특정 페이지를 소재로 지정할 때."""
    if track == "trend":
        r = requests.get(f"{API}/pages/{page_id}", headers=_headers(), timeout=30)
        r.raise_for_status()
        return careet_topic(r.json())
    return archive_topic(page_id)
