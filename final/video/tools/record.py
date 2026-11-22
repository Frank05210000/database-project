#!/usr/bin/env python3
"""Scripted demo recorder (Playwright + Chrome DevTools screencast).

A scene file is a Python module with `async def run(d: Demo)`. Each `d.cap(zh, en)`
call opens a caption at the current moment and closes the previous one, so the
subtitles line up with what is on screen without any manual timing.

    python3 final/video/tools/record.py final/video/scenes/us04_cart.py
    python3 final/video/tools/record.py SCENE --headed --base http://localhost:5173

Output (final/video/recordings/<scene-name>/):
    raw.mp4         1920x1080 30fps, high quality (screencast JPEG q=92)
    captions.json   [{"start": s, "end": s, "zh": "...", "en": "..."}], seconds from start
"""
import argparse
import asyncio
import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

FFMPEG = shutil.which("ffmpeg", path="/opt/homebrew/bin") or "ffmpeg"
VIDEO_DIR = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 30          # output video size
VW, VH, DSF = 1280, 720, 1.5        # CSS viewport × device scale = 1920×1080 (UI appears 1.5× larger)

# Visible cursor + click ripple (headless screencasts have no OS cursor).
CURSOR_JS = r"""
(() => {
  if (window.__demoCursor) return; window.__demoCursor = true;
  const mk = () => {
    if (document.getElementById('__demo_cursor') || !document.body) return;
    const c = document.createElement('div');
    c.id = '__demo_cursor';
    c.innerHTML = '<svg width="34" height="34" viewBox="0 0 24 24"><path d="M4 2l15 11-6.5 1.2L16 21l-3 1.4-3.4-6.6L4 20z" fill="#fff" stroke="#222" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'-100px', top:'-100px', zIndex:2147483647,
      pointerEvents:'none', transform:'translate(-6px,-3px)', filter:'drop-shadow(0 2px 3px rgba(0,0,0,.35))'});
    document.body.appendChild(c);
    const p = JSON.parse(sessionStorage.getItem('__demo_xy') || 'null');
    if (p) { c.style.left = p[0] + 'px'; c.style.top = p[1] + 'px'; }
  };
  document.addEventListener('DOMContentLoaded', mk); mk();
  addEventListener('mousemove', e => {
    mk(); const c = document.getElementById('__demo_cursor'); if (!c) return;
    c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
    sessionStorage.setItem('__demo_xy', JSON.stringify([e.clientX, e.clientY]));
  }, true);
  addEventListener('mousedown', e => {
    const r = document.createElement('div');
    Object.assign(r.style, {position:'fixed', left:(e.clientX-22)+'px', top:(e.clientY-22)+'px', width:'44px', height:'44px',
      borderRadius:'50%', border:'3px solid #E88D67', background:'rgba(232,141,103,.25)', zIndex:2147483646,
      pointerEvents:'none', transition:'transform .45s ease-out, opacity .45s ease-out'});
    document.body.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 500);
  }, true);
})();
"""


class Demo:
    """Helpers a scene uses. Every action is slowed down so viewers can follow it."""

    def __init__(self, page, base, t0):
        self.page, self.base, self.t0 = page, base.rstrip("/"), t0
        self.captions, self._open = [], None
        self.x, self.y = VW / 2, VH / 2

    # ---- captions ----
    def now(self):
        return time.time() - self.t0

    def cap(self, zh, en):
        """Start a new bilingual caption (ends the previous one)."""
        self.end_cap()
        self._open = {"start": round(self.now(), 3), "zh": zh, "en": en}

    def end_cap(self):
        if self._open:
            self._open["end"] = round(self.now(), 3)
            self.captions.append(self._open)
            self._open = None

    # ---- actions ----
    async def wait(self, sec=1.0):
        await self.page.wait_for_timeout(int(sec * 1000))

    async def goto(self, path="/", wait=1.2):
        url = path if "://" in path else self.base + path
        await self.page.goto(url, wait_until="load")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:
            pass  # 首頁寵物動畫會持續請求圖片，等不到 networkidle 就繼續
        await self.page.mouse.move(self.x, self.y)
        await self.wait(wait)

    async def _loc(self, target):
        loc = self.page.locator(target) if isinstance(target, str) else target
        loc = loc.first
        await loc.scroll_into_view_if_needed()
        await loc.wait_for(state="visible")
        return loc

    async def move_to(self, target, steps=28):
        loc = await self._loc(target)
        b = await loc.bounding_box()
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        await self.page.mouse.move(x, y, steps=steps)
        self.x, self.y = x, y
        return loc

    async def click(self, target, pause=0.35, after=0.8):
        await self.move_to(target)
        await self.wait(pause)
        await self.page.mouse.down(); await self.page.mouse.up()
        await self.wait(after)

    async def hover(self, target, after=0.8):
        await self.move_to(target)
        await self.wait(after)

    async def type(self, target, text, delay=70, clear=True, after=0.5):
        await self.click(target, after=0.2)
        if clear:
            await self.page.keyboard.press("ControlOrMeta+A")
            await self.page.keyboard.press("Backspace")
        await self.page.keyboard.type(text, delay=delay)
        await self.wait(after)

    async def fill(self, target, value, after=0.6):
        """Set a field at once (date inputs, long text) after moving the cursor there."""
        loc = await self.move_to(target)
        await self.wait(0.25)
        await loc.click()
        await loc.fill(str(value))
        await self.wait(after)

    async def check(self, target, after=0.6):
        loc = await self.move_to(target)
        await self.wait(0.25)
        await loc.check()
        await self.wait(after)

    async def press(self, key, after=0.8):
        await self.page.keyboard.press(key)
        await self.wait(after)

    async def select(self, target, value, after=0.8):
        await self.move_to(target)
        await (await self._loc(target)).select_option(value)
        await self.wait(after)

    async def scroll(self, dy=500, steps=12, after=0.6):
        """Smooth wheel scroll; dy > 0 scrolls down."""
        for _ in range(steps):
            await self.page.mouse.wheel(0, dy / steps)
            await self.page.wait_for_timeout(30)
        await self.wait(after)

    async def scroll_to(self, target, after=0.8):
        loc = self.page.locator(target).first if isinstance(target, str) else target
        await loc.evaluate("e => e.scrollIntoView({behavior:'smooth', block:'center'})")
        await self.wait(after)

    async def highlight(self, target, sec=1.5):
        """Draw an orange box around an element for `sec` seconds."""
        loc = await self._loc(target)
        await loc.evaluate("""(e, ms) => { const o = e.style.outline, f = e.style.outlineOffset;
            e.style.outline = '4px solid #E88D67'; e.style.outlineOffset = '4px';
            setTimeout(() => { e.style.outline = o; e.style.outlineOffset = f; }, ms); }""", int(sec * 1000))
        await self.wait(sec)


def load_scene(path):
    spec = importlib.util.spec_from_file_location("scene", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def frames_to_mp4(frames, t0, t_end, fdir):
    """frames: [(wall_ts, jpg_path)] at irregular times (screencast only sends changes).
    Resample onto an exact 30 fps grid: output frame k shows the latest frame with ts <= t0 + k/FPS."""
    seq = fdir / "seq"
    seq.mkdir()
    i, n_out = 0, int((t_end - t0) * FPS) + 1
    for k in range(n_out):
        t = t0 + k / FPS
        while i + 1 < len(frames) and frames[i + 1][0] <= t:
            i += 1
        (seq / f"{k:06d}.jpg").hardlink_to(frames[i][1])
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(seq / "%06d.jpg"),
                    "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                           f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", str(fdir / "raw.mp4")], check=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--base", default="http://localhost:5173")
    ap.add_argument("--headed", action="store_true", help="show the browser window while recording")
    ap.add_argument("--out", help="output dir (default recordings/<scene name>)")
    a = ap.parse_args()

    scene_path = Path(a.scene).resolve()
    scene = load_scene(scene_path)
    out = Path(a.out) if a.out else VIDEO_DIR / "recordings" / scene_path.stem
    fdir = out / "frames"
    shutil.rmtree(out, ignore_errors=True)
    fdir.mkdir(parents=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=not a.headed,
                                          args=[f"--window-size={VW},{VH + 140}"])
        ctx = await browser.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=DSF,
                                        locale="zh-TW", **getattr(scene, "CONTEXT", {}))
        await ctx.add_init_script(CURSOR_JS)
        page = await ctx.new_page()
        page.on("dialog", lambda dlg: asyncio.ensure_future(dlg.accept()))   # e.g. "確定要取消此訂單嗎？"
        cdp = await ctx.new_cdp_session(page)

        frames, n = [], 0

        def on_frame(ev):
            nonlocal n
            n += 1
            fp = fdir / f"{n:06d}.jpg"
            fp.write_bytes(base64.b64decode(ev["data"]))
            frames.append((ev["metadata"]["timestamp"], fp))
            asyncio.ensure_future(cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]}))

        cdp.on("Page.screencastFrame", on_frame)
        if hasattr(scene, "setup"):          # e.g. log in before the clock starts
            await scene.setup(page, a.base)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                                "maxWidth": W, "maxHeight": H, "everyNthFrame": 1})
        await page.wait_for_timeout(300)
        t0 = min(f[0] for f in frames) if frames else time.time()
        d = Demo(page, a.base, t0)
        try:
            await scene.run(d)
            await d.wait(getattr(scene, "TAIL", 1.0))
        finally:
            d.end_cap()
            t_end = time.time()
            await cdp.send("Page.stopScreencast")
            await browser.close()

    if not frames:
        sys.exit("no frames captured")
    frames.sort()
    frames_to_mp4(frames, t0, t_end, fdir)
    (fdir / "raw.mp4").rename(out / "raw.mp4")
    (out / "captions.json").write_text(json.dumps(d.captions, ensure_ascii=False, indent=2))
    shutil.rmtree(fdir)
    print(f"✓ {out/'raw.mp4'}  ({t_end - t0:.1f}s, {n} frames, {len(d.captions)} captions)")


if __name__ == "__main__":
    asyncio.run(main())
