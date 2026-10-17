"""브랜드·규격·모델·글자 수 제한 등 파이프라인 전역 설정 (기획안 §3.4, 부록 A)."""
from __future__ import annotations

import os
from datetime import date, timedelta
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

# ── 요일별 트랙 (월·수·금 입시 / 화·목 트렌드) ───────────────────
TRACKS = {
    "admissions": {"name": "입시 브리핑", "kicker": "입시 브리핑"},
    "trend": {"name": "요즘 트렌드", "kicker": "요즘 뭐가 유행?"},
}
SCHEDULE = {0: "admissions", 1: "trend", 2: "admissions", 3: "trend", 4: "admissions"}  # weekday() 기준
WEEK_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEK_KO = "월화수목금토일"


def track_for(d: date) -> str | None:
    return SCHEDULE.get(d.weekday())


def kicker_for(d: date, track: str) -> str:
    return f"{WEEK_EN[d.weekday()]} · {TRACKS[track]['kicker']}"


def next_post(d: date) -> tuple[date, str]:
    n = d + timedelta(days=1)
    while n.weekday() not in SCHEDULE:
        n += timedelta(days=1)
    return n, SCHEDULE[n.weekday()]


def next_label(d: date) -> str:
    """06장 'NEXT ·' 예고 라벨. 예: '내일(화) 요즘 트렌드', '다음 주 월요일 입시 브리핑'."""
    n, track = next_post(d)
    when = f"내일({WEEK_KO[n.weekday()]})" if (n - d).days == 1 else f"다음 주 {WEEK_KO[n.weekday()]}요일"
    return f"{when} {TRACKS[track]['name']}"


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
    # 트렌드 트랙
    "trend_name": 14,
    "trend_text": 40,
    "career_field": 12,
    "career_reason": 26,
    "career_tip": 26,
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
