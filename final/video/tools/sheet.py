#!/usr/bin/env python3
"""Contact sheet of a recording: one frame near the end of each caption (+ the last frame).

    python3 final/video/tools/sheet.py s01_guest_search [s02_cart ...]   → work/sheet_<scene>.jpg
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V = Path(__file__).resolve().parents[1]
FF = "/opt/homebrew/bin/ffmpeg"
FONT = ImageFont.truetype(str(Path.home() / "Library/Fonts/NotoSansTC-Medium.ttf"), 22)

for scene in sys.argv[1:]:
    rec = V / "recordings" / scene
    caps = json.loads((rec / "captions.json").read_text())
    dur = float(subprocess.run(["/opt/homebrew/bin/ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(rec / "raw.mp4")], capture_output=True, text=True).stdout)
    pts = [(max(c["start"], c["end"] - 0.4), c["zh"]) for c in caps] + [(dur - 0.1, "(end)")]
    tiles = []
    for k, (t, label) in enumerate(pts):
        f = V / "work" / f"_f{k}.jpg"
        subprocess.run([FF, "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(rec / "raw.mp4"),
                        "-frames:v", "1", "-vf", "scale=760:-1", str(f)], check=True)
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 34], fill=(0, 0, 0))
        d.text((8, 4), f"{t:5.1f}s  {label}", font=FONT, fill=(255, 230, 120))
        tiles.append(im)
        f.unlink()
    cols = 2
    w, h = tiles[0].size
    sheet = Image.new("RGB", (w * cols, h * ((len(tiles) + cols - 1) // cols)), "white")
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    out = V / "work" / f"sheet_{scene}.jpg"
    sheet.save(out, quality=80)
    print(out)
