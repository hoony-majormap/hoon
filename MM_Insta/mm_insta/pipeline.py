"""오케스트레이터 — 소재 1건 → facts.json → script.json → 게이트 → JPEG 6장 + 캡션 (MVP §9).

사용 예
  python -m mm_insta.pipeline --notion-latest                     # 아카이브에서 최신 고1·2 소재 자동 선택
  python -m mm_insta.pipeline --notion-page <페이지 id>
  python -m mm_insta.pipeline --topic-file fixtures/topics/trend_2028_rules.json
  python -m mm_insta.pipeline --topic-file fixtures/topics/trend_2028_rules.json \
      --offline fixtures/demo/trend_2028_rules                     # LLM 없이 저장된 facts/작가 원고로 렌더

종료 코드: 0 = 모든 게이트 통과, 2 = 게이트 실패(발행 금지), 1 = 실행 오류
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import OUT_DIR, SERIES, load_dotenv
from .gates.text_gates import feedback, run_text_gates
from .models import FactSheet, Topic, WriterOutput, fact_map, refs_in, resolve, to_script

KST = timezone(timedelta(hours=9))


class Steps:
    """단계별 로그 (1단계에서 Supabase run_steps 테이블로 그대로 옮긴다)."""

    def __init__(self):
        self.items: list[dict] = []

    def run(self, name: str, fn, *args, **kwargs):
        t0 = time.monotonic()
        print(f"  ▸ {name} …", flush=True)
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            self.items.append({"step": name, "status": "error", "duration_ms": int((time.monotonic() - t0) * 1000), "detail": str(e)})
            raise
        self.items.append({"step": name, "status": "ok", "duration_ms": int((time.monotonic() - t0) * 1000)})
        return result


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-")[:40]


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_topic(args) -> Topic:
    if args.topic_file:
        from .sources.local import load_topic as load

        return load(args.topic_file)
    from .sources import notion

    if args.notion_page:
        return notion.fetch_topic(args.notion_page)
    used = set(json.loads(USED_FILE.read_text())) if USED_FILE.exists() else set()
    return notion.pick_latest(used)


USED_FILE = OUT_DIR / "used_topics.json"


def build_caption(script: dict, topic: Topic) -> str:
    facts = fact_map(script)
    refs = refs_in(script["slides"]) | refs_in(script["caption"])
    sources = []
    for fid in sorted(refs, key=lambda x: int(x[1:])):
        s = facts[fid]["source"]
        if s not in sources:
            sources.append(s)
    urls = []
    for u in [topic.url, *(facts[fid]["url"] for fid in sorted(refs))]:
        if u and u not in urls:
            urls.append(u)
    lines = [resolve(script["caption"], facts).strip(), ""]
    lines.append("📌 출처: " + " · ".join(sources) + " (수치는 메이저맵이 재가공)")
    lines += [f"원문: {u}" for u in urls]
    lines += ["", " ".join(script["hashtags"])]
    return "\n".join(lines)


def run(args) -> int:
    load_dotenv()
    steps = Steps()
    print("① 소재 읽기")
    topic = steps.run("소재", load_topic, args)
    series = SERIES[topic.series]
    run_date = args.date or datetime.now(KST).strftime("%Y-%m-%d")
    out_dir = Path(args.out) if args.out else OUT_DIR / f"{run_date}_{_slug(topic.title)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "topic.json", topic.model_dump())
    print(f"   {topic.title}\n   → {out_dir}")

    offline = Path(args.offline) if args.offline else None
    next_teaser = topic.next_teaser_hint or series["next"]

    print("② 팩트 추출")
    if offline:
        facts = FactSheet.model_validate_json((offline / "facts.json").read_text(encoding="utf-8")).facts
    else:
        from .agents.writers import extract_facts

        facts = steps.run("팩트 추출기", extract_facts, topic)
    _write_json(out_dir / "facts.json", {"facts": [f.model_dump() for f in facts]})
    print(f"   팩트 {len(facts)}개")

    print("③ 작가 May·Polar → ④ 검수 G1·G2·G3")
    attempts = []
    fb = None
    max_attempts = 1 if offline else 2  # 재작성 1회 (§6)
    for attempt in range(1, max_attempts + 1):
        if offline:
            draft = WriterOutput.model_validate_json((offline / "writer.json").read_text(encoding="utf-8"))
        else:
            from .agents.writers import write_script

            draft = steps.run(f"작가 (시도 {attempt})", write_script, topic, facts, series["kicker"], next_teaser, fb)
        script = to_script(topic, facts, draft, series["kicker"])
        results = steps.run(f"G1·G2·G3 (시도 {attempt})", run_text_gates, script, topic)
        attempts.append({"attempt": attempt, "gates": results})
        for r in results:
            print(f"   [{r['gate']}] {'통과' if r['pass'] else '실패'}" + "".join(f"\n      - {m}" for m in r["violations"]))
        if all(r["pass"] for r in results):
            break
        fb = feedback(results)
    _write_json(out_dir / "script.json", script)
    _write_json(out_dir / "writer.json", draft.model_dump())
    text_ok = all(r["pass"] for r in attempts[-1]["gates"])

    g4 = None
    if text_ok or args.force_render:
        print("⑤ 렌더 HTML → PNG → JPEG + G4 렌더 검사")
        from .render.renderer import render

        jpgs, g4 = steps.run("렌더러+G4", render, script, out_dir)
        print(f"   [G4] {'통과' if g4['pass'] else '실패'}" + "".join(f"\n      - {m}" for m in g4["violations"]))
        for w in g4["warnings"]:
            print(f"      · {w}")
        print(f"   {len(jpgs)}장: " + ", ".join(p.name for p in jpgs))
    else:
        print("⑤ 렌더 생략 — 텍스트 게이트 실패 (1단계에서는 여기서 예비 소재로 교체)")

    (out_dir / "caption.txt").write_text(build_caption(script, topic), encoding="utf-8")
    passed = text_ok and g4 is not None and g4["pass"]
    report = {
        "run_date": run_date,
        "series": topic.series,
        "topic_id": topic.id,
        "topic_title": topic.title,
        "mode": "offline-fixture" if offline else "llm",
        "pass": passed,
        "attempts": attempts,
        "g4": g4,
        "steps": steps.items,
    }
    _write_json(out_dir / "gate_report.json", report)

    if passed and not args.topic_file:
        used = set(json.loads(USED_FILE.read_text())) if USED_FILE.exists() else set()
        _write_json(USED_FILE, sorted(used | {topic.id}))

    print(f"\n{'✅ 모든 게이트 통과' if passed else '⛔ 게이트 실패 — 발행 금지'} · {out_dir}")
    return 0 if passed else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="메이저맵 인스타 카드뉴스 생성 (MVP)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--notion-latest", action="store_true", help="아카이브 DB에서 고1·2 키워드 최신 미사용 기사 1건")
    src.add_argument("--notion-page", help="아카이브 DB 페이지 id")
    src.add_argument("--topic-file", help="로컬 소재 JSON")
    ap.add_argument("--offline", help="facts.json·writer.json이 있는 폴더 (LLM 호출 생략)")
    ap.add_argument("--out", help="출력 폴더 (기본: out/<날짜>_<제목>)")
    ap.add_argument("--date", help="실행 날짜 YYYY-MM-DD (기본: 오늘 KST)")
    ap.add_argument("--force-render", action="store_true", help="텍스트 게이트 실패여도 디버그용으로 렌더")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except Exception as e:  # noqa: BLE001 — CLI 최상단에서 원인을 보여주고 종료
        print(f"\n❌ 실행 오류: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
