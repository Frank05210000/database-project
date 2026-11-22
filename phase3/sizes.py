# 產生 4.5 節資料量估計表（schema 長度 × 預估 tuple 數）
# 欄位平均長度（bytes）：INT/SERIAL 4、SMALLINT 2、NUMERIC 8、BOOLEAN 1、DATE 4、TIMESTAMP 8；
# VARCHAR/TEXT 以平均實際長度估計（中文 UTF-8 每字 3 bytes）＋ 1 byte 長度標頭。
T = [
 # name, [(col, bytes)], rows, basis
 ("users", [("user_id",4),("loginid",13),("name",10),("password_hash",61),("email",26),("address",61),("phone",11),("is_active",1),("created_at",8)], 20033, "顧客 20,000、工作人員 30、平台管理員 3"),
 ("user_role", [("user_id",4),("role",7)], 20040, "每位使用者約 1 個角色，少數兼任"),
 ("store_staff", [("user_id",4),("store_id",4)], 30, "工作人員約 30 位，大多隸屬一間商店"),
 ("store", [("store_id",4),("name",19),("address",61),("email",26),("phone",11)], 10, "10 間門市"),
 ("product", [("product_id",4),("store_id",4),("name",37),("description",301),("category",10),("image_url",61),("price",8),("stock",4),("is_listed",1),("created_at",8),("updated_at",8)], 2000, "每店約 200 項商品"),
 ("cart_item", [("user_id",4),("product_id",4),("quantity",4),("added_at",8)], 9000, "3,000 位顧客購物車內平均 3 項"),
 ("orders", [("order_id",4),("user_id",4),("order_time",8),("recipient_name",10),("recipient_phone",11),("recipient_address",61),("subtotal",8),("discount_total",8),("tax",8),("shipping_fee",8),("total",8),("status",9),("paid_at",8)], 109500, "每日 300 筆，保存一年"),
 ("order_item", [("order_id",4),("item_no",2),("product_id",4),("product_name",37),("unit_price",8),("quantity",4),("event_discount",8)], 328500, "每筆訂單平均 3 項"),
 ("order_status_history", [("order_id",4),("seq_no",2),("status",9),("changed_at",8),("changed_by",4)], 416100, "每筆訂單平均 3.8 次狀態"),
 ("discount", [("discount_code",11),("discount_type",13),("description",61),("start_date",4),("end_date",4),("rate",8),("min_amount",8),("buy_qty",2),("free_qty",2),("is_active",1)], 200, "一年約 200 個折扣政策"),
 ("product_discount", [("product_id",4),("discount_code",11),("discount_type",14),("start_date",4),("end_date",4)], 1000, "特殊活動平均套用 5 項商品"),
 ("order_discount", [("order_id",4),("discount_code",11),("amount",8)], 164250, "每筆訂單平均套用 1.5 個折扣"),
 ("return_request", [("return_id",4),("order_id",4),("requested_at",8),("reason",61),("status",9),("processed_by",4),("processed_at",8),("reject_reason",31),("refund_total",8)], 3285, "約 3\\% 的訂單申請退貨"),
 ("return_item", [("return_id",4),("order_id",4),("item_no",2),("return_qty",4),("refund_amount",8)], 4928, "每筆申請平均退 1.5 項"),
 ("store_review", [("order_id",4),("store_id",4),("rating",2),("comment",91),("reviewed_at",8)], 28470, "約 20\\% 訂單評價、平均 1.3 間店"),
 ("system_setting", [("setting_key",15),("setting_value",6),("description",31)], 2, "稅率、基本運費"),
]
def fmt(b):
    return f"{b/1024/1024:,.2f} MB" if b >= 1024*1024 else f"{b/1024:,.1f} KB"
tot = 0
rows = []
for n, cols, r, basis in T:
    L = sum(c for _, c in cols); s = L * r; tot += s
    rows.append(f"\\at{{{n}}} & {L} & {r:,} & {fmt(s)} & {basis}\\\\\\hline")
open("size_table.tex","w").write("\n".join(rows) + f"\n\\multicolumn{{3}}{{|r|}}{{\\textbf{{合計}}}} & \\textbf{{{fmt(tot)}}} & 一年資料量\\\\\\hline\n")
print(open("size_table.tex").read())

# ---- 4.4 節：預期操作、頻率與系統負擔（格式同範例：系統負擔 = 頻率 × 表格資料量，worst case）----
rows_of = {n: r for n, _, r, _ in T}
OPS = [
 ("users","登入時以 loginid 驗證帳號",2250,"Query"),
 ("users","註冊新顧客",30,"Insert"),
 ("users","平台管理員修改資料、停用或啟用帳號",20,"Update"),
 ("user_role","登入時讀取角色",2250,"Query"),
 ("user_role","trigger 檢查顧客或工作人員角色",4800,"Query"),
 ("user_role","平台管理員指派或移除角色",2,"Insert"),
 ("store","商品頁與商店頁顯示商店資訊",6000,"Query"),
 ("store_staff","工作人員操作時查詢隸屬的商店",1000,"Query"),
 ("store_staff","平台管理員指定工作人員的商店",1,"Update"),
 ("product","關鍵字搜尋、瀏覽與商品詳細資料",45000,"Query"),
 ("product","結帳扣庫存、取消或退貨回補",920,"Update"),
 ("product","工作人員新增或修改商品",50,"Update"),
 ("cart_item","加入購物車、修改數量",4500,"Insert"),
 ("cart_item","顯示購物車",6000,"Query"),
 ("cart_item","移除商品、結帳後清空",1200,"Delete"),
 ("orders","確認付款後建立訂單",300,"Insert"),
 ("orders","顧客查詢歷史訂單、工作人員查詢訂單",1950,"Query"),
 ("orders","更新訂單狀態、取消訂單",920,"Update"),
 ("orders","日、週、月銷售報表",150,"Query"),
 ("order_item","建立訂單明細",900,"Insert"),
 ("order_item","查詢訂單明細、報表統計",2100,"Query"),
 ("order_status_history","trigger 自動記錄狀態變更",1220,"Insert"),
 ("order_status_history","顧客查看狀態歷程",500,"Query"),
 ("discount","購物車預估與結帳時查詢有效折扣",6300,"Query"),
 ("discount","工作人員新增、修改或停用折扣",10,"Update"),
 ("product_discount","商品頁顯示特殊活動折扣",45000,"Query"),
 ("product_discount","設定特殊活動適用商品",5,"Insert"),
 ("order_discount","記錄訂單套用的折扣",450,"Insert"),
 ("order_discount","查詢訂單金額明細",750,"Query"),
 ("return_request","申請退貨",9,"Insert"),
 ("return_request","查詢退貨申請",100,"Query"),
 ("return_request","審核退貨申請",9,"Update"),
 ("return_item","新增退貨明細、核准時寫入退款金額",28,"Update"),
 ("store_review","撰寫商店評價",60,"Insert"),
 ("store_review","商店頁顯示平均評分與評論",6000,"Query"),
 ("system_setting","計算金額時讀取稅率與基本運費",6300,"Query"),
]
out = []
for t, op, f, kind in OPS:
    r = rows_of[t]
    if kind == "Insert":
        out.append(f"\\at{{{t}}} & {op} & {f:,} & don't care & {f:,} Insert\\\\\\hline")
    else:
        out.append(f"\\at{{{t}}} & {op} & {f:,} & {r:,} & {f*r:,} {kind}\\\\\\hline")
open("freq_table.tex","w").write("\n".join(out) + "\n")
print(open("freq_table.tex").read()[:600])
