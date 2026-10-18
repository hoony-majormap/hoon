"""파이프라인 데이터 계약: 소재(Topic) → facts.json → 작가 출력 → script.json (부록 A)."""
from __future__ import annotations

import re
from typing import Iterator, Literal

from pydantic import BaseModel, Field

FACT_REF = re.compile(r"\{(f\d+)\}")


# ── 소재 ────────────────────────────────────────────────────────
class ResearchNote(BaseModel):
    """캐릿 밖에서 찾은 근거 한 줄 (웹 리서치 결과). 캐릿 소재는 이것과 섞어야만 게시된다 (G5)."""

    claim: str = Field(description="확인된 사실 한 줄 (자체 문장, 숫자는 원문 그대로)")
    source: str = Field(description="매체·기관명")
    date: str = Field(description="게시일 YYYY-MM-DD (모르면 빈 문자열)")
    url: str = Field(description="원문 링크 — 검색 결과에 실제로 나온 URL만")


class RelatedContent(BaseModel):
    """메이저맵 콘텐츠 DB에서 찾은 연결 글 — 캡션의 '메이저맵에서 더 보기'."""

    id: int
    title: str
    url: str
    summary: str = ""
    category: str = ""
    majors: str = ""  # 관련 학과·직업
    views: int = 0


class Topic(BaseModel):
    """노션 아카이브 페이지 또는 로컬 JSON에서 읽은 소재 1건."""

    id: str
    title: str
    track: str = "admissions"  # admissions(월·수·금) | trend(화·목)
    source_name: str = "베리타스알파"
    source_type: str = "베리타스 아카이브"
    url: str = ""
    published: str = ""  # YYYY-MM-DD
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    check_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)  # "수치 = 출처명, 기준일" 형식
    keywords: list[str] = Field(default_factory=list)
    next_teaser_hint: str = ""
    research: list[ResearchNote] = Field(default_factory=list)  # 추가 리서치 (트렌드 편 필수)
    angle: str = ""  # 리서처가 제안한 섞는 각도
    related: list[RelatedContent] = Field(default_factory=list)  # 메이저맵 연결 콘텐츠

    def trend_text(self) -> str:
        """노션 소재 원문만 (리서치 제외) — G5의 엄격한 베끼기 검사 대상."""
        parts = [self.title, self.summary, *self.key_points, *self.check_points]
        return "\n".join(p for p in parts if p)

    def source_text(self) -> str:
        """G2 원문 유사도 비교 대상 + 팩트 추출 입력."""
        notes = [f"{n.claim} = {n.source}, {n.date}" for n in self.research]
        return "\n".join(p for p in [self.trend_text(), *self.evidence, *notes] if p)


# ── ② 팩트 추출기 출력 ─────────────────────────────────────────
class Fact(BaseModel):
    id: str = Field(description="f1, f2 … 순번")
    value: str = Field(description="카드에 그대로 찍힐 값. 예: '80.8%', '4,529명', '10명 중 8명'")
    claim: str = Field(description="이 값이 무엇을 뜻하는지 한 줄 (자체 문장)")
    source: str = Field(description="출처 기관·매체명")
    as_of: str = Field(description="수치 기준일 YYYY-MM-DD (모르면 소재 발행일)")
    url: str = Field(description="원문 링크 (없으면 빈 문자열)")
    derived_from: str = Field(
        default="",
        description="다른 팩트를 쉽게 바꾼 표현이면 원 팩트 id (예: '10명 중 8명' ← f1). 아니면 빈 문자열",
    )


class FactSheet(BaseModel):
    facts: list[Fact]


# ── ③ 작가 출력 (6장 고정 구조) ───────────────────────────────
class Line(BaseModel):
    who: Literal["may", "polar"]
    text: str


class HookSlide(BaseModel):
    headline: list[str] = Field(description="3줄 헤드라인, 줄당 공백 제외 9자 이내")
    highlight_line: int = Field(description="레드로 강조할 줄 번호 (1부터)")
    sub: str
    dialogue: list[Line]


class BigNumberSlide(BaseModel):
    label: str
    number: str = Field(description="반드시 '{fN}' 하나")
    line: str
    bar_left: str = Field(description="'{fN}' — 막대 왼쪽(강조) 비율")
    bar_left_label: str
    bar_right: str = Field(description="'{fN}' — 막대 오른쪽 비율")
    bar_right_label: str
    dialogue: list[Line]


class ChangePanel(BaseModel):
    title: str
    before: str = Field(description="'{fN}'")
    after: str = Field(description="'{fN}'")
    note: str


class DotsPanel(BaseModel):
    title: str
    filled: str = Field(description="'{fN}' — 칠할 점 개수가 담긴 팩트")
    total: str = Field(description="'{fN}' — 전체 점 개수가 담긴 팩트")
    note: str


class DetailSlide(BaseModel):
    title: str
    change: ChangePanel
    dots: DotsPanel
    dialogue: list[Line]


class CompareRow(BaseModel):
    item: str
    now: str
    next: str


class CompareSlide(BaseModel):
    title: str
    mode: Literal["change", "versus"] = Field(
        default="change", description="change = 지금→바뀐 뒤(화살표), versus = 나란히 비교(vs)")
    col_now: str
    col_next: str
    rows: list[CompareRow]
    dialogue: list[Line]


class ActionStep(BaseModel):
    title: str
    desc: str


class ActionSlide(BaseModel):
    title: str
    steps: list[ActionStep] = Field(description="정확히 3개")
    dialogue: list[Line]


class CtaSlide(BaseModel):
    headline: str
    teaser: str = Field(description="다음 회 예고 한 줄")
    dialogue: list[Line]


class WriterOutput(BaseModel):
    hook: HookSlide
    big_number: BigNumberSlide
    detail: DetailSlide
    compare: CompareSlide
    action: ActionSlide
    cta: CtaSlide
    caption: str = Field(description="300자 이내 캡션 본문 (출처 링크·해시태그 제외)")
    hashtags: list[str] = Field(description="5개 이내, '#' 포함")


# ── ③ 작가 출력 — 트렌드 트랙 (화·목) ────────────────────────
class TrendItem(BaseModel):
    tag: str = Field(default="유행", description="장 위 꼬리표 (예: '유행', '팩트체크', '진짜 과학') — 뒤에 번호가 붙는다")
    name: str = Field(description="이 장의 제목 (짧게)")
    what_label: str = Field(default="이게 뭐냐면", description="첫 칸 제목")
    what: str = Field(description="첫 칸 — 처음 듣는 고등학생에게 한 줄 설명")
    why_label: str = Field(default="왜 뜨냐면", description="둘째 칸 제목 (예: '왜 뜨냐면', '알고 보면', '주의할 점')")
    why: str = Field(description="둘째 칸 — 10대 시선의 이유 또는 리서치로 보탠 사실")
    dialogue: list[Line] = Field(description="0~1개")


class CareerLink(BaseModel):
    field: str = Field(description="실제 학과명 또는 직업명")
    reason: str = Field(description="이 유행과 어떻게 이어지는지 한 줄")


class CareerSlide(BaseModel):
    title: str
    links: list[CareerLink] = Field(description="정확히 3개")
    tip: str = Field(description="오늘 해볼 것 한 줄")
    dialogue: list[Line] = Field(description="0~1개")


class TrendWriterOutput(BaseModel):
    hook: HookSlide
    items: list[TrendItem] = Field(description="정확히 3개 — 유행 소개 + 리서치로 보탠 사실·관점")
    career: CareerSlide
    cta: CtaSlide
    caption: str = Field(description="300자 이내 캡션 본문 (출처 링크·해시태그 제외)")
    hashtags: list[str] = Field(description="5개 이내, '#' 포함")


ADMISSIONS_LAYOUTS = ["hook", "big_number", "detail", "compare", "action", "cta"]


def to_script(topic: Topic, facts: list[Fact], out: WriterOutput | TrendWriterOutput, kicker: str,
              next_label: str = "", post_date: str = "") -> dict:
    """작가 출력 → script.json (렌더러 입력). 트랙마다 6장 구성이 다르다."""
    slides: list[dict] = []
    if isinstance(out, TrendWriterOutput):
        slides.append({"layout": "hook", **out.hook.model_dump(), "kicker": kicker})
        for i, item in enumerate(out.items, start=1):
            slides.append({"layout": "trend_item", "index": i, **item.model_dump()})
        slides.append({"layout": "career", **out.career.model_dump()})
        slides.append({"layout": "cta", **out.cta.model_dump()})
    else:
        for layout in ADMISSIONS_LAYOUTS:
            slide = {"layout": layout, **getattr(out, layout).model_dump()}
            if layout == "hook":
                slide["kicker"] = kicker
            slides.append(slide)
    for no, slide in enumerate(slides, start=1):
        slide["no"] = no
    return {
        "track": topic.track,
        "post_date": post_date,
        "topic_id": topic.id,
        "topic_title": topic.title,
        "kicker": kicker,
        "next_label": next_label,
        "source": {"name": topic.source_name, "date": topic.published, "url": topic.url},
        "research": [n.model_dump() for n in topic.research],
        "related": [r.model_dump() for r in topic.related],
        "facts": [f.model_dump() for f in facts],
        "slides": slides,
        "caption": out.caption,
        "hashtags": out.hashtags,
    }


def iter_texts(script: dict) -> Iterator[tuple[str, str]]:
    """작가가 쓴 모든 문자열을 (경로, 텍스트)로 순회 — 게이트 공통 입력."""

    def walk(node, path):
        if isinstance(node, str):
            yield path, node
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{path}[{i}]")
        elif isinstance(node, dict):
            for k, v in node.items():
                if k in ("no", "layout", "who", "highlight_line", "kicker", "index"):
                    continue
                yield from walk(v, f"{path}.{k}" if path else k)

    for slide in script["slides"]:
        yield from walk(slide, f"slides[{slide['no']}]")
    yield "caption", script["caption"]
    for i, tag in enumerate(script["hashtags"]):
        yield f"hashtags[{i}]", tag


def fact_map(script: dict) -> dict[str, dict]:
    return {f["id"]: f for f in script["facts"]}


def resolve(text: str, facts: dict[str, dict]) -> str:
    """'{f1}' → '80.8%'. 없는 id는 그대로 둔다 (G1이 잡는다)."""
    return FACT_REF.sub(lambda m: facts[m.group(1)]["value"] if m.group(1) in facts else m.group(0), text)


def refs_in(node) -> set[str]:
    """노드(슬라이드 등) 안에서 참조된 fact id 집합."""
    found: set[str] = set()
    if isinstance(node, str):
        found.update(FACT_REF.findall(node))
    elif isinstance(node, list):
        for v in node:
            found |= refs_in(v)
    elif isinstance(node, dict):
        for v in node.values():
            found |= refs_in(v)
    return found
