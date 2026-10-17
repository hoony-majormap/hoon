"""Supabase 저장소 — 카드 이미지(Storage 'insta-cards')와 게시물 행(insta_posts).

GitHub Actions에서 service_role 키로 쓴다. 웹은 publishable 키로 읽기만 한다.
필요 환경변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import requests

BUCKET = "insta-cards"
TABLE = "insta_posts"


class Store:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        # 새 형식(sb_secret_…)은 apikey 헤더로만, 예전 service_role JWT는 Bearer로도 보낸다
        self.headers = {"apikey": key} if key.startswith("sb_") else {"apikey": key, "Authorization": f"Bearer {key}"}

    @classmethod
    def from_env(cls) -> "Store | None":
        url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        return cls(url, key) if url and key else None

    # ── 행 ──
    def used_source_ids(self, track: str) -> set[str]:
        r = requests.get(
            f"{self.url}/rest/v1/{TABLE}",
            headers=self.headers,
            params={"select": "source_id", "track": f"eq.{track}", "status": "eq.ready"},
            timeout=30,
        )
        r.raise_for_status()
        return {row["source_id"] for row in r.json() if row.get("source_id")}

    def get(self, post_date: str) -> dict | None:
        r = requests.get(
            f"{self.url}/rest/v1/{TABLE}",
            headers=self.headers,
            params={"select": "id,version,status", "post_date": f"eq.{post_date}"},
            timeout=30,
        )
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

    def upsert(self, row: dict) -> dict:
        row = {**row, "updated_at": datetime.now(timezone.utc).isoformat()}
        r = requests.post(
            f"{self.url}/rest/v1/{TABLE}",
            headers={**self.headers, "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "post_date"},
            json=row,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()[0]

    # ── 이미지 ──
    def upload(self, local: Path, path: str) -> str:
        with open(local, "rb") as f:
            r = requests.post(
                f"{self.url}/storage/v1/object/{BUCKET}/{path}",
                headers={**self.headers, "Content-Type": "image/jpeg", "x-upsert": "true",
                         "Cache-Control": "max-age=31536000"},
                data=f.read(),
                timeout=60,
            )
        r.raise_for_status()
        return f"{self.url}/storage/v1/object/public/{BUCKET}/{path}"
