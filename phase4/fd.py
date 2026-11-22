# 產生 Section 5 的函數相依圖（TikZ）：屬性排成一列方框，主鍵加底線，
# 每條 FD 在方框下方畫一條橫線，從左邊（決定者）連到右邊（被決定的屬性），箭頭指向被決定的屬性。
# 用法：python3 fd.py  → 產生 fd_before.tex、fd_after.tex
import re

def esc(s):
    return s.replace("_", r"\_")

def rel(name, attrs, pk, fds, note=None):
    return dict(name=name, attrs=attrs, pk=pk, fds=fds, note=note)

BEFORE = [
 rel("USERS", ["user_id","loginid","name","password_hash","email","address","phone","is_active","created_at"], ["user_id"],
     [("FD1", ["user_id"], ["loginid","name","password_hash","email","address","phone","is_active","created_at"]),
      ("FD2", ["loginid"], ["user_id","name","password_hash","email","address","phone","is_active","created_at"])]),
 rel("USER_ROLE", ["user_id","role"], ["user_id","role"], []),
 rel("STORE", ["store_id","name","address","email","phone"], ["store_id"],
     [("FD1", ["store_id"], ["name","address","email","phone"])]),
 rel("STORE_STAFF", ["user_id","store_id"], ["user_id"],
     [("FD1", ["user_id"], ["store_id"])]),
 rel("PRODUCT", ["product_id","store_id","name","description","category","image_url","price","stock","is_listed","created_at","updated_at"], ["product_id"],
     [("FD1", ["product_id"], ["store_id","name","description","category","image_url","price","stock","is_listed","created_at","updated_at"])]),
 rel("CART_ITEM", ["user_id","product_id","quantity","added_at"], ["user_id","product_id"],
     [("FD1", ["user_id","product_id"], ["quantity","added_at"])]),
 rel("ORDERS", ["order_id","user_id","order_time","recipient_name","recipient_phone","recipient_address","subtotal","discount_total","tax","shipping_fee","total","status","paid_at"], ["order_id"],
     [("FD1", ["order_id"], ["user_id","order_time","recipient_name","recipient_phone","recipient_address","subtotal","discount_total","tax","shipping_fee","total","status","paid_at"]),
      ("FD2", ["subtotal","discount_total","tax","shipping_fee"], ["total"])]),
 rel("ORDER_ITEM", ["order_id","item_no","product_id","product_name","unit_price","quantity","event_discount"], ["order_id","item_no"],
     [("FD1", ["order_id","item_no"], ["product_id","product_name","unit_price","quantity","event_discount"]),
      ("FD2", ["order_id","product_id"], ["item_no","product_name","unit_price","quantity","event_discount"])]),
 rel("ORDER_STATUS_HISTORY", ["order_id","seq_no","status","changed_at","changed_by"], ["order_id","seq_no"],
     [("FD1", ["order_id","seq_no"], ["status","changed_at","changed_by"])]),
 rel("DISCOUNT", ["discount_code","discount_type","description","start_date","end_date","rate","min_amount","buy_qty","free_qty","is_active"], ["discount_code"],
     [("FD1", ["discount_code"], ["discount_type","description","start_date","end_date","rate","min_amount","buy_qty","free_qty","is_active"])]),
 rel("PRODUCT_DISCOUNT", ["product_id","discount_code","discount_type","start_date","end_date"], ["product_id","discount_code"],
     [("FD1", ["product_id","discount_code"], ["discount_type","start_date","end_date"]),
      ("FD2", ["discount_code"], ["discount_type","start_date","end_date"])], note="部分相依（違反 2NF）"),
 rel("ORDER_DISCOUNT", ["order_id","discount_code","amount"], ["order_id","discount_code"],
     [("FD1", ["order_id","discount_code"], ["amount"])]),
 rel("RETURN_REQUEST", ["return_id","order_id","requested_at","reason","status","processed_by","processed_at","reject_reason","refund_total"], ["return_id"],
     [("FD1", ["return_id"], ["order_id","requested_at","reason","status","processed_by","processed_at","reject_reason","refund_total"]),
      ("FD2", ["order_id"], ["return_id","requested_at","reason","status","processed_by","processed_at","reject_reason","refund_total"])]),
 rel("RETURN_ITEM", ["return_id","order_id","item_no","return_qty","refund_amount"], ["return_id","item_no"],
     [("FD1", ["return_id","item_no"], ["order_id","return_qty","refund_amount"]),
      ("FD2", ["return_id"], ["order_id"])], note="部分相依（違反 2NF）"),
 rel("STORE_REVIEW", ["order_id","store_id","rating","comment","reviewed_at"], ["order_id","store_id"],
     [("FD1", ["order_id","store_id"], ["rating","comment","reviewed_at"])]),
 rel("SYSTEM_SETTING", ["setting_key","setting_value","description"], ["setting_key"],
     [("FD1", ["setting_key"], ["setting_value","description"])]),
]

AFTER = [
 rel("ORDERS", ["order_id","user_id","order_time","recipient_name","recipient_phone","recipient_address","subtotal","discount_total","tax","shipping_fee","status","paid_at"], ["order_id"],
     [("FD1", ["order_id"], ["user_id","order_time","recipient_name","recipient_phone","recipient_address","subtotal","discount_total","tax","shipping_fee","status","paid_at"])]),
 rel("PRODUCT_DISCOUNT", ["product_id","discount_code"], ["product_id","discount_code"], []),
 rel("RETURN_ITEM", ["order_id","item_no","return_qty","refund_amount"], ["order_id","item_no"],
     [("FD1", ["order_id","item_no"], ["return_qty","refund_amount"])]),
]

CH = 0.155   # 每個字元寬度 (cm)，\scriptsize 等寬字
def diagram(r):
    xs, x = {}, 0.0
    out = [r"\begin{tikzpicture}[font=\scriptsize\ttfamily, box/.style={draw,minimum height=0.55cm,inner sep=2pt,anchor=west}]"]
    note = rf"\quad{{\normalfont\color{{red!70!black}}{r['note']}}}" if r["note"] else ""
    out.append(rf"\node[anchor=south west,font=\small\bfseries\sffamily] at (0,0.32) {{{esc(r['name'])}{note}}};")
    for a in r["attrs"]:
        w = max(len(a) * CH + 0.25, 0.9)
        label = rf"\underline{{{esc(a)}}}" if a in r["pk"] else esc(a)
        out.append(rf"\node[box,minimum width={w:.2f}cm] at ({x:.2f},0) {{{label}}};")
        xs[a] = (x + w / 2)
        x += w
    y = -0.45
    n = len(r["fds"])
    for k, (tag, lhs, rhs) in enumerate(r["fds"]):
        y -= 0.34
        dx = (k - (n - 1) / 2) * 0.16          # 同一張表多條 FD 時左右錯開，避免線重疊
        X = {a: xs[a] + dx for a in lhs + rhs}
        pts = sorted(X.values())
        out.append(rf"\node[anchor=east,font=\scriptsize\sffamily\bfseries] at (-0.05,{y:.2f}) {{{tag}}};")
        out.append(rf"\draw ({pts[0]:.2f},{y:.2f}) -- ({pts[-1]:.2f},{y:.2f});")
        for a in lhs:   # 決定者：粗線，沒有箭頭
            out.append(rf"\draw[line width=1.1pt] ({X[a]:.2f},-0.28) -- ({X[a]:.2f},{y:.2f});")
        for a in rhs:   # 被決定的屬性：箭頭
            out.append(rf"\draw[-{{Stealth[length=4pt]}}] ({X[a]:.2f},{y:.2f}) -- ({X[a]:.2f},-0.28);")
    out.append(r"\end{tikzpicture}")
    body = "\n".join(out)
    return "\\par\\noindent\\begin{adjustbox}{max width=\\linewidth}\n" + body + "\n\\end{adjustbox}\\par\\medskip\n"

for fname, rels in (("fd_before.tex", BEFORE), ("fd_after.tex", AFTER)):
    open(fname, "w").write("\n".join(diagram(r) for r in rels))
    print(fname, len(rels))
