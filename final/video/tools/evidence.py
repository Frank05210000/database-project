#!/usr/bin/env python3
"""psql evidence cards for the demo video: run a query against the e-Shop DB (inside
BEGIN … ROLLBACK, so nothing changes) and lay the psql output on a 1920×1080 FUWA card.

    python3 final/video/tools/evidence.py      → assets/evidence/ev_<name>.png
Run it right after recording all scenes (the queries look at the rows the demo created).
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V = Path(__file__).resolve().parents[1]
ROOT = V.parents[1]
TERM2PNG = ROOT / "phase4" / "tools" / "term2png.py"
CONTAINER = "eshop-implementation-b6539e-db-1"
FONT = Path.home() / "Library/Fonts/NotoSansTC-Medium.ttf"
W, H = 1920, 1080
OUT = V / "assets" / "evidence"

CARDS = [
    ("checkout", "資料庫佐證：結帳後的訂單", "Evidence: the order created at checkout",
     "SELECT order_id, user_id, subtotal, discount_total, tax, shipping_fee, total\n  FROM v_orders WHERE order_id = 14;"),
    ("history", "資料庫佐證：trigger 寫入的狀態歷程", "Evidence: status history written by the trigger",
     "SELECT h.order_id, h.seq_no, h.status, h.changed_at, u.loginid AS changed_by\n"
     "  FROM order_status_history h JOIN users u ON u.user_id = h.changed_by\n"
     " WHERE h.order_id = 14 ORDER BY h.seq_no;"),
    ("returns", "資料庫佐證：退貨與退款金額", "Evidence: the approved return and its refund",
     "SELECT return_id, order_id, status, reason, refund_total\n  FROM return_request ORDER BY return_id DESC LIMIT 3;"),
    ("br13", "資料庫佐證：直接寫 SQL 也會被 BR-13 擋下", "Evidence: BR-13 also blocks raw SQL",
     "INSERT INTO product_discount (product_id, discount_code)\nVALUES (9, 'EVT-0004');   -- 貓抓板跳台 已有 EVT-0001"),
    ("roles", "資料庫佐證：帳號、角色與停用狀態", "Evidence: accounts, roles and deactivation",
     "SELECT u.loginid, u.name, u.is_active, string_agg(r.role, ', ' ORDER BY r.role) AS roles\n"
     "  FROM users u LEFT JOIN user_role r USING (user_id)\n"
     " WHERE u.loginid IN ('demo_dan', 'demo_staff', 'carol')\n GROUP BY u.user_id ORDER BY u.user_id;"),
]


def psql(sql):
    r = subprocess.run(["docker", "exec", "-i", CONTAINER, "sh", "-c",
                        'psql -X -q -U "$POSTGRES_USER" -d "$POSTGRES_DB"'],
                       input=f"BEGIN;\n{sql}\nROLLBACK;\n", capture_output=True, text=True)
    return (r.stdout + r.stderr).replace("psql:<stdin>:", "").strip("\n")


def card(name, zh, en, sql):
    out = psql(sql)
    lines = [l for l in out.splitlines() if not l.startswith(("ERROR:  current transaction", "WARNING"))]
    shown = "\n".join("fuwa=# " + l if i == 0 else "fuwa-# " + l for i, l in enumerate(sql.splitlines()))
    text = shown + "\n" + "\n".join(lines)
    term = OUT / f"_term_{name}.png"
    subprocess.run([sys.executable, str(TERM2PNG), str(term)], input=text, text=True, check=True)

    bg = Image.new("RGB", (W, H), "#FFF6E0")
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, W, 14], fill="#E07A5F")
    d.text((110, 70), zh, font=ImageFont.truetype(str(FONT), 58), fill="#6B3E26")
    d.text((112, 150), en, font=ImageFont.truetype(str(FONT), 34), fill="#B07A4F")
    t = Image.open(term)
    box_w, box_h = W - 220, H - 230 - 200          # leave the bottom free for subtitles
    s = min(box_w / t.width, box_h / t.height, 1.6)
    t = t.resize((int(t.width * s), int(t.height * s)), Image.LANCZOS)
    bg.paste(t, ((W - t.width) // 2, 230))
    dst = OUT / f"ev_{name}.png"
    bg.save(dst)
    term.unlink()
    print(dst, "\n" + text, "\n")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for c in CARDS:
        card(*c)
