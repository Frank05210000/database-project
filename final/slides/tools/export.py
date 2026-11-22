#!/usr/bin/env python3
"""Export the HTML deck: one PNG per slide (export/slide_NN.png, 2560x1440),
a PDF (export/FUWA_FUWA_Final.pdf) and an image-based PPTX with speaker notes
from notes.json if present (export/FUWA_FUWA_Final.pptx).

    python3 final/slides/tools/export.py [--png-only] [--scale 2]
"""
import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

DECK = Path(__file__).resolve().parents[1]
OUT = DECK / "export"


async def shoot(scale):
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        page = await b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=scale)
        await page.goto((DECK / "index.html").as_uri())
        await page.wait_for_load_state("networkidle")
        await page.evaluate("document.fonts.ready")
        await page.add_style_tag(content="#bar,#help{display:none!important}.slide{transition:none!important}")
        n = await page.evaluate("document.querySelectorAll('.slide').length")
        paths = []
        for k in range(1, n + 1):
            await page.evaluate(f"location.hash='#{k}'")
            await page.wait_for_timeout(250)
            path = OUT / f"slide_{k:02d}.png"
            await page.screenshot(path=str(path))
            paths.append(path)
        await b.close()
    return paths


def build_pdf(paths):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims[0].save(OUT / "FUWA_FUWA_Final.pdf", save_all=True, append_images=ims[1:], resolution=192)


def build_pptx(paths):
    from pptx import Presentation
    from pptx.util import Emu
    notes = {}
    nf = DECK / "notes.json"
    if nf.exists():
        notes = {int(k): v for k, v in json.loads(nf.read_text()).items()}
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)   # 16:9
    for k, p in enumerate(paths, 1):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.shapes.add_picture(str(p), 0, 0, prs.slide_width, prs.slide_height)
        if notes.get(k):
            s.notes_slide.notes_text_frame.text = notes[k]
    prs.save(OUT / "FUWA_FUWA_Final.pptx")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-only", action="store_true")
    ap.add_argument("--scale", type=float, default=2)
    a = ap.parse_args()
    shots = asyncio.run(shoot(a.scale))
    print(f"✓ {len(shots)} slides → {OUT}")
    if not a.png_only:
        build_pdf(shots)
        build_pptx(shots)
        print("✓ FUWA_FUWA_Final.pdf, FUWA_FUWA_Final.pptx")
