"""요일 규칙: 월·수·금 입시 / 화·목 트렌드 / 주말 없음."""
from datetime import date

from mm_insta import pipeline
from mm_insta.config import kicker_for, next_label, track_for


def test_weekday_tracks():
    week = [track_for(date(2026, 10, d)) for d in range(19, 26)]
    assert week == ["admissions", "trend", "admissions", "trend", "admissions", None, None]


def test_labels():
    assert kicker_for(date(2026, 10, 20), "trend") == "TUE · 요즘 뭐가 유행?"
    assert next_label(date(2026, 10, 19)) == "내일(화) 요즘 트렌드"
    assert next_label(date(2026, 10, 23)) == "다음 주 월요일 입시 브리핑"


def test_weekend_is_noop(capsys):
    assert pipeline.main(["--date", "2026-10-24"]) == 0
    assert "주말" in capsys.readouterr().out
