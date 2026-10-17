"""로컬 JSON 소재 파일 읽기 (오프라인 데모·테스트·노션 미연결 시)."""
from __future__ import annotations

import json
from pathlib import Path

from ..models import Topic


def load_topic(path: str | Path) -> Topic:
    return Topic.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
