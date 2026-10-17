"""오케스트레이터 — 요일별 소재 1건 → facts → 6장 원고 → 게이트 → JPEG 6장 + 캡션 → (Supabase)

요일 규칙: 월·수·금 = 입시 브리핑 / 화·목 = 요즘 트렌드 (주말은 게시 없음)

사용 예
  python -m mm_insta.pipeline --publish                         # 오늘(KST) 것 생성 → Supabase 저장 (Actions 크론)
  python -m mm_insta.pipeline --date 2026-10-20 --publish       # 특정 날짜 다시 만들기
  python -m mm_insta.pipeline --date 2026-10-20 --page <노션 페이지 id>   # 소재 지정
  python -m mm_insta.pipeline --date 2026-10-19 --topic-file fixtures/topics/trend_2028_rules.json \
      --offline fixtures/demo/trend_2028_rules                  # LLM 없이 저장된 원고로 렌더

종료 코드: 0 = 통과(또는 주말), 2 = 게이트 실패(게시 금지), 1 = 실행 오류
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import OUT_DIR, TRACKS, kicker_for, load_dotenv, next_label, track_for
from .gates.text_gates import feedback, run_text_gates
from .models import FactSheet, Topic, TrendWriterOutput, WriterOutput, fact_map, refs_in, resolve, to_script

KST = timezone(timedelta(hours=9))
USED_FILE = OUT_DIR / "used_topics.json"


class Steps:
    """단계별 로그 → gate_report.json · insta_posts.gate_report"""

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


class GateFailure(RuntimeError):
    pass


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-")[:40]


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _local_used() -> set[str]:
    return set(json.loads(USED_FILE.read_text())) if USED_FILE.exists() else set()


def load_topic(args, track: str, store) -> Topic:
    if args.topic_file:
        from .sources.local import load_topic as load

        topic = load(args.topic_file)
    else:
        from .sources import notion

        if args.page:
            topic = notion.fetch(args.page, track)
        else:
            used = store.used_source_ids(track) if store else _local_used()
            topic = notion.pick(track, used)
    topic.track = track
    return topic


def build_caption(script: dict, topic: Topic) -> str:
    """인스타 본문(출처 포함). 해시태그는 따로 복사할 수 있게 분리한다."""
    facts = fact_map(script)
    refs = sorted(refs_in(script["slides"]) | refs_in(script["caption"]), key=lambda x: int(x[1:]))
    sources = [topic.source_name] if topic.track == "trend" else []
    for fid in refs:
        if facts[fid]["source"] not in sources:
            sources.append(facts[fid]["source"])
    urls = []
    for u in [topic.url, *(facts[fid]["url"] for fid in refs)]:
        if u and u not in urls:
            urls.append(u)
    note = "내용은 메이저맵이 학생 눈높이로 재구성" if topic.track == "trend" else "수치는 메이저맵이 재가공"
    lines = [resolve(script["caption"], facts).strip(), ""]
    if sources:
        lines.append(f"📌 출처: {' · '.join(sources)} ({note})")
    lines += [f"원문: {u}" for u in urls]
    return "\n".join(lines).strip()


def generate(topic: Topic, post_date: date, out_dir: Path, offline: Path | None, steps: Steps, force_render=False) -> dict:
    """소재 → facts → 원고(재작성 1회) → G1~G3 → 렌더+G4. 결과 묶음을 돌려준다."""
    kicker, nxt = kicker_for(post_date, topic.track), next_label(post_date)

    print("② 팩트 추출")
    if offline:
        facts = FactSheet.model_validate_json((offline / "facts.json").read_text(encoding="utf-8")).facts
    else:
        from .agents.writers import extract_facts

        facts = steps.run("팩트 추출기", extract_facts, topic)
    _write_json(out_dir / "facts.json", {"facts": [f.model_dump() for f in facts]})
    print(f"   팩트 {len(facts)}개")

    print(f"③ 작가 May·Polar ({TRACKS[topic.track]['name']}) → ④ 검수 G1·G2·G3")
    schema = TrendWriterOutput if topic.track == "trend" else WriterOutput
    attempts, fb = [], None
    for attempt in range(1, (1 if offline else 2) + 1):  # 재작성 1회
        if offline:
            draft = schema.model_validate_json((offline / "writer.json").read_text(encoding="utf-8"))
        else:
            from .agents.writers import write_script

            draft = steps.run(f"작가 (시도 {attempt})", write_script, topic, facts, kicker, nxt, fb)
        script = to_script(topic, facts, draft, kicker, nxt, post_date.isoformat())
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

    jpgs, g4 = [], None
    if text_ok or force_render:
        print("⑤ 렌더 HTML → PNG → JPEG + G4 렌더 검사")
        from .render.renderer import render

        jpgs, g4 = steps.run("렌더러+G4", render, script, out_dir)
        print(f"   [G4] {'통과' if g4['pass'] else '실패'}" + "".join(f"\n      - {m}" for m in g4["violations"]))
        for w in g4["warnings"]:
            print(f"      · {w}")
    else:
        print("⑤ 렌더 생략 — 텍스트 게이트 실패")

    caption = build_caption(script, topic)
    (out_dir / "caption.txt").write_text(caption, encoding="utf-8")
    (out_dir / "hashtags.txt").write_text(" ".join(script["hashtags"]), encoding="utf-8")
    return {
        "script": script,
        "facts": facts,
        "caption": caption,
        "jpgs": jpgs,
        "attempts": attempts,
        "g4": g4,
        "pass": text_ok and g4 is not None and g4["pass"],
    }


def _row(topic: Topic, post_date: date, result: dict, mode: str) -> dict:
    facts = fact_map(result["script"])
    hook = next(s for s in result["script"]["slides"] if s["layout"] == "hook")
    return {
        "post_date": post_date.isoformat(),
        "track": topic.track,
        "title": topic.title,
        "headline": " ".join(resolve(line, facts) for line in hook["headline"]),
        "caption": result["caption"],
        "hashtags": result["script"]["hashtags"],
        "source_id": topic.id,
        "source_url": topic.url or None,
        "source_name": topic.source_name,
        "topic": topic.model_dump(),
        "facts": [f.model_dump() for f in result["facts"]],
        "script": result["script"],
        "mode": mode,
    }


def run(args) -> int:
    load_dotenv()
    post_date = date.fromisoformat(args.date) if args.date else datetime.now(KST).date()
    track = args.track or track_for(post_date)
    if not track:
        print(f"{post_date}은 주말이라 게시가 없습니다. (--track으로 강제 가능)")
        return 0

    store = None
    if args.publish:
        from .store import Store

        store = Store.from_env()
        if not store:
            raise RuntimeError("--publish에는 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY가 필요합니다.")
        prev = store.get(post_date.isoformat())
        version = (prev["version"] + 1) if prev else 1
        store.upsert({"post_date": post_date.isoformat(), "track": track, "status": "generating", "version": version, "error": None})

    steps = Steps()
    offline = Path(args.offline) if args.offline else None
    try:
        print(f"① 소재 읽기 — {post_date} {TRACKS[track]['name']}")
        topic = steps.run("소재", load_topic, args, track, store)
        out_dir = Path(args.out) if args.out else OUT_DIR / f"{post_date}_{track}_{_slug(topic.title)}"
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_json(out_dir / "topic.json", topic.model_dump())
        print(f"   {topic.title}\n   → {out_dir}")

        result = generate(topic, post_date, out_dir, offline, steps, args.force_render)
        report = {
            "post_date": post_date.isoformat(), "track": track, "topic_id": topic.id, "topic_title": topic.title,
            "mode": "offline-fixture" if offline else "llm", "pass": result["pass"],
            "attempts": result["attempts"], "g4": result["g4"], "steps": steps.items,
        }
        _write_json(out_dir / "gate_report.json", report)

        if store:
            row = _row(topic, post_date, result, "seed" if offline else "llm") | {"gate_report": report, "version": version}
            if result["pass"]:
                urls = [store.upload(p, f"{post_date}/v{version}/{p.name}") for p in result["jpgs"]]
                store.upsert(row | {"status": "ready", "image_urls": urls, "error": None})
            else:
                store.upsert(row | {"status": "failed", "error": "자동 검수 실패 — gate_report 참고"})
        if result["pass"] and not store and not args.topic_file:
            _write_json(USED_FILE, sorted(_local_used() | {topic.id}))
    except Exception as e:
        if store:
            store.upsert({"post_date": post_date.isoformat(), "track": track, "status": "failed",
                          "error": f"{type(e).__name__}: {e}", "gate_report": {"steps": steps.items}})
        raise

    print(f"\n{'✅ 모든 게이트 통과' if result['pass'] else '⛔ 게이트 실패 — 게시 금지'} · {out_dir}")
    return 0 if result["pass"] else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="메이저맵 인스타 카드뉴스 생성")
    ap.add_argument("--date", help="게시 날짜 YYYY-MM-DD (기본: 오늘 KST). 요일로 트랙이 정해진다")
    ap.add_argument("--track", choices=list(TRACKS), help="요일 규칙 대신 트랙 지정")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--page", help="소재로 쓸 노션 페이지 id (기본: 자동 선택)")
    src.add_argument("--topic-file", help="로컬 소재 JSON")
    ap.add_argument("--offline", help="facts.json·writer.json이 있는 폴더 (LLM 호출 생략)")
    ap.add_argument("--publish", action="store_true", help="Supabase에 이미지·게시물 저장")
    ap.add_argument("--out", help="출력 폴더 (기본: out/<날짜>_<트랙>_<제목>)")
    ap.add_argument("--force-render", action="store_true", help="텍스트 게이트 실패여도 디버그용으로 렌더")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except Exception as e:  # noqa: BLE001 — CLI 최상단에서 원인을 보여주고 종료
        print(f"\n❌ 실행 오류: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
