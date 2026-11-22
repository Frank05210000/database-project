"""把 psql 的文字輸出畫成終端機風格的 PNG（CJK 佔兩格，對齊 psql 的排版）。
用法：python3 term2png.py out.png < text.txt"""
import sys, unicodedata
from PIL import Image, ImageDraw, ImageFont
text = sys.stdin.read().rstrip("\n").expandtabs(4)
SZ = 26
latin = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", SZ)
cjk = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", SZ)
CW = latin.getlength("M"); LH = int(SZ * 1.45); PAD = 28; BAR = 44
def wide(c): return unicodedata.east_asian_width(c) in "WF"
MAXC = 110   # 終端機寬度：超過就換行，和真正的終端機視窗一樣
def wrap(l):
    out, cur, w = [], "", 0
    for c in l:
        cw = 2 if wide(c) else 1
        if w + cw > MAXC:
            out.append(cur); cur, w = "", 0
        cur += c; w += cw
    out.append(cur)
    return out
lines = []
for l in text.split("\n"):
    parts = wrap(l)
    lines.append(parts[0])
    # 續行沿用原本那一行的顏色判斷
    lines += [("\x00" + p) for p in parts[1:]]
cols = max(sum(2 if wide(c) else 1 for c in l.lstrip("\x00")) for l in lines)
W = int(PAD * 2 + cols * CW); H = BAR + PAD * 2 + LH * len(lines)
img = Image.new("RGB", (W, H), "#1e1f29"); d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, BAR], fill="#2d2f3b")
for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    d.ellipse([18 + i * 26, 14, 34 + i * 26, 30], fill=col)
d.text((W / 2, BAR / 2), "psql — fuwa@PostgreSQL 16", fill="#b8bccb", font=latin, anchor="mm")
y = BAR + PAD
prev = "#e6e6e6"
for l in lines:
    x = PAD
    if l.startswith("\x00"):
        l = l[1:]; color = prev
    else:
        color = "#7ee787" if l.startswith(("fuwa=#","fuwa-#")) else ("#ff7b72" if l.startswith("ERROR") else "#e6e6e6")
    prev = color
    for c in l:
        f = cjk if wide(c) else latin
        d.text((x, y), c, fill=color, font=f)
        x += CW * (2 if wide(c) else 1)
    y += LH
img.save(sys.argv[1]); print(sys.argv[1], img.size)
