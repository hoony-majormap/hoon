"""⑤ 렌더러 + G4 — 실제 헤드리스 브라우저로 렌더 (Chromium 없으면 건너뜀)."""
from __future__ import annotations

import pytest
from PIL import Image

from mm_insta.config import load_dotenv
from test_gates import load

load_dotenv()
renderer = pytest.importorskip("mm_insta.render.renderer")
pytest.importorskip("playwright.sync_api")


def test_demo_renders_six_jpegs_and_passes_g4(tmp_path):
    _, script = load("trend_2028_rules")
    jpgs, g4 = renderer.render(script, tmp_path)
    assert g4["pass"], g4["violations"]
    assert len(jpgs) == 6
    for p in jpgs:
        with Image.open(p) as im:
            assert (im.format, im.size) == ("JPEG", (1080, 1350))
    assert all(s["font"]["check_900"] for s in g4["slides"])  # Wanted Sans 로드


def test_g4_catches_overflow_after_shrink(tmp_path):
    _, script = load("trend_2028_rules")
    script["slides"][0]["headline"][1] = "아주아주아주아주길어서넘치는헤드라인"
    _, g4 = renderer.render(script, tmp_path)
    assert not g4["pass"]
    assert any("01장" in v and "가로 넘침" in v for v in g4["violations"])
    assert g4["slides"][0]["font_scale"] < 1  # 1단계 축소를 시도했음


def test_trend_renders_and_credits_source(tmp_path):
    from test_gates import load_seed

    _, script = load_seed("2026-10-20")
    jpgs, g4 = renderer.render(script, tmp_path)
    assert g4["pass"], g4["violations"]
    cta = (tmp_path / "html" / "06.html").read_text()
    assert "캐릿" in cta and "학생 눈높이로 재구성" in cta
    assert "출처: 캐릿" in (tmp_path / "html" / "02.html").read_text()
