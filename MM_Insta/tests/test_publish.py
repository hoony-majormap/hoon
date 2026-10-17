"""--publish: generating 행 → 이미지 6장 업로드 → ready 행 (가짜 Store로 확인)."""
from __future__ import annotations

from pathlib import Path

import pytest

from mm_insta import pipeline, store

ROOT = Path(__file__).resolve().parent.parent
pytest.importorskip("playwright.sync_api")


class FakeStore:
    def __init__(self):
        self.rows, self.uploads = [], []

    def get(self, post_date):
        return {"id": "x", "version": 2, "status": "ready"}

    def used_source_ids(self, track):
        return set()

    def upsert(self, row):
        self.rows.append(row)
        return row

    def upload(self, local, path):
        self.uploads.append(path)
        return f"https://example.supabase.co/storage/v1/object/public/insta-cards/{path}"


def test_publish_flow(monkeypatch, tmp_path):
    from mm_insta.config import load_dotenv

    load_dotenv()
    fake = FakeStore()
    monkeypatch.setattr(store.Store, "from_env", classmethod(lambda cls: fake))
    day = "2026-10-20"
    code = pipeline.main([
        "--date", day, "--publish", "--out", str(tmp_path),
        "--topic-file", str(ROOT / f"fixtures/seed/{day}/topic.json"),
        "--offline", str(ROOT / f"fixtures/seed/{day}"),
    ])
    assert code == 0
    assert fake.rows[0]["status"] == "generating" and fake.rows[0]["version"] == 3
    final = fake.rows[-1]
    assert final["status"] == "ready" and final["track"] == "trend" and final["version"] == 3
    assert fake.uploads == [f"{day}/v3/0{i}.jpg" for i in range(1, 7)]
    assert len(final["image_urls"]) == 6 and final["hashtags"][0] == "#메이저맵"
    assert "캐릿" in final["caption"] and "#" not in final["caption"]
    assert final["source_id"] == "3fc6af6c-8bcc-81f2-b4e3-cbba1f0cd34e"


def test_publish_records_failure(monkeypatch, tmp_path):
    fake = FakeStore()
    monkeypatch.setattr(store.Store, "from_env", classmethod(lambda cls: fake))
    monkeypatch.setattr(pipeline, "load_topic", lambda *a: (_ for _ in ()).throw(RuntimeError("노션 연결 실패")))
    assert pipeline.main(["--date", "2026-10-20", "--publish", "--out", str(tmp_path)]) == 1
    assert fake.rows[-1]["status"] == "failed" and "노션 연결 실패" in fake.rows[-1]["error"]


def test_store_key_headers():
    assert store.Store("https://x.supabase.co", "sb_secret_abc").headers == {"apikey": "sb_secret_abc"}
    assert "Authorization" in store.Store("https://x.supabase.co", "eyJhbGciOi.jwt").headers
