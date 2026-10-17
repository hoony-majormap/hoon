#!/usr/bin/env python3
"""korean-edu-market-research 결정론적 파이프라인.

LLM이 하면 안 되는 일(산수, 등급 판정, 병합, 렌더링)을 여기서 한다.
에이전트는 JSON만 만들고, 수치 계산과 MD/HTML 생성은 전부 이 스크립트가 한다.
findings.json 하나만 진실원천(SSOT)으로 두기 위해서다.

사용법:
  pipeline.py init     --keyword "외국인 TOPIK 대비 과정" [--date 2026-10-17] [--out output]
  pipeline.py validate RUN_DIR/raw/c1.json
  pipeline.py merge    RUN_DIR
  pipeline.py render   RUN_DIR
  pipeline.py check    RUN_DIR

표준 라이브러리만 쓴다.
"""

import argparse
import datetime as dt
import html
import json
import re
import statistics
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "dashboard-template.html"

SEGMENTS = ["어학당", "사설학원", "온라인코스", "앱", "과외", "유학원", "공공무료"]
PUBLIC_SEGMENTS = {"어학당", "공공무료"}
SOURCE_TYPES = ["official", "aggregator", "press", "sns", "blog", "snippet"]
TIERS = ["A", "B", "C"]
STALE_MONTHS = 18
MIN_VERIFIED_RATIO = 0.70
PPH_TOLERANCE = 0.01

# 17개 계약 필드 중 필수
REQUIRED = [
    "name", "segment", "price_raw", "currency", "total_hours", "hours_estimated",
    "price_per_hour_krw", "source_urls", "published_at", "confidence", "checked_at",
]
# 정규화를 결정론적으로 하기 위한 보조 필드 (계약 17개 외)
AUX_REQUIRED = ["id", "price_amount", "source_type", "evidence"]


# ---------------------------------------------------------------- utils

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_date(value):
    """YYYY / YYYY-MM / YYYY-MM-DD. 부분 날짜는 가장 이른 날로 본다(신선도를 보수적으로)."""
    if not isinstance(value, str):
        return None
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", value.strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def months_between(start, end):
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def worst_tier(*tiers):
    return max((t for t in tiers if t in TIERS), key=TIERS.index, default="C")


def slugify(text):
    text = re.sub(r"[\\/:*?\"<>|]", "", text.strip())
    return re.sub(r"\s+", "-", text)


def won(n):
    if n is None:
        return "미확인"
    return f"{round(n):,}원"


def hours_text(h, estimated):
    if h is None:
        return "미확인"
    s = f"{h:g}h"
    return f"{s} (시수 추정)" if estimated else s


# ---------------------------------------------------------------- init

def cmd_init(args):
    date = args.date or dt.date.today().isoformat()
    if not parse_date(date):
        sys.exit(f"잘못된 날짜: {date}")
    run_dir = Path(args.out) / f"{date}-{slugify(args.keyword)}"
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    run_path = run_dir / "run.json"
    if not run_path.exists():
        dump_json(run_path, {
            "keyword": args.keyword,
            "run_date": date,
            "selection": {"mode": None, "selected_ids": []},
        })
    print(run_dir)


# ---------------------------------------------------------------- validate

def validate_record(rec):
    """스키마 위반 목록을 돌려준다. 빈 리스트면 통과."""
    errors = []
    for key in REQUIRED + AUX_REQUIRED:
        if key not in rec:
            errors.append(f"필수 필드 없음: {key}")
    if errors:
        return errors

    if rec["segment"] not in SEGMENTS:
        errors.append(f"segment는 {SEGMENTS} 중 하나: {rec['segment']!r}")
    if rec["source_type"] not in SOURCE_TYPES:
        errors.append(f"source_type은 {SOURCE_TYPES} 중 하나: {rec['source_type']!r}")
    if rec["confidence"] not in TIERS:
        errors.append(f"confidence는 A/B/C: {rec['confidence']!r}")
    if not isinstance(rec["source_urls"], list) or not all(
        isinstance(u, str) and u.startswith("http") for u in rec["source_urls"]
    ):
        errors.append("source_urls는 http URL 배열")
    if not isinstance(rec["hours_estimated"], bool):
        errors.append("hours_estimated는 true/false")
    if rec["price_amount"] is not None and not isinstance(rec["price_amount"], (int, float)):
        errors.append("price_amount는 숫자 또는 null")
    if rec["total_hours"] is not None and (
        not isinstance(rec["total_hours"], (int, float)) or rec["total_hours"] <= 0
    ):
        errors.append("total_hours는 양수 또는 null")
    if rec["hours_estimated"] and not rec.get("hours_basis"):
        errors.append("hours_estimated=true면 hours_basis(추정 근거)가 필요")
    if rec["published_at"] != "date_unknown" and not parse_date(rec["published_at"]):
        errors.append("published_at은 YYYY[-MM[-DD]] 또는 'date_unknown'")
    if not parse_date(rec["checked_at"]):
        errors.append("checked_at은 YYYY-MM-DD")
    if rec["currency"] != "KRW" and rec["price_amount"]:
        fx = rec.get("fx") or {}
        if not isinstance(fx.get("rate_to_krw"), (int, float)) or not fx.get("as_of"):
            errors.append("외화 가격이면 fx.rate_to_krw와 fx.as_of가 필요")
    if not isinstance(rec["evidence"], list):
        errors.append("evidence는 배열")
    else:
        fields = {e.get("field") for e in rec["evidence"] if isinstance(e, dict)}
        if rec["price_amount"] is not None and "price_raw" not in fields:
            errors.append("가격을 적었으면 evidence에 price_raw 원문 인용이 필요")
        if rec["total_hours"] is not None and not rec["hours_estimated"] and "total_hours" not in fields:
            errors.append("시수를 확정값으로 적었으면 evidence에 total_hours 원문 인용이 필요")
        for e in rec["evidence"]:
            if not isinstance(e, dict) or not e.get("quote") or not str(e.get("url", "")).startswith("http"):
                errors.append("evidence 항목은 {field, quote, url} 형태")
                break
    return errors


def cmd_validate(args):
    rec = load_json(args.file)
    errors = validate_record(rec)
    if errors:
        print(f"FAIL {args.file}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    pph, note = compute_pph(rec)
    print(f"OK {args.file} — {rec['name']} / 시간당 {won(pph)}" + (f" ({note})" if note else ""))


# ---------------------------------------------------------------- merge

def compute_pph(rec):
    """시간당 원가(KRW/h)를 직접 계산한다. (값, 계산 불가 사유)"""
    amount, hours = rec.get("price_amount"), rec.get("total_hours")
    if amount is None:
        return None, "가격 미확인"
    if not hours:
        return None, "시수 미확인"
    rate = 1
    if rec.get("currency") != "KRW":
        rate = (rec.get("fx") or {}).get("rate_to_krw")
        if not rate:
            return None, "환율 없음"
    return round(amount * rate / hours), None


def grade(rec, verdict):
    """규칙 기반 등급과 플래그. 선언 등급, 규칙 등급, 검증 권고 중 가장 낮은 것을 쓴다."""
    flags, tiers = [], [rec["confidence"]]
    checked = parse_date(rec["checked_at"])

    if rec["published_at"] == "date_unknown":
        flags.append("date_unknown")
        tiers.append("C")
    else:
        published = parse_date(rec["published_at"])
        if months_between(published, checked) >= STALE_MONTHS:
            flags.append("stale")
            tiers.append("C")

    if rec["source_type"] == "snippet":
        flags.append("snippet_only")
        tiers.append("C")
    elif rec["source_type"] in ("press", "sns", "blog"):
        flags.append("secondary_source")
        tiers.append("B")

    if rec["hours_estimated"]:
        flags.append("hours_estimated")
        tiers.append("B")

    pph, reason = compute_pph(rec)
    if pph is None:
        flags.append("pph_unavailable")
        tiers.append("C")
    else:
        claimed = rec.get("price_per_hour_krw")
        if isinstance(claimed, (int, float)) and pph and abs(claimed - pph) / pph > PPH_TOLERANCE:
            flags.append("pph_recomputed")

    if verdict:
        flags.extend(f for f in verdict.get("flags", []) if f not in flags)
        if verdict.get("recommended_confidence") in TIERS:
            tiers.append(verdict["recommended_confidence"])

    return worst_tier(*tiers), flags, pph, reason


def summarize_errors(errors, limit=3):
    head = "; ".join(errors[:limit])
    more = f" 외 {len(errors) - limit}건" if len(errors) > limit else ""
    return f"스키마 위반: {head}{more}"


def cmd_merge(args):
    run_dir = Path(args.run_dir)
    run = load_json(run_dir / "run.json")
    verification_path = run_dir / "verification.json"
    verification = load_json(verification_path) if verification_path.exists() else {}
    if not verification:
        print("경고: verification.json 없음 — 검증 에이전트를 거치지 않은 병합이다", file=sys.stderr)

    competitors, excluded, invalid = [], [], []
    for path in sorted((run_dir / "raw").glob("*.json")):
        rec = load_json(path)
        errors = validate_record(rec)
        if errors:
            invalid.append({"file": path.name, "name": rec.get("name"), "errors": errors})
            continue
        if not rec["source_urls"]:
            excluded.append({"id": rec["id"], "name": rec["name"], "reason": "source_urls 비어 있음"})
            continue

        verdict = verification.get(rec["id"])
        tier, flags, pph, reason = grade(rec, verdict)
        out = dict(rec)
        out["claimed_price_per_hour_krw"] = rec.get("price_per_hour_krw")
        out["price_per_hour_krw"] = pph
        out["pph_unavailable_reason"] = reason
        out["declared_confidence"] = rec["confidence"]
        out["confidence"] = tier
        out["flags"] = flags
        out["sector"] = "공공·대학" if rec["segment"] in PUBLIC_SEGMENTS else "사설·플랫폼"
        out["section"] = "body" if tier in ("A", "B") else "appendix"
        out["verifier_notes"] = (verdict or {}).get("notes")
        competitors.append(out)

    if invalid:
        for item in invalid:
            print(f"스키마 위반으로 제외: {item['file']}", file=sys.stderr)
            for e in item["errors"]:
                print(f"  - {e}", file=sys.stderr)

    body = [c for c in competitors if c["section"] == "body"]
    paid = [c["price_per_hour_krw"] for c in body if c["price_per_hour_krw"]]
    total = len(competitors) + len(excluded) + len(invalid)
    verified = len(body)
    stats = {
        "total_candidates_analyzed": total,
        "body_count": len(body),
        "appendix_count": len(competitors) - len(body),
        "excluded_count": len(excluded) + len(invalid),
        "verified_ratio": round(verified / total, 3) if total else 0,
        "paid_count": len(paid),
        "free_count": sum(1 for c in body if c["price_per_hour_krw"] == 0),
        "pph_median": round(statistics.median(paid)) if paid else None,
        "pph_min": min(paid) if paid else None,
        "pph_max": max(paid) if paid else None,
        "pph_spread": round(max(paid) / min(paid), 1) if len(paid) >= 2 else None,
        "topik_guarantee_count": sum(1 for c in body if c.get("topik_guarantee") is True),
    }

    findings = {
        "meta": {
            "keyword": run["keyword"],
            "run_date": run["run_date"],
            "selection": run.get("selection", {}),
            "verified_by_agent": bool(verification),
            "merged_at": dt.datetime.now().isoformat(timespec="seconds"),
            "rules": {"stale_months": STALE_MONTHS, "min_verified_ratio": MIN_VERIFIED_RATIO},
        },
        "stats": stats,
        "competitors": competitors,
        "excluded": excluded + [
            {"id": None, "name": i["name"] or i["file"], "reason": summarize_errors(i["errors"])}
            for i in invalid
        ],
    }
    dump_json(run_dir / "findings.json", findings)
    print(f"findings.json — 본문 {stats['body_count']} / 부록 {stats['appendix_count']} / "
          f"제외 {stats['excluded_count']} / 출처 확인 비율 {stats['verified_ratio']:.0%}")


# ---------------------------------------------------------------- analysis

def validate_analysis(analysis, findings):
    body_ids = {c["id"] for c in findings["competitors"] if c["section"] == "body"}
    all_ids = {c["id"] for c in findings["competitors"]}
    errors = []

    def check_refs(where, refs):
        if not refs:
            errors.append(f"{where}: refs가 비어 있음 (근거 없는 주장)")
        for r in refs or []:
            if r not in all_ids:
                errors.append(f"{where}: 존재하지 않는 id {r!r}")
            elif r not in body_ids:
                errors.append(f"{where}: {r!r}는 부록(C등급) 항목 — 근거로 쓸 수 없음")

    for i, c in enumerate(analysis.get("conclusions", []), 1):
        check_refs(f"결론 {i}", c.get("refs"))
    gaps = analysis.get("gaps", [])
    if not 1 <= len(gaps) <= 3:
        errors.append(f"gaps는 1-3개여야 함 (현재 {len(gaps)})")
    for i, g in enumerate(gaps, 1):
        check_refs(f"빈틈 {i}", g.get("refs"))
    proposal = analysis.get("proposal")
    if not proposal:
        errors.append("proposal 없음")
    else:
        for key in ("name", "target", "curriculum", "price_krw", "total_hours", "differentiator"):
            if proposal.get(key) in (None, ""):
                errors.append(f"proposal.{key} 없음")
        check_refs("제안", proposal.get("refs"))
    return errors


# ---------------------------------------------------------------- render

def md_cell(text):
    return str(text if text not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def source_links(urls):
    return " ".join(f"[{i}]({u})" for i, u in enumerate(urls, 1))


def render_report(findings, analysis, check_result):
    meta, stats = findings["meta"], findings["stats"]
    comps = findings["competitors"]
    by_id = {c["id"]: c for c in comps}
    body = [c for c in comps if c["section"] == "body"]
    appendix = [c for c in comps if c["section"] == "appendix"]
    selection = meta.get("selection") or {}
    lines = []
    w = lines.append

    w(f"# {meta['keyword']} — 경쟁 상품 리서치 리포트")
    w("")
    w(f"> 실행일 {meta['run_date']} · 분석 대상 {stats['total_candidates_analyzed']}곳 "
      f"(본문 {stats['body_count']} / 부록 {stats['appendix_count']} / 제외 {stats['excluded_count']}) · "
      f"출처 확인 비율 {stats['verified_ratio']:.0%}")
    if selection.get("mode") == "auto":
        w(">")
        w("> ⚠️ **경쟁사 자동 선정됨 — 검토 필요.** 승인 게이트에 응답이 없어 발굴 상위 후보로 자동 진행했다.")
    if not meta.get("verified_by_agent"):
        w(">")
        w("> ⚠️ **검증 에이전트를 거치지 않았다.** 수치를 의사결정에 쓰기 전에 검증을 돌릴 것.")
    if not check_result["passed"]:
        w(">")
        w("> 🚫 **완료 판정 미통과 — 위험물.** 아래 '완료 판정' 절의 실패 항목을 먼저 해결할 것.")
    w("")
    w(f"확인된 경쟁사 {stats['body_count']}곳을 기준으로 작성했다. 개수를 채우기 위해 추가한 항목은 없다.")
    w("")

    w("## 결론")
    w("")
    for i, c in enumerate(analysis.get("conclusions", []), 1):
        refs = ", ".join(by_id[r]["name"] for r in c.get("refs", []) if r in by_id)
        w(f"{i}. {c['text']} _(근거: {refs})_")
    w("")

    w("## 지표 요약")
    w("")
    w("| 지표 | 값 | 비고 |")
    w("|---|---|---|")
    w(f"| 시간당 원가 중앙값 | {won(stats['pph_median'])} | 유료 {stats['paid_count']}곳 기준, 무료 {stats['free_count']}곳 제외 |")
    spread = f"{won(stats['pph_min'])} ~ {won(stats['pph_max'])}" if stats["pph_min"] is not None else "미확인"
    ratio = f" ({stats['pph_spread']}배)" if stats["pph_spread"] else ""
    w(f"| 가격 스프레드 | {spread}{ratio} | 유료 본문 항목 |")
    w(f"| 출처 확인 비율 | {stats['verified_ratio']:.0%} | A/B 등급 ÷ 전체 분석 대상 (기준 {MIN_VERIFIED_RATIO:.0%}) |")
    w(f"| TOPIK 급수 보장 제공 | {stats['topik_guarantee_count']}곳 | 본문 항목 중 |")
    w("")

    w("## 경쟁사 비교표")
    w("")
    w("원가격과 시간당 환산값을 나란히 둔다. 환산 과정을 숨기지 않기 위해서다.")
    w("")
    w("| 상품 | 세그먼트 | 원가격(표기 그대로) | 총 시수 | 시간당 원가 | 신뢰도 | 출처 |")
    w("|---|---|---|---|---|---|---|")
    for c in sorted(body, key=lambda c: (c["price_per_hour_krw"] is None, c["price_per_hour_krw"] or 0)):
        w(f"| {md_cell(c['name'])} | {c['segment']} | {md_cell(c['price_raw'])} | "
          f"{hours_text(c['total_hours'], c['hours_estimated'])} | {won(c['price_per_hour_krw'])} | "
          f"{c['confidence']} | {source_links(c['source_urls'])} |")
    w("")

    w("## 경쟁사 팩트시트")
    w("")
    for c in body:
        w(f"### {c['name']} ({c['segment']} · 신뢰도 {c['confidence']})")
        w("")
        rows = [
            ("대상", c.get("target")),
            ("원가격", c["price_raw"]),
            ("통화", c["currency"] + (f" (환율 {c['fx']['rate_to_krw']:g}원, {c['fx']['as_of']} 기준)"
                                       if c["currency"] != "KRW" and c.get("fx") else "")),
            ("기간", f"{c['duration_weeks']:g}주" if c.get("duration_weeks") else None),
            ("총 시수", hours_text(c["total_hours"], c["hours_estimated"])
             + (f" — 근거: {c['hours_basis']}" if c.get("hours_basis") else "")),
            ("시간당 원가", won(c["price_per_hour_krw"])),
            ("커리큘럼", c.get("curriculum_summary")),
            ("TOPIK 보장", c.get("topik_claim")),
            ("모집 경로", c.get("channel")),
            ("차별점", c.get("differentiator")),
            ("소스 발행·수정일", c["published_at"]),
            ("확인 시점", c["checked_at"]),
            ("플래그", ", ".join(c["flags"]) or None),
            ("출처", source_links(c["source_urls"])),
        ]
        w("| 항목 | 내용 |")
        w("|---|---|")
        for k, v in rows:
            w(f"| {k} | {md_cell(v)} |")
        w("")

    w("## 시장 빈틈")
    w("")
    for i, g in enumerate(analysis.get("gaps", []), 1):
        refs = ", ".join(by_id[r]["name"] for r in g.get("refs", []) if r in by_id)
        w(f"### {i}. {g['title']}")
        w("")
        w(g["description"])
        w("")
        w(f"_근거: {refs}_")
        w("")

    p = analysis.get("proposal", {})
    w("## 우리 상품 제안 (1안)")
    w("")
    pph = round(p["price_krw"] / p["total_hours"]) if p.get("price_krw") is not None and p.get("total_hours") else None
    w("| 항목 | 내용 |")
    w("|---|---|")
    w(f"| 상품명 | {md_cell(p.get('name'))} |")
    w(f"| 대상 | {md_cell(p.get('target'))} |")
    w(f"| 커리큘럼 | {md_cell(p.get('curriculum'))} |")
    w(f"| 가격 | {won(p.get('price_krw'))} / {p.get('total_hours', '?')}h → 시간당 {won(pph)} "
      f"(시장 중앙값 {won(stats['pph_median'])}) |")
    w(f"| 차별점 | {md_cell(p.get('differentiator'))} |")
    if p.get("rationale"):
        w(f"| 근거 | {md_cell(p['rationale'])} |")
    w("")
    w("> 경쟁사의 구조·방식·가격 모델은 참고했지만 문구·교재·상품명은 새로 쓴다.")
    w("")

    w("## 미확인·추정 항목")
    w("")
    unknowns = []
    for c in comps:
        if c["hours_estimated"]:
            unknowns.append(f"{c['name']}: 시수 추정 — {c.get('hours_basis')}")
        if c["price_per_hour_krw"] is None:
            unknowns.append(f"{c['name']}: 시간당 원가 계산 불가 — {c['pph_unavailable_reason']}")
        if "pph_recomputed" in c["flags"]:
            unknowns.append(f"{c['name']}: 수집 단계 시간당 값({won(c['claimed_price_per_hour_krw'])})이 "
                            f"재계산값과 달라 재계산값을 사용")
        if c.get("verifier_notes"):
            unknowns.append(f"{c['name']}: 검증 메모 — {c['verifier_notes']}")
    for u in unknowns or ["없음"]:
        w(f"- {u}")
    w("")

    w("## 완료 판정")
    w("")
    for item in check_result["items"]:
        w(f"- [{'x' if item['ok'] else ' '}] {item['label']} — {item['detail']}")
    w("")

    w("## 부록 A — 신뢰도 C (본문 제외)")
    w("")
    if appendix:
        w("| 상품 | 원가격 | 사유 | 출처 |")
        w("|---|---|---|---|")
        for c in appendix:
            w(f"| {md_cell(c['name'])} | {md_cell(c['price_raw'])} | {', '.join(c['flags'])} | "
              f"{source_links(c['source_urls'])} |")
    else:
        w("없음")
    w("")

    w("## 부록 B — 제외 항목")
    w("")
    for e in findings["excluded"] or [{"name": "없음", "reason": ""}]:
        w(f"- {e['name']}" + (f": {e['reason']}" if e["reason"] else ""))
    w("")

    w("## 부록 C — 전체 출처")
    w("")
    for c in comps:
        for u in c["source_urls"]:
            w(f"- {c['name']} — <{u}> (발행 {c['published_at']}, 확인 {c['checked_at']})")
    w("")
    return "\n".join(lines)


def render_dashboard(findings, analysis, check_result):
    payload = {
        "meta": findings["meta"],
        "stats": findings["stats"],
        "competitors": findings["competitors"],
        "excluded": findings["excluded"],
        "analysis": analysis,
        "check": check_result,
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.read_text(encoding="utf-8")
    title = html.escape(f"{findings['meta']['keyword']} 경쟁 대시보드")
    return page.replace("__TITLE__", title).replace("__DATA_JSON__", data)


def run_checks(run_dir, findings, analysis_errors):
    comps = findings["competitors"]
    body = [c for c in comps if c["section"] == "body"]
    stats = findings["stats"]
    missing_src = [c["name"] for c in body if not c["source_urls"] or not c.get("checked_at")]
    stale_in_body = [c["name"] for c in body if {"stale", "date_unknown"} & set(c["flags"])]
    items = [
        {"label": "report.md와 dashboard.html 생성",
         "ok": (run_dir / "report.md").exists() and (run_dir / "dashboard.html").exists(),
         "detail": "render 단계 산출물"},
        {"label": "본문 모든 수치에 source_url + checked_at",
         "ok": not missing_src, "detail": "누락: " + ", ".join(missing_src) if missing_src else "누락 없음"},
        {"label": f"출처 확인 비율 {MIN_VERIFIED_RATIO:.0%} 이상",
         "ok": stats["verified_ratio"] >= MIN_VERIFIED_RATIO,
         "detail": f"{stats['verified_ratio']:.0%} (나머지는 부록·제외로 명시)"},
        {"label": f"{STALE_MONTHS}개월 넘은·날짜 불명 소스가 본문에 없음",
         "ok": not stale_in_body, "detail": ", ".join(stale_in_body) if stale_in_body else "없음"},
        {"label": "분석 결과의 모든 주장이 본문 항목을 근거로 참조",
         "ok": not analysis_errors, "detail": "; ".join(analysis_errors) if analysis_errors else "통과"},
        {"label": "검증 에이전트 통과",
         "ok": bool(findings["meta"].get("verified_by_agent")), "detail": "verification.json 기준"},
    ]
    return {"passed": all(i["ok"] for i in items), "items": items}


def load_run(run_dir):
    findings_path = run_dir / "findings.json"
    analysis_path = run_dir / "analysis.json"
    if not findings_path.exists():
        sys.exit("findings.json 없음 — merge를 먼저 실행")
    if not analysis_path.exists():
        sys.exit("analysis.json 없음 — 분석 에이전트를 먼저 실행")
    findings, analysis = load_json(findings_path), load_json(analysis_path)
    return findings, analysis, validate_analysis(analysis, findings)


def cmd_render(args):
    run_dir = Path(args.run_dir)
    findings, analysis, analysis_errors = load_run(run_dir)
    if analysis_errors:
        print("analysis.json 문제 (리포트에 표시됨):", file=sys.stderr)
        for e in analysis_errors:
            print(f"  - {e}", file=sys.stderr)
    # 산출물 존재 여부가 판정 항목이라 두 번 렌더한다: 먼저 쓰고, 판정하고, 판정을 넣어 다시 쓴다.
    for _ in range(2):
        result = run_checks(run_dir, findings, analysis_errors)
        (run_dir / "report.md").write_text(render_report(findings, analysis, result), encoding="utf-8")
        (run_dir / "dashboard.html").write_text(render_dashboard(findings, analysis, result), encoding="utf-8")
    print(f"{run_dir / 'report.md'}\n{run_dir / 'dashboard.html'}")


def cmd_check(args):
    run_dir = Path(args.run_dir)
    findings, _, analysis_errors = load_run(run_dir)
    result = run_checks(run_dir, findings, analysis_errors)
    for item in result["items"]:
        print(f"[{'PASS' if item['ok'] else 'FAIL'}] {item['label']} — {item['detail']}")
    print("완료" if result["passed"] else "미완료 — 위험물. 실패 항목을 해결할 것")
    sys.exit(0 if result["passed"] else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--keyword", required=True)
    p.add_argument("--date")
    p.add_argument("--out", default="output")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("validate")
    p.add_argument("file")
    p.set_defaults(func=cmd_validate)
    for name, func in (("merge", cmd_merge), ("render", cmd_render), ("check", cmd_check)):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.set_defaults(func=func)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
