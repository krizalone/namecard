#!/usr/bin/env python3
"""
Render the favicon PNG/ICO set and the Open Graph image.

  site/favicon.svg  ->  site/favicon.ico              16/32/48 px
                        site/apple-touch-icon.png     180 px, full-bleed (iOS rounds it)
                        site/icon-192.png, icon-512.png   rounded square
                        site/icon-maskable-512.png    full-bleed, mark inside the safe zone
  tools/og.html     ->  site/og-image.jpg             1200x630 link-preview card

Requirements:  pip install pillow playwright
               Uses the installed Microsoft Edge or Google Chrome (no browser download).
Usage:         python render-images.py   (run build-vcf.py first so the portrait exists)
"""

import io
import re
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"


def launch(p):
    for channel in ("msedge", "chrome", None):
        try:
            return p.chromium.launch(channel=channel) if channel else p.chromium.launch()
        except Exception:
            continue
    raise SystemExit("No Chromium browser found. Install Edge/Chrome or run: playwright install chromium")


def svg_variant(svg: str, full_bleed: bool, mark_scale: float = 1.0) -> str:
    if full_bleed:
        svg = svg.replace('rx="14"', 'rx="0"')
    if mark_scale != 1.0:
        svg = svg.replace('<g class="mark">',
                          f'<g class="mark" transform="translate(32 32) scale({mark_scale}) translate(-32 -32)">')
    return svg


def render_svg(page, svg: str, size: int) -> Image.Image:
    page.set_viewport_size({"width": size, "height": size})
    svg = re.sub(r"<svg ", f'<svg width="{size}" height="{size}" ', svg, count=1)
    page.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
    png = page.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": size, "height": size})
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main():
    src = (SITE / "favicon.svg").read_text(encoding="utf-8")
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page()

        rounded = svg_variant(src, full_bleed=False)
        for size, name in ((192, "icon-192.png"), (512, "icon-512.png")):
            render_svg(page, rounded, size).save(SITE / name, optimize=True)
        render_svg(page, svg_variant(src, full_bleed=True), 180).convert("RGB").save(
            SITE / "apple-touch-icon.png", optimize=True)
        render_svg(page, svg_variant(src, full_bleed=True, mark_scale=.78), 512).convert("RGB").save(
            SITE / "icon-maskable-512.png", optimize=True)
        render_svg(page, rounded, 256).save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

        og = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        og.goto((ROOT / "tools" / "og.html").as_uri(), wait_until="networkidle")
        og.evaluate("document.fonts.ready.then(() => true)")
        og.wait_for_timeout(300)
        png = og.screenshot(clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        Image.open(io.BytesIO(png)).convert("RGB").save(
            SITE / "og-image.jpg", quality=86, optimize=True, progressive=True)
        browser.close()

    for name in ("favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
                 "icon-maskable-512.png", "og-image.jpg"):
        f = SITE / name
        print(f"wrote site/{name}  ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
