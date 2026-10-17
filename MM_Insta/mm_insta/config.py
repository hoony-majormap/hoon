"""브랜드·규격·모델·글자 수 제한 등 파이프라인 전역 설정 (기획안 §3.4, 부록 A)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "out"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """의존성 없이 .env를 읽는다 (이미 설정된 환경변수는 덮어쓰지 않음)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()  # 아래 os.environ 읽기 전에 .env 반영

# ── 브랜드 (BI 매뉴얼) ──────────────────────────────────────────
BRAND = {
    "red": "#EA5645",
    "navy": "#202B45",
    "mint": "#90C6B4",
    "gray_text": "#5B6478",
    "gray_bg": "#F4F5F7",
    "off_white": "#FAF7F2",
    "white": "#FFFFFF",
    "site": "majormap.net",
    "font_family": "Wanted Sans",
}

# ── 카드 규격 ───────────────────────────────────────────────────
CARD_W, CARD_H = 1080, 1350
SLIDE_COUNT = 6
JPEG_QUALITY = 92
FONT_SHRINK_STEP = 0.9  # G4 넘침 시 1단계 축소 비율

# ── LLM ─────────────────────────────────────────────────────────
MODEL_WRITER = os.environ.get("MM_MODEL_WRITER", "claude-sonnet-5-5")
MODEL_FACTS = os.environ.get("MM_MODEL_FACTS", "claude-sonnet-5-5")

# ── 시리즈 ──────────────────────────────────────────────────────
SERIES = {
    "MON_NEWS": {"kicker": "MON · 입시 뉴스 브리핑", "next": "내일(화) 학과탐구"},
}

# ── 슬롯별 글자 수 제한 (부록 A, 공백 제외 글자 수) ───────────────
LIMITS = {
    "kicker": 16,
    "headline_lines": 3,
    "headline_line": 9,
    "sub": 32,
    "bubble": 36,
    "bubbles_per_slide": 2,
    "big_line": 16,
    "label": 24,
    "title": 20,
    "panel_title": 16,
    "panel_note": 24,
    "compare_rows": 4,
    "compare_cell": 16,
    "action_title": 16,
    "action_desc": 24,
    "teaser": 24,
    "caption": 300,
    "hashtags": 5,
}

# G3 코드부: 겁주기·비하·학원 광고 톤 금칙어 (월 1회 사람 리뷰로 갱신, §13-5)
BANNED_PHRASES = [
    "망한다", "망해", "끝장", "인생 끝", "늦었다", "포기해", "바보", "멍청",
    "지잡", "지방대 따위", "학원 등록", "수강 신청", "할인", "선착순", "무조건 합격", "100% 합격",
    "씨발", "존나", "개빡",
]

# G2: 원문과 연속 어절 n개 이상 겹치면 실패
G2_NGRAM = 6
