"""노션 '베리타스알파 구독자 기사 아카이브' DB에서 소재 1건을 읽는다 (MVP §9.2).

1단계에서는 같은 인터페이스로 '소재 DB'를 읽도록 교체한다.
필요 환경변수: NOTION_TOKEN (아카이브 DB가 이 통합(integration)에 공유돼 있어야 함)
"""
from __future__ import annotations

import os

import requests

from ..models import Topic

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
# 📚 베리타스알파 구독자 기사 아카이브 (2026.07.17~10.17)
ARCHIVE_DB_ID = os.environ.get("NOTION_ARCHIVE_DB_ID", "5a9f093b-a89f-4fc8-8de2-432e6fbb05dc")

# 고1·고2 관련 키워드 (기획안 §4.1 '소재 채우는 경로')
MON_KEYWORDS = ["2028 개편", "학생부 정성평가", "반도체·AI·첨단", "무전공·자유전공", "수능최저"]


def _headers() -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN이 없습니다. .env에 설정하거나 --topic-file로 로컬 소재를 쓰세요.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


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
    return None


def _page_sections(page_id: str) -> dict[str, list[str]]:
    """'핵심 내용' / '체크 포인트' 헤딩 아래 글머리 항목을 모은다."""
    sections: dict[str, list[str]] = {}
    current = None
    cursor = None
    while True:
        params = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        r = requests.get(f"{API}/blocks/{page_id}/children", headers=_headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        for block in data["results"]:
            kind = block["type"]
            if kind.startswith("heading_"):
                current = _plain(block[kind]["rich_text"]).strip()
                sections.setdefault(current, [])
            elif kind in ("bulleted_list_item", "numbered_list_item", "paragraph") and current:
                text = _plain(block[kind]["rich_text"]).strip()
                if text:
                    sections[current].append(text)
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return sections


def fetch_topic(page_id: str) -> Topic:
    r = requests.get(f"{API}/pages/{page_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    page = r.json()
    props = page["properties"]
    sections = _page_sections(page_id)
    title = _prop(props, "기사 제목")
    published = _prop(props, "발행일")
    return Topic(
        id=page["id"],
        title=title,
        url=_prop(props, "링크"),
        published=published,
        summary=_prop(props, "핵심 요약"),
        keywords=_prop(props, "키워드") or [],
        key_points=sections.get("핵심 내용", []),
        check_points=sections.get("체크 포인트", []),
        evidence=[f"{title} = 베리타스알파, {published}"],
    )


def pick_latest(used_ids: set[str], keywords: list[str] = MON_KEYWORDS) -> Topic:
    """키워드가 걸린 최신 기사 중 아직 쓰지 않은 1건."""
    body = {
        "filter": {"or": [{"property": "키워드", "multi_select": {"contains": k}} for k in keywords]},
        "sorts": [{"property": "발행일", "direction": "descending"}],
        "page_size": 50,
    }
    r = requests.post(f"{API}/databases/{ARCHIVE_DB_ID}/query", headers=_headers(), json=body, timeout=30)
    r.raise_for_status()
    for page in r.json()["results"]:
        if page["id"] not in used_ids and page["id"].replace("-", "") not in used_ids:
            return fetch_topic(page["id"])
    raise RuntimeError("조건에 맞는 미사용 소재가 없습니다 (월요일 재고 소진).")
