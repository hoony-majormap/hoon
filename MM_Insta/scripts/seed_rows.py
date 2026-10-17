"""out/seed/<날짜>/ 결과물 → insta_posts 행 (JSON + SQL). 초기 1주치 시드용.

이미지는 웹앱 public/seed/<날짜>/ 에 함께 배포하고 image_urls는 상대경로로 둔다.
  python scripts/seed_rows.py            # supabase/seed/insta_posts_seed.{json,sql} 생성
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mm_insta.models import Topic, fact_map, resolve  # noqa: E402

DAYS = ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]


def row(day: str) -> dict:
    out = ROOT / "out/seed" / day
    topic = Topic.model_validate_json((out / "topic.json").read_text())
    script = json.loads((out / "script.json").read_text())
    report = json.loads((out / "gate_report.json").read_text())
    assert report["pass"], f"{day} 게이트 실패 — 시드로 쓸 수 없음"
    facts = fact_map(script)
    hook = next(s for s in script["slides"] if s["layout"] == "hook")
    return {
        "post_date": day,
        "track": topic.track,
        "status": "ready",
        "title": topic.title,
        "headline": " ".join(resolve(line, facts) for line in hook["headline"]),
        "caption": (out / "caption.txt").read_text(),
        "hashtags": script["hashtags"],
        "image_urls": [f"/seed/{day}/{i:02d}.jpg" for i in range(1, 7)],
        "source_id": topic.id,
        "source_url": topic.url or None,
        "source_name": topic.source_name,
        "topic": topic.model_dump(),
        "facts": script["facts"],
        "script": script,
        "gate_report": report,
        "mode": "seed",
        "version": 1,
    }


def sql_literal(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list) and all(isinstance(x, str) for x in v) and v is not None:
        return "array[" + ",".join(sql_literal(x) for x in v) + "]::text[]" if v else "'{}'::text[]"
    if isinstance(v, (dict, list)):
        return "'" + json.dumps(v, ensure_ascii=False).replace("'", "''") + "'::jsonb"
    return "'" + str(v).replace("'", "''") + "'"


def main():
    rows = [row(d) for d in DAYS]
    dest = ROOT / "supabase/seed"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "insta_posts_seed.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    cols = list(rows[0])
    jsonb_cols = {"topic", "facts", "script", "gate_report"}
    stmts = []
    for r in rows:
        vals = []
        for c in cols:
            v = r[c]
            vals.append(sql_literal(v) if c not in jsonb_cols else "'" + json.dumps(v, ensure_ascii=False).replace("'", "''") + "'::jsonb")
        stmts.append(
            f"insert into public.insta_posts ({', '.join(cols)}) values ({', '.join(vals)})\n"
            f"on conflict (post_date) do nothing;"
        )
    (dest / "insta_posts_seed.sql").write_text("\n\n".join(stmts) + "\n")
    print(f"{len(rows)}행 → {dest}")


if __name__ == "__main__":
    main()
