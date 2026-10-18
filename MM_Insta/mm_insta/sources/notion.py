"""노션에서 오늘의 소재 1건을 고른다.

- 입시 (월·수·금): ① 「최근 입시 트렌드」 리포트의 주제 섹션 → 다 쓰면 ② 베리타스알파 기사 아카이브 DB
- 트렌드 (화·목): 「캐릿 아티클 아카이브」 + 「캐릿 마이크로 트렌드 아카이브」 DB (최신순, 유행지남 제외)
  → 캐릿 소재는 그대로 쓰지 않는다: 파이프라인이 웹 리서치(agents/researcher.py)를 붙이고 G5가 섞였는지 검사
- 공통: 「메이저맵 콘텐츠 DB」에서 주제가 닿는 글을 찾아 캡션 '메이저맵에서 더 보기'에 붙인다

필요 환경변수: NOTION_TOKEN (아래 페이지·DB가 이 통합(integration)에 공유돼 있어야 함)
"""
from __future__ import annotations

import os
import re

import requests

from ..config import MM_CONTENT_URL, RELATED_MAX
from ..models import RelatedContent, Topic

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# 2026-10-17_최근 입시 트렌드 — 2027 수능·의대·2028 개편과 메이저맵 시사점
REPORT_PAGE_ID = os.environ.get("NOTION_REPORT_PAGE_ID", "3fc6af6c-8bcc-816d-a0c6-c44ad8f126aa")
# 📚 베리타스알파 구독자 기사 아카이브 (2026.07.17~10.17)
ARCHIVE_DB_ID = os.environ.get("NOTION_ARCHIVE_DB_ID", "5a9f093b-a89f-4fc8-8de2-432e6fbb05dc")
# 캐릿 아티클 아카이브 (2024.10~2026.10)
CAREET_DB_ID = os.environ.get("NOTION_CAREET_DB_ID", "05d3c1f9-2bb8-4780-8357-75049e775a03")
# 캐릿 마이크로 트렌드 아카이브 (2024.10~2026.10) — 한 줄짜리 유행 소식
MICRO_DB_ID = os.environ.get("NOTION_MICRO_DB_ID", "6c2655c3-6eae-461c-bebb-9dfaad1cdea9")
# 메이저맵 콘텐츠 DB (전체 817) — 그간 메이저맵에 올린 글
MM_CONTENT_DB_ID = os.environ.get("NOTION_MM_CONTENT_DB_ID", "47f32dec-3533-409f-a823-bc13da8b0578")

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


def micro_topic(page: dict) -> Topic:
    props = page["properties"]
    title, published = _prop(props, "트렌드"), _prop(props, "날짜")
    summary = _prop(props, "요약")
    return Topic(
        id=page["id"],
        track="trend",
        title=title,
        source_name="캐릿",
        source_type="캐릿 마이크로 트렌드",
        url=_prop(props, "링크"),
        published=published,
        summary=summary,
        key_points=_bullets(summary),
        keywords=_prop(props, "출처") or [],  # 퍼진 곳: 인스타그램·틱톡 …
        evidence=[f"{title} = 캐릿, {published}"],
    )


def careet_candidates() -> list[dict]:
    """아티클 + 마이크로 트렌드를 합쳐 최근 60건. 아티클은 유행중 → 유행예감 → 일반 순."""
    articles = _query(CAREET_DB_ID, {"sorts": [{"property": "날짜", "direction": "descending"}]})
    articles = [p for p in articles if _prop(p["properties"], "분류") not in CAREET_SKIP]
    micro = _query(MICRO_DB_ID, {"sorts": [{"property": "날짜", "direction": "descending"}]})
    pages = sorted(articles[:60] + micro[:60], key=lambda p: _date_of(p), reverse=True)[:60]
    return sorted(pages, key=lambda p: CAREET_PRIORITY.get(_prop(p["properties"], "분류"), 1))


def _date_of(page: dict) -> str:
    return _prop(page["properties"], "날짜") or ""


def careet_page_topic(page: dict) -> Topic:
    return micro_topic(page) if "트렌드" in page["properties"] else careet_topic(page)


# ── 메이저맵 콘텐츠 DB ──────────────────────────────────────────
def related_contents(terms: list[str], limit: int = RELATED_MAX) -> list[RelatedContent]:
    """검색어가 제목·한줄요약·해시태그·관련 학과에 닿는 메이저맵 글 — 조회수 높은 순."""
    terms = [t for t in dict.fromkeys(t.strip() for t in terms) if t][:6]
    if not terms:
        return []
    fields = [("제목", "title"), ("한줄요약", "rich_text"), ("해시태그", "rich_text"), ("관련 학과·직업", "rich_text")]
    body = {
        "filter": {"or": [{"property": f, kind: {"contains": t}} for t in terms for f, kind in fields]},
        "sorts": [{"property": "조회수", "direction": "descending"}],
    }
    out = []
    for page in _query(MM_CONTENT_DB_ID, body)[:limit * 5]:
        props = page["properties"]
        cid = _prop(props, "콘텐츠 ID")
        if cid is None or _prop(props, "콘텐츠 형식") == "이벤트·공지":
            continue
        out.append(RelatedContent(
            id=int(cid),
            title=_prop(props, "제목"),
            url=MM_CONTENT_URL.format(id=int(cid)),
            summary=_prop(props, "한줄요약") or "",
            category=_prop(props, "카테고리") or "",
            majors=_prop(props, "관련 학과·직업") or "",
            views=int(_prop(props, "조회수") or 0),
        ))
        if len(out) >= limit:
            break
    return out


# ── 선택 ────────────────────────────────────────────────────────
def candidates(track: str, used: set[str]):
    """안 쓴 소재를 우선순위대로 하나씩 (트렌드는 리서치가 안 붙으면 다음 후보로 넘어간다)."""
    is_used = lambda tid: any(_same(tid, u) for u in used)  # noqa: E731
    if track == "trend":
        for page in careet_candidates():
            if not is_used(page["id"]):
                yield careet_page_topic(page)
        return
    for t in report_topics():
        if not is_used(t.id) and t.key_points:
            yield t
    for pid in archive_candidates():
        if not is_used(pid):
            yield archive_topic(pid)


def pick(track: str, used: set[str]) -> Topic:
    for topic in candidates(track, used):
        return topic
    raise RuntimeError("캐릿 아카이브에 아직 안 쓴 소재가 없습니다." if track == "trend"
                       else "입시 소재(리포트·아카이브)를 모두 사용했습니다.")


def fetch(page_id: str, track: str) -> Topic:
    """특정 페이지를 소재로 지정할 때."""
    if track == "trend":
        r = requests.get(f"{API}/pages/{page_id}", headers=_headers(), timeout=30)
        r.raise_for_status()
        return careet_page_topic(r.json())
    return archive_topic(page_id)
