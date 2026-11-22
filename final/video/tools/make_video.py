#!/usr/bin/env python3
"""Cut recordings together per an edit list and burn in bilingual (zh + en) subtitles.

    python3 final/video/tools/make_video.py final/video/edit.json [--preview]

edit.json:
{
  "output": "out/FUWA_FUWA_Final_Demo.mp4",      # relative to final/video/
  "music": null,                                  # optional bgm file, looped + faded
  "music_volume": 0.12,
  "segments": [
    {"type": "title", "zh": "顧客購物流程", "en": "Customer Shopping Flow", "duration": 3},
    {"type": "clip", "src": "recordings/us04_cart", "start": 0, "end": null, "speed": 1.0},
    {"type": "clip", "src": "raw/screen.mov", "subs": [{"start": 1, "end": 4, "zh": "…", "en": "…"}]},
    {"type": "image", "src": "assets/psql_stock.png", "duration": 5, "subs": [{"start": 0, "end": 5, "zh": "…", "en": "…"}]}
  ]
}
- "src" is a recording dir (raw.mp4 + captions.json from record.py) or any video file.
- Captions are shifted/trimmed/sped up with their clip automatically; "subs" adds or
  overrides captions (times relative to the clip's own start, before trimming).
- Outputs: <output>.mp4 (subtitles burned in) + <output>.srt (bilingual soft subs).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FFMPEG = shutil.which("ffmpeg", path="/opt/homebrew/bin") or "ffmpeg"
FFPROBE = shutil.which("ffprobe", path="/opt/homebrew/bin") or "ffprobe"
VIDEO_DIR = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 30

FONT = next((p for p in [Path.home() / "Library/Fonts/NotoSansTC-Medium.ttf",
                         Path("/System/Library/Fonts/STHeiti Medium.ttc")] if p.exists()), None)
# FUWA FUWA palette (same as website / slides)
BROWN, CREAM, SAND, ORANGE, RED = (93, 64, 55), (255, 245, 230), (252, 223, 140), (232, 141, 103), (213, 107, 89)

SUB = dict(zh_size=46, en_size=32, max_w=1640, pad_x=34, pad_y=18, gap=8, bottom=56, radius=18, alpha=205)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(map(str, cmd))[:300]}\n{r.stderr[-2000:]}")
    return r.stdout


def duration(path):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def font(size):
    return ImageFont.truetype(str(FONT), size)


def wrap(text, f, max_w, draw):
    """Wrap by words for Latin text, by characters for CJK."""
    tokens = text.split(" ") if text.isascii() else list(text)
    sep = " " if text.isascii() else ""
    lines, cur = [], ""
    for t in tokens:
        cand = (cur + sep + t) if cur else t
        if draw.textlength(cand, font=f) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur); cur = t
    if cur:
        lines.append(cur)
    return lines


def render_sub(zh, en, path):
    """Rounded brown box, cream Chinese line(s), sand English line(s)."""
    s = SUB
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    fz, fe = font(s["zh_size"]), font(s["en_size"])
    rows = [(l, fz, CREAM) for l in wrap(zh, fz, s["max_w"], tmp)] if zh else []
    rows += [(l, fe, SAND) for l in wrap(en, fe, s["max_w"], tmp)] if en else []
    if not rows:
        return None
    heights = [f.getbbox("國Ag")[3] - f.getbbox("國Ag")[1] for _, f, _ in rows]
    widths = [tmp.textlength(t, font=f) for t, f, _ in rows]
    bw = int(max(widths)) + 2 * s["pad_x"]
    bh = sum(heights) + s["gap"] * (len(rows) - 1) + 2 * s["pad_y"]
    img = Image.new("RGBA", (bw + 24, bh + 24), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([12, 16, bw + 12, bh + 16], s["radius"], fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([12, 12, bw + 12, bh + 12], s["radius"], fill=BROWN + (s["alpha"],))
    y = 12 + s["pad_y"]
    for (t, f, c), h, w in zip(rows, heights, widths):
        d.text((12 + (bw - w) / 2, y - f.getbbox("國Ag")[1]), t, font=f, fill=c)
        y += h + s["gap"]
    img.save(path)
    return img.size


def render_title(seg, path):
    """Full-frame title card in the FUWA FUWA look (striped awning + cream background)."""
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    n, sw = 12, W / 12
    for i in range(n):
        d.rounded_rectangle([i * sw, -60, (i + 1) * sw, 120], 40, fill=RED if i % 2 else (246, 187, 111))
    if seg.get("kicker"):
        fk = font(40)
        d.text((W / 2, 400), seg["kicker"], font=fk, fill=ORANGE, anchor="mm")
    d.text((W / 2, 520), seg.get("zh", ""), font=font(104), fill=BROWN, anchor="mm")
    if seg.get("en"):
        d.text((W / 2, 640), seg["en"], font=font(52), fill=(138, 106, 93), anchor="mm")
    d.rounded_rectangle([W / 2 - 90, 720, W / 2 + 90, 730], 5, fill=ORANGE)
    img.save(path)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(edit_path, preview=False):
    edit = json.loads(Path(edit_path).read_text())
    out = VIDEO_DIR / edit.get("output", "out/demo.mp4")
    work = VIDEO_DIR / "work"
    shutil.rmtree(work, ignore_errors=True)
    (work / "subs").mkdir(parents=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    venc = ["-c:v", "libx264", "-preset", "ultrafast" if preview else "medium", "-crf", "26" if preview else "18",
            "-pix_fmt", "yuv420p", "-r", str(FPS)]
    norm = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,fps={FPS}"

    parts, caps, t = [], [], 0.0
    for i, seg in enumerate(edit["segments"]):
        part = work / f"part{i:03d}.mp4"
        if seg["type"] in ("title", "image"):
            if seg["type"] == "title":
                png = work / f"title{i:03d}.png"
                render_title(seg, png)
            else:                               # still image, e.g. a psql result screenshot
                png = VIDEO_DIR / seg["src"]
            dur = float(seg.get("duration", 3))
            fade = min(0.4, dur / 4)
            run([FFMPEG, "-y", "-loop", "1", "-t", f"{dur}", "-i", png,
                 "-vf", f"{norm},fade=t=in:d={fade},fade=t=out:st={dur - fade}:d={fade}", *venc, part])
            for c in seg.get("subs", []):
                caps.append({**c, "start": t + c["start"], "end": t + c["end"]})
        elif seg["type"] == "clip":
            src = VIDEO_DIR / seg["src"]
            video = src / "raw.mp4" if src.is_dir() else src
            own = json.loads((src / "captions.json").read_text()) if src.is_dir() and (src / "captions.json").exists() else []
            own = seg.get("subs", own) if seg.get("replace_subs") else own + seg.get("subs", [])
            start, speed = float(seg.get("start", 0)), float(seg.get("speed", 1))
            end = float(seg["end"]) if seg.get("end") is not None else duration(video)
            run([FFMPEG, "-y", "-ss", f"{start}", "-to", f"{end}", "-i", video, "-an",
                 "-vf", f"setpts=(PTS-STARTPTS)/{speed},{norm}", *venc, part])
            dur = (end - start) / speed
            for c in own:
                s, e = max(c["start"], start), min(c["end"], end)
                if e - s >= 0.3:
                    caps.append({**c, "start": t + (s - start) / speed, "end": t + (e - start) / speed})
        else:
            sys.exit(f"unknown segment type {seg['type']}")
        dur = duration(part)
        parts.append(part)
        t += dur
        print(f"  [{i:02d}] {seg['type']:5s} {dur:6.2f}s  {seg.get('zh') or seg.get('src')}")

    # concat (all parts share codec params → stream copy)
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = work / "joined.mp4"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    total = duration(joined)

    # captions → PNG overlays; small batches keep the filter graph manageable
    caps.sort(key=lambda c: c["start"])
    for j, c in enumerate(caps[:-1]):          # avoid overlap with the next caption
        c["end"] = min(c["end"], caps[j + 1]["start"])
    cur = joined
    BATCH = 24
    for b in range(0, len(caps), BATCH):
        chunk, ins, chain, last = caps[b:b + BATCH], [], [], "[0:v]"
        for k, c in enumerate(chunk):
            png = work / "subs" / f"{b + k:04d}.png"
            size = render_sub(c.get("zh", ""), c.get("en", ""), png)
            if not size:
                continue
            ins += ["-loop", "1", "-i", png]
            idx = len(ins) // 4
            x, y = (W - size[0]) // 2, H - SUB["bottom"] - size[1]
            tag = f"[v{k}]"
            chain.append(f"{last}[{idx}:v]overlay={x}:{y}:shortest=1:"
                         f"enable='between(t,{c['start']:.3f},{c['end']:.3f})'{tag}")
            last = tag
        if not chain:
            continue
        nxt = work / f"subbed{b // BATCH}.mp4"
        run([FFMPEG, "-y", "-i", cur, *ins, "-filter_complex", ";".join(chain), "-map", last, *venc, nxt])
        cur = nxt

    # optional background music
    final = out
    if edit.get("music"):
        vol = edit.get("music_volume", 0.12)
        run([FFMPEG, "-y", "-i", cur, "-stream_loop", "-1", "-i", VIDEO_DIR / edit["music"],
             "-filter_complex", f"[1:a]volume={vol},afade=t=in:d=1.5,afade=t=out:st={max(total - 2.5, 0)}:d=2.5[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final])
    else:
        shutil.copy(cur, final)

    with out.with_suffix(".srt").open("w") as f:
        for n, c in enumerate(caps, 1):
            f.write(f"{n}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c.get('zh', '')}\n{c.get('en', '')}\n\n")
    print(f"✓ {final}  ({total:.1f}s, {len(caps)} captions)\n✓ {out.with_suffix('.srt')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("edit", nargs="?", default=str(VIDEO_DIR / "edit.json"))
    ap.add_argument("--preview", action="store_true", help="fast low-quality encode")
    a = ap.parse_args()
    build(a.edit, a.preview)
