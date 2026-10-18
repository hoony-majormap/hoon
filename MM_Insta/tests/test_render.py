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
    assert "캐릿" in cta and "콜린스 사전" in cta and "추가 취재" in cta
    assert "출처: 캐릿" in (tmp_path / "html" / "02.html").read_text()
    # 리서치 팩트를 쓴 유행 장은 캐릿과 그 출처를 함께 적는다 + 꼬리표·칸 제목은 원고를 따른다
    item3 = (tmp_path / "html" / "03.html").read_text()
    assert "출처: 캐릿(2026.10.7) · 카파시 X 게시물(2025.2.2) · 콜린스 사전(2025.11.6)" in item3
    assert "팩트체크 02" in item3 and "어디서 왔냐면" in item3


def test_compare_versus_mode(tmp_path):
    from test_gates import load_seed

    _, script = load_seed("2026-10-28")
    paths = renderer.build_html(script, tmp_path)
    html = paths[3].read_text()
    assert 'class="table versus"' in html and ">vs<" in html and ">→<" not in html
    _, change = load_seed("2026-10-19")
    assert ">→<" in renderer.build_html(change, tmp_path / "c")[3].read_text()
