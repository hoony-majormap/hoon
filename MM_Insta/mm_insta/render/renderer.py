"""⑤ 렌더러 + G4 렌더 검사: script.json → HTML 템플릿 → PNG 캡처 → JPEG 6장 (기획안 §7, §8-4·8).

- 숫자는 여기서 facts 값으로 치환된다 (작가는 {fN}만 씀)
- G4: 글자 넘침·줄 수·캔버스 밖·폰트(Wanted Sans) 로드·이미지 로드 → 넘치면 글자 1단계 축소 후 재검사
"""
from __future__ import annotations

import copy
import io
import math
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from PIL import Image

from ..config import ASSETS_DIR, BRAND, CARD_H, CARD_W, FONT_SHRINK_STEP, JPEG_QUALITY, TEMPLATES_DIR
from ..models import fact_map, refs_in, resolve

TEMPLATE_FILES = {
    "hook": "01_hook.html.j2",
    "big_number": "02_big_number.html.j2",
    "detail": "03_detail.html.j2",
    "compare": "04_compare.html.j2",
    "action": "05_action.html.j2",
    "cta": "06_cta.html.j2",
    "trend_item": "trend_item.html.j2",
    "career": "career.html.j2",
}
BACKGROUNDS = {"hook": "navy", "big_number": "offwhite", "detail": "mint", "compare": "white", "action": "red",
               "cta": "navy", "career": "red"}
TREND_ITEM_BACKGROUNDS = ["offwhite", "mint", "white"]  # 유행 01·02·03
# BI '색상 활용 규정': 흰·네이비 배경 → 레드 로고 / 레드·민트 배경 → 화이트 로고
LOGOS = {"navy": "logo_text.png", "offwhite": "logo_text.png", "white": "logo_text.png",
         "red": "logo_text_white.png", "mint": "logo_text_white.png"}
FONTS = [(500, "WantedSans-Medium.woff2"), (600, "WantedSans-Medium.woff2"), (700, "WantedSans-Bold.woff2"),
         (800, "WantedSans-ExtraBold.woff2"), (900, "WantedSans-Black.woff2"), (400, "WantedSans-Regular.woff2")]

# 페이지 안에서 실행: 자동 맞춤(큰 숫자) → 넘침·줄 수·캔버스 밖 검사
CHECK_JS = r"""
() => {
  const W = 1080, H = 1350, issues = [];
  document.querySelectorAll('[data-autofit]').forEach(el => {
    el.style.fontSize = '';
    let fs = parseFloat(getComputedStyle(el).fontSize);
    const min = fs * 0.45;
    while (el.scrollWidth > el.clientWidth + 1 && fs > min) { fs -= 4; el.style.fontSize = fs + 'px'; }
  });
  const label = el => (el.className || el.tagName) + ' "' + el.textContent.trim().replace(/\s+/g, ' ').slice(0, 24) + '"';
  document.querySelectorAll('[data-fit]').forEach(el => {
    if (el.scrollWidth > el.clientWidth + 1) issues.push('가로 넘침: ' + label(el));
    const r = el.getBoundingClientRect();
    if (r.left < -1 || r.top < -1 || r.right > W + 1 || r.bottom > H + 1) issues.push('카드 밖: ' + label(el));
    const max = parseInt(el.dataset.maxLines || '0');
    if (max) {
      const t = el.querySelector('p') || el;
      const cs = getComputedStyle(t), lh = parseFloat(cs.lineHeight);
      if (lh) {
        const inner = t.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
        const lines = Math.round(inner / lh);
        if (lines > max) issues.push(lines + '줄 > ' + max + '줄: ' + label(el));
      }
    }
  });
  const content = document.querySelector('.content');
  if (content.scrollHeight > content.clientHeight + 1)
    issues.push('세로 넘침: 본문 ' + content.scrollHeight + 'px > ' + content.clientHeight + 'px');
  const imgs = [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src.split('/').pop());
  if (imgs.length) issues.push('이미지 로드 실패: ' + imgs.join(', '));
  return issues;
}
"""

FONT_JS = r"""
async () => {
  await document.fonts.ready;
  const loaded = [...document.fonts].filter(f => f.family.replace(/"/g, '') === 'Wanted Sans' && f.status === 'loaded');
  return {
    loaded_weights: [...new Set(loaded.map(f => f.weight))].sort(),
    check_700: document.fonts.check('700 40px "Wanted Sans"'),
    check_900: document.fonts.check('900 40px "Wanted Sans"'),
  };
}
"""


def _uri(path: Path) -> str:
    return path.resolve().as_uri()


def _fmt_date(iso: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{m.group(1)}.{int(m.group(2))}.{int(m.group(3))}" if m else iso


def _sources(fact_ids: set[str], facts: dict[str, dict]) -> list[str]:
    seen: dict[str, None] = {}
    for fid in sorted(fact_ids, key=lambda x: int(x[1:])):
        f = facts[fid]
        seen.setdefault(f"{f['source']}({_fmt_date(f['as_of'])})", None)
    return list(seen)


def _first_number(text: str) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    return float(m.group()) if m else None


def _deep_resolve(node, facts):
    if isinstance(node, str):
        return resolve(node, facts)
    if isinstance(node, list):
        return [_deep_resolve(v, facts) for v in node]
    if isinstance(node, dict):
        return {k: _deep_resolve(v, facts) for k, v in node.items()}
    return node


def _characters() -> dict[str, str]:
    """브랜드 원본 PNG가 있으면 우선, 없으면 placeholder SVG."""
    out = {}
    for who in ("may", "polar"):
        png = ASSETS_DIR / "characters" / f"{who}.png"
        out[who] = _uri(png if png.exists() else ASSETS_DIR / "characters" / f"{who}.svg")
    return out


def build_html(script: dict, html_dir: Path) -> list[Path]:
    facts = fact_map(script)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR / "cards"), autoescape=True, undefined=StrictUndefined)
    all_refs = refs_in(script["slides"]) | refs_in(script["caption"])
    trend = script.get("track") == "trend"
    src = script.get("source") or {}
    all_sources = _sources(all_refs, facts) if all_refs else []
    if trend and src.get("name"):
        all_sources = [f"{src['name']}({_fmt_date(src.get('date', ''))})"] + [s for s in all_sources if not s.startswith(src["name"])]
    common = {
        "asset_root": _uri(ASSETS_DIR),
        "template_root": _uri(TEMPLATES_DIR / "cards"),
        "fonts": FONTS,
        "characters": _characters(),
        "total": len(script["slides"]),
        "site": BRAND["site"],
        "next_label": script.get("next_label") or "다음 회",
        "all_sources": " · ".join(all_sources),
        "source_note": "내용은 메이저맵이 학생 눈높이로 재구성했습니다." if trend else "수치는 메이저맵이 재가공했습니다.",
    }
    html_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for raw in script["slides"]:
        slide = _deep_resolve(copy.deepcopy(raw), facts)
        layout = slide["layout"]
        refs = refs_in(raw)
        if layout == "big_number":
            m = re.match(r"^(.*?\d)([^\d]*)$", slide["number"])
            slide["number_main"], slide["number_unit"] = (m.group(1), m.group(2)) if m else (slide["number"], "")
            if slide["bar_left"]:
                left, right = _first_number(slide["bar_left"]) or 0, _first_number(slide["bar_right"]) or 0
                slide["bar_left_pct"] = round(100 * left / (left + right), 1) if left + right else 50
        if layout == "detail":
            filled = _first_number(slide["dots"]["filled"]) if slide["dots"]["filled"] else None
            total = _first_number(slide["dots"]["total"]) if slide["dots"]["total"] else None
            slide["dots_filled"] = int(filled or 0)
            slide["dots_total"] = int(total or 0)
            # 8개 이하는 한 줄, 그 이상은 두 줄
            slide["dots_cols"] = max(slide["dots_total"], 1) if slide["dots_total"] <= 8 else math.ceil(slide["dots_total"] / 2)
        source_line = ""
        if refs and layout != "cta":
            source_line = "출처: " + " · ".join(_sources(refs, facts)) + " · 메이저맵 재가공"
        elif trend and layout == "trend_item" and src.get("name"):
            source_line = f"출처: {src['name']}({_fmt_date(src.get('date', ''))}) · 메이저맵 재구성"
        bg = TREND_ITEM_BACKGROUNDS[(slide["index"] - 1) % 3] if layout == "trend_item" else BACKGROUNDS[layout]
        html = env.get_template(TEMPLATE_FILES[layout]).render(
            slide=slide, bg=bg, logo=LOGOS[bg], source_line=source_line, **common
        )
        path = html_dir / f"{slide['no']:02d}.html"
        path.write_text(html, encoding="utf-8")
        paths.append(path)
    return paths


def render(script: dict, out_dir: Path) -> tuple[list[Path], dict]:
    """HTML → PNG → JPEG. 반환: (JPEG 경로들, G4 리포트)."""
    from playwright.sync_api import sync_playwright

    html_paths = build_html(script, out_dir / "html")
    slides_report, jpgs = [], []
    with sync_playwright() as p:
        # Playwright 버전과 다른 Chromium을 쓸 때만 지정 (예: 사전 설치된 /opt/pw-browsers/chromium)
        browser = p.chromium.launch(executable_path=os.environ.get("MM_CHROMIUM_PATH") or None)
        page = browser.new_page(viewport={"width": CARD_W, "height": CARD_H}, device_scale_factor=1)
        for html in html_paths:
            page.goto(html.resolve().as_uri())
            fonts = page.evaluate(FONT_JS)
            issues = page.evaluate(CHECK_JS)
            scale = 1.0
            if issues:  # 글자 크기 1단계 축소 후 재검사
                scale = FONT_SHRINK_STEP
                page.evaluate(f"document.documentElement.style.setProperty('--fs', '{scale}')")
                issues = page.evaluate(CHECK_JS)
            png = page.screenshot(clip={"x": 0, "y": 0, "width": CARD_W, "height": CARD_H}, type="png")
            jpg = out_dir / f"{html.stem}.jpg"
            Image.open(io.BytesIO(png)).convert("RGB").save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True)
            jpgs.append(jpg)
            font_ok = fonts["check_700"] and fonts["check_900"] and bool(fonts["loaded_weights"])
            slides_report.append({
                "slide": int(html.stem),
                "font_scale": scale,
                "overflow": issues,
                "font": fonts,
                "pass": not issues and font_ok,
            })
        browser.close()
    return jpgs, g4_report(jpgs, slides_report)


def g4_report(jpgs: list[Path], slides_report: list[dict]) -> dict:
    violations = []
    if len(jpgs) != 6:
        violations.append(f"장 수 {len(jpgs)} ≠ 6")
    for jpg in jpgs:
        with Image.open(jpg) as im:
            if im.format != "JPEG":
                violations.append(f"{jpg.name}: 형식 {im.format} ≠ JPEG")
            if im.size != (CARD_W, CARD_H):
                violations.append(f"{jpg.name}: 해상도 {im.size} ≠ {(CARD_W, CARD_H)}")
    for s in slides_report:
        violations += [f"{s['slide']:02d}장: {msg}" for msg in s["overflow"]]
        if not (s["font"]["check_700"] and s["font"]["check_900"] and s["font"]["loaded_weights"]):
            violations.append(f"{s['slide']:02d}장: Wanted Sans 미로드 {s['font']}")
    return {
        "gate": "G4",
        "pass": not violations,
        "violations": violations,
        "warnings": [f"{s['slide']:02d}장: 글자 {s['font_scale']}배로 축소됨" for s in slides_report if s["font_scale"] < 1],
        "slides": slides_report,
    }
