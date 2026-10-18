"""렌더 전 텍스트 게이트 (기획안 §7).

G1 팩트체커(코드부) — 카드 속 모든 숫자가 facts.json에 있는가
G2 원문 유사도 — 소재 원문과 연속 어절 n개 이상 겹치는가
G3 톤·안전(코드부) — 금칙어, 슬롯별 글자 수, 장 구조
G5 섞기(트렌드 편) — 캐릿 소재를 그대로 올리지 않는다: 캐릿 밖 리서치 팩트가 카드에 실리고, 캐릿 문장과 더 엄격하게 비교
"""
from __future__ import annotations

import re

from ..config import BANNED_PHRASES, CAREET_DOMAINS, G2_NGRAM, G5_NGRAM, LIMITS
from ..models import FACT_REF, Topic, fact_map, iter_texts, refs_in, resolve

NUM = re.compile(r"\d+(?:[.,]\d+)*")
# 학년 표기(고1·중3)는 통계가 아니므로 숫자 검사에서 뺀다
GRADE = re.compile(r"[중고]\s?[1-3](?!\d)")


def _nums(text: str) -> set[str]:
    return {m.replace(",", "") for m in NUM.findall(GRADE.sub("", text))}


def _len(text: str) -> int:
    return len(text.replace(" ", ""))


def _result(gate: str, violations: list[str], warnings: list[str] | None = None, **extra) -> dict:
    return {"gate": gate, "pass": not violations, "violations": violations, "warnings": warnings or [], **extra}


# ── G1 ──────────────────────────────────────────────────────────
def g1_facts(script: dict, topic: Topic) -> dict:
    facts = fact_map(script)
    source_nums = _nums(topic.source_text())
    violations, warnings = [], []

    # (a) 팩트 값 자체가 소재 원문에 근거하는가 — 팩트 추출기 환각 차단
    # 바꿔 말하기(derived)는 원문에 숫자가 우연히 있어도 항상 확인 대상으로 남긴다
    for f in script["facts"]:
        if f.get("derived_from"):
            if f["derived_from"] not in facts:
                violations.append(f"{f['id']} '{f['value']}': derived_from '{f['derived_from']}'가 facts에 없음")
            else:
                warnings.append(f"{f['id']} '{f['value']}'는 {f['derived_from']}의 바꿔 말하기 — 사람이 한 번 확인 권장")
            continue
        missing = _nums(f["value"]) - source_nums
        if missing:
            violations.append(f"{f['id']} '{f['value']}': 숫자 {sorted(missing)}가 소재 원문에 없음")

    # (b) 참조 id 존재 + (c) 작가 텍스트 속 숫자가 팩트 값에서 왔는가
    allowed = set().union(*(_nums(f["value"]) for f in script["facts"])) if script["facts"] else set()
    for path, text in iter_texts(script):
        for ref in FACT_REF.findall(text):
            if ref not in facts:
                violations.append(f"{path}: 없는 팩트 참조 {{{ref}}}")
        # 해시태그(#2028입시)는 참조 문법을 쓸 수 없으니 '값이 facts에 있는가'만 본다
        typed = set() if path.startswith("hashtags") else _nums(FACT_REF.sub("", text))
        if typed:
            violations.append(f"{path}: 숫자를 직접 씀 {sorted(typed)} → facts id로 참조할 것 ('{text}')")
        stray = _nums(resolve(text, facts)) - allowed
        if stray and not typed:
            violations.append(f"{path}: '{resolve(text, facts)}'의 숫자 {sorted(stray)}가 facts에 없음")
    return _result("G1", violations, warnings)


# ── G2 ──────────────────────────────────────────────────────────
def _eojeol(text: str) -> list[str]:
    return [w for w in re.sub(r"[^\w%.,·]", " ", text).split() if w]


def _overlaps(script: dict, source: str, n: int, label: str) -> tuple[list[str], float]:
    facts = fact_map(script)
    src = _eojeol(source)
    src_grams = {tuple(src[i : i + n]) for i in range(len(src) - n + 1)}
    violations, max_ratio = [], 0.0
    for path, text in iter_texts(script):
        words = _eojeol(resolve(text, facts))
        if len(words) < n:
            continue
        grams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
        hits = [g for g in grams if g in src_grams]
        max_ratio = max(max_ratio, len(hits) / len(grams))
        if hits:
            violations.append(f"{path}: {label}과 {n}어절 연속 일치 — '{' '.join(hits[0])}'")
    return violations, max_ratio


def g2_similarity(script: dict, topic: Topic, n: int = G2_NGRAM) -> dict:
    violations, max_ratio = _overlaps(script, topic.source_text(), n, "원문")
    return _result("G2", violations, max_overlap_ratio=round(max_ratio, 3), ngram=n)


# ── G5 (트렌드 편) ──────────────────────────────────────────────
def _is_careet(source: str, url: str) -> bool:
    return "캐릿" in source or any(d in (url or "") for d in CAREET_DOMAINS)


def g5_mix(script: dict, topic: Topic, n: int = G5_NGRAM) -> dict:
    """캐릿에서 온 소재는 그대로 올리지 않는다 — 다른 출처와 섞이고, 캐릿 문장과도 멀어야 게시."""
    facts = fact_map(script)
    violations, warnings = [], []
    outside = [r for r in topic.research if r.url and not _is_careet(r.source, r.url)]
    if not outside:
        violations.append("캐릿 밖 리서치 출처가 없음 — 캐릿 소재만으로는 게시하지 않는다")
    mixed = sorted(fid for fid in refs_in(script["slides"])
                   if fid in facts and not _is_careet(facts[fid]["source"], facts[fid]["url"]))
    if not mixed:
        violations.append("카드에 캐릿 밖 출처의 팩트가 없음 — 리서치 팩트를 {fN}으로 1개 이상 써야 함")
    copied, max_ratio = _overlaps(script, topic.trend_text(), n, "캐릿 원문")
    violations += copied
    if not topic.related:
        warnings.append("메이저맵 연결 콘텐츠 없음 — 캡션에 '메이저맵에서 더 보기'가 빠짐")
    return _result("G5", violations, warnings, research_sources=len(outside), research_facts=mixed,
                   max_overlap_ratio=round(max_ratio, 3), ngram=n)


# ── G3 (코드부) ────────────────────────────────────────────────
def g3_tone_limits(script: dict) -> dict:
    facts = fact_map(script)
    v: list[str] = []

    def check(path: str, text: str, limit_key: str):
        n = _len(resolve(text, facts))
        if n > LIMITS[limit_key]:
            v.append(f"{path}: {n}자 > {LIMITS[limit_key]}자 ('{resolve(text, facts)}')")

    for path, text in iter_texts(script):
        for phrase in BANNED_PHRASES:
            if phrase in text:
                v.append(f"{path}: 금칙어 '{phrase}'")

    s = {sl["layout"]: sl for sl in script["slides"]}
    if len(script["slides"]) != 6:
        v.append(f"장 수 {len(script['slides'])} ≠ 6")

    for sl in script["slides"]:
        p = f"slides[{sl['no']}]"
        dlg = sl.get("dialogue", [])
        if len(dlg) > LIMITS["bubbles_per_slide"]:
            v.append(f"{p}.dialogue: 말풍선 {len(dlg)}개 > {LIMITS['bubbles_per_slide']}개")
        for i, line in enumerate(dlg):
            check(f"{p}.dialogue[{i}]", line["text"], "bubble")
        if "title" in sl:
            check(f"{p}.title", sl["title"], "title")

    hook = s["hook"]
    if len(hook["headline"]) != LIMITS["headline_lines"]:
        v.append(f"slides[1].headline: {len(hook['headline'])}줄 ≠ {LIMITS['headline_lines']}줄")
    for i, line in enumerate(hook["headline"]):
        check(f"slides[1].headline[{i}]", line, "headline_line")
    if not 1 <= hook["highlight_line"] <= len(hook["headline"]):
        v.append("slides[1].highlight_line 범위 밖")
    check("slides[1].sub", hook["sub"], "sub")
    whos = [d["who"] for d in hook["dialogue"]]
    if not ("polar" in whos and "may" in whos):
        v.append("slides[1].dialogue: Polar 질문 + May 한 줄 대화가 필요")

    if script.get("track", "admissions") == "trend":
        _g3_trend(script, check, v)
    else:
        big = s["big_number"]
        check("slides[2].label", big["label"], "label")
        check("slides[2].line", big["line"], "big_line")
        if len(FACT_REF.findall(big["number"])) != 1 or FACT_REF.sub("", big["number"]).strip():
            v.append("slides[2].number: 큰 숫자는 팩트 참조 정확히 1개여야 함")
        if bool(big["bar_left"]) != bool(big["bar_right"]):
            v.append("slides[2].bar: 왼쪽·오른쪽은 함께 쓰거나 함께 비워야 함")

        det = s["detail"]
        check("slides[3].change.title", det["change"]["title"], "panel_title")
        check("slides[3].change.note", det["change"]["note"], "panel_note")
        check("slides[3].dots.title", det["dots"]["title"], "panel_title")
        check("slides[3].dots.note", det["dots"]["note"], "panel_note")
        for key in ("before", "after"):
            if len(FACT_REF.findall(det["change"][key])) != 1:
                v.append(f"slides[3].change.{key}: 팩트 참조 1개가 필요")
        if det["dots"]["filled"] or det["dots"]["total"]:
            try:
                filled = _first_int(resolve(det["dots"]["filled"], facts))
                total = _first_int(resolve(det["dots"]["total"], facts))
                if not 0 < filled <= total <= 20:
                    v.append(f"slides[3].dots: {filled}/{total} — 0 < 칠한 수 ≤ 전체 ≤ 20 이어야 함")
            except ValueError:
                v.append("slides[3].dots: filled/total 값에서 정수를 읽을 수 없음")

        cmp_ = s["compare"]
        if not 1 <= len(cmp_["rows"]) <= LIMITS["compare_rows"]:
            v.append(f"slides[4].rows: {len(cmp_['rows'])}행 (1~{LIMITS['compare_rows']}행)")
        for i, row in enumerate(cmp_["rows"]):
            for k in ("item", "now", "next"):
                check(f"slides[4].rows[{i}].{k}", row[k], "compare_cell")
        check("slides[4].col_now", cmp_["col_now"], "compare_cell")
        check("slides[4].col_next", cmp_["col_next"], "compare_cell")

        act = s["action"]
        if len(act["steps"]) != 3:
            v.append(f"slides[5].steps: {len(act['steps'])}개 ≠ 3개")
        for i, st in enumerate(act["steps"]):
            check(f"slides[5].steps[{i}].title", st["title"], "action_title")
            check(f"slides[5].steps[{i}].desc", st["desc"], "action_desc")

    cta = s["cta"]
    check(f"slides[{cta['no']}].teaser", cta["teaser"], "teaser")
    check(f"slides[{cta['no']}].headline", cta["headline"], "title")

    if _len(resolve(script["caption"], facts)) > LIMITS["caption"]:
        v.append(f"caption: {_len(resolve(script['caption'], facts))}자 > {LIMITS['caption']}자")
    if len(script["hashtags"]) > LIMITS["hashtags"]:
        v.append(f"hashtags: {len(script['hashtags'])}개 > {LIMITS['hashtags']}개")
    for t in script["hashtags"]:
        if not t.startswith("#") or " " in t:
            v.append(f"hashtags: '{t}' 형식 오류")
    return _result("G3", v, engine="code (금칙어·글자 수·구조) — LLM 톤 판정은 1단계")


def _g3_trend(script: dict, check, v: list[str]) -> None:
    items = [sl for sl in script["slides"] if sl["layout"] == "trend_item"]
    if len(items) != 3:
        v.append(f"trend_item: {len(items)}장 ≠ 3장")
    for sl in items:
        p = f"slides[{sl['no']}]"
        check(f"{p}.tag", sl.get("tag", ""), "trend_tag")
        check(f"{p}.name", sl["name"], "trend_name")
        check(f"{p}.what_label", sl.get("what_label", ""), "trend_label")
        check(f"{p}.what", sl["what"], "trend_text")
        check(f"{p}.why_label", sl.get("why_label", ""), "trend_label")
        check(f"{p}.why", sl["why"], "trend_text")
        if len(sl["dialogue"]) > 1:
            v.append(f"{p}.dialogue: 유행 장은 말풍선 1개까지")
    career = next((sl for sl in script["slides"] if sl["layout"] == "career"), None)
    if not career:
        v.append("career 장이 없음")
        return
    p = f"slides[{career['no']}]"
    if len(career["links"]) != 3:
        v.append(f"{p}.links: {len(career['links'])}개 ≠ 3개")
    for i, link in enumerate(career["links"]):
        check(f"{p}.links[{i}].field", link["field"], "career_field")
        check(f"{p}.links[{i}].reason", link["reason"], "career_reason")
    check(f"{p}.tip", career["tip"], "career_tip")


def _first_int(text: str) -> int:
    m = re.search(r"\d+", text.replace(",", ""))
    if not m:
        raise ValueError(text)
    return int(m.group())


def run_text_gates(script: dict, topic: Topic) -> list[dict]:
    results = [g1_facts(script, topic), g2_similarity(script, topic), g3_tone_limits(script)]
    if topic.track == "trend":
        results.append(g5_mix(script, topic))
    return results


def feedback(results: list[dict]) -> list[str]:
    return [f"[{r['gate']}] {m}" for r in results for m in r["violations"]]
