# FUWA FUWA e-Shop：Phase 3 開發計畫

依據：期中簡報（衝突時為準）、`phase2/srs.tex`（US-01～19、BR-01～26、DR-01～14）、`phase2/schema.sql`。

## 1. 架構

```
瀏覽器 ── React 18 + TS + Vite（fuwafuwa-shop/，同一個網站依角色顯示三種介面）
   │  /api/*（Vite proxy）
FastAPI（backend/）── JWT 登入、依角色授權（deps.require_role）
   │  SQLAlchemy 2 + psycopg 3
PostgreSQL 16（db/init/：01 schema、02 trigger、03 種子資料）
```

| 介面 | 路由前綴 | 角色 | 子系統 |
|---|---|---|---|
| 顧客購物介面 | `/`、`/product/:id`、`/cart`、`/order`、`/my-orders`、`/stores` | 訪客、customer | PMS、STS、SCS、OMS |
| 工作人員管理介面 | `/staff/*` | staff | PMS、OMS、DMS、RSS |
| 平台管理介面 | `/admin/*` | admin | AAS |

一位使用者可以同時有多種角色（`user_role`）；登入後頁首依角色顯示可進入的介面。
目前工作人員可以管理所有商店，各店獨立權限屬未來擴充。

## 2. 以簡報為準的需求調整

- 平台管理員可新增、查詢、修改使用者帳號（任何角色），指派或移除 customer、staff、admin 角色，停用或啟用帳號。
- 系統至少保留一位啟用中的平台管理員（trigger `trg_keep_one_admin`）；管理員不能停用自己或移除自己的 admin 角色。
- 初始資料：`admin`（admin）、`staff`（staff）、`manager`（staff＋admin）、`alice`、`bob`、`carol`（customer，carol 已停用）。

## 3. 商業規則落實位置

| 規則 | 後端 | 資料庫 |
|---|---|---|
| BR-06 庫存 | `services/orders.checkout` SELECT … FOR UPDATE | `stock >= 0` CHECK、`cart_item_check` trigger |
| BR-07 至少一項 | 結帳同一交易寫入訂單與明細 | — |
| BR-09～BR-17 金額 | `services/pricing.quote`（購物車預覽與結帳共用） | discount 的 CHECK |
| BR-13 期間不重疊 | 建立前先查衝突代碼（DMS-F-008） | `product_discount_check`、`discount_period_check` trigger（pg_advisory_xact_lock 防併發） |
| BR-18 代碼不可改 | 由 `discount_code_seq` 產生 | `discount_code_immutable` trigger |
| BR-19 狀態流轉 | `services/orders.advance_status / cancel_order` | `orders_status_check` trigger＋自動寫 `order_status_history` |
| BR-20 不可刪除 | 被引用時改下架/停用 | 外鍵 NO ACTION |
| BR-21 角色 | `deps.require_role` | `orders_insert_check`、`return_request_update` trigger |
| BR-23 報表分攤 | `routers/reports.py` | — |
| BR-24 評價 | `routers/stores.py` | `store_review_insert` trigger |
| BR-25 退貨 | `services/orders.create_return` | `return_request_insert`、`return_item_insert` trigger、UNIQUE(order_id)、FK (order_id, item_no) → order_item |
| BR-26 退款 | `services/orders.compute_refund / approve_return` | — |

金額欄位約定：`orders.shipping_fee` 存基本運費，`orders.discount_total` 為特殊活動＋季節性＋運費折扣合計，
總額不存欄位，由 `v_orders.total = subtotal − discount_total + tax + shipping_fee` 計算。BR-26 的「運費」指顧客實付運費（基本運費 − 運費折扣）。
部分數量退貨時，該項「扣除特殊活動折扣後的金額」依退貨數量比例計算。

### 正規化（3NF）

Phase 4 依課本正規化到 3NF，相對 Phase 2 的 schema 做了兩處拆分：
- `product_discount(product_id, discount_code)`：移除重複的 discount_type／start_date／end_date（原本部分相依於 discount_code），
  連帶移除 discount 上給複合外鍵用的 UNIQUE、EXCLUDE 與 btree_gist；BR-13 改由 trigger 檢查。
- `return_item(order_id, item_no, return_qty, refund_amount)`：移除 return_id（return_id → order_id 是部分相依），
  因為 `return_request.order_id` 是 UNIQUE，order_id 就能識別退貨申請。
- `orders` 刪除 `total`（BR-09 的 total = subtotal − discount_total + tax + shipping_fee 是遞移相依），
  改為表層級 `CHECK (subtotal - discount_total + tax + shipping_fee >= 0)`，總額由檢視表 `v_orders.total` 計算；
  ORM 以 `column_property` 用同一公式計算，API 仍回傳 total。

## 4. 工作拆分（並行、檔案不重疊）

| 編號 | 負責 | 檔案 |
|---|---|---|
| W0 核心 | 主 session | `db/init/*`、`backend/app/{config,db,models,security,deps,errors,main}.py`、`services/{pricing,orders}.py`、`tests/conftest.py`、前端 `src/api/*`、`src/contexts/AuthContext.tsx`、`src/App.tsx`、`docker-compose.yml` |
| W1 AAS/STS/PMS 後端 | subagent | `routers/{auth,admin,stores,products}.py`、`tests/test_{aas_admin,pms_sts}.py` |
| W2 SCS/OMS 後端 | subagent | `routers/{cart,orders,returns}.py`、`app/seed_orders.py`、`tests/test_{scs_oms,returns}.py` |
| W3 DMS/RSS 後端 | agy implementer | `routers/{discounts,reports}.py`、`tests/test_{dms,rss}.py` |
| W4 顧客介面 | subagent | `src/pages/*`（既有頁面）、`src/components/*`（既有）、`src/hooks/*`、`src/services/*`、`src/i18n/*` |
| W5 工作人員＋管理介面 | subagent | `src/pages/staff/*`、`src/pages/admin/*`、`src/components/Backoffice/*` |
| W6 素材 | agy generate_image | `public/images/products/*.png` |
| W7 整合 | 主 session | Dockerfile、啟動腳本、README、端對端驗證 |

## 5. API 契約（全部以 `/api` 開頭，錯誤格式 `{"detail": "BR-xx：訊息"}`）

工作人員沒有 `store_staff` 紀錄時為總部，保留跨店權限（含既有 staff、manager）。店員僅能維護本店商品（含更新後的商店），越權回 403；訂單與退貨清單限含本店商品的訂單，其他商店的詳細資料與狀態操作回 404。報表強制採本店篩選，摘要金額依本店比例分攤並扣除本店退款。店員僅能管理所有指定商品皆屬本店的特殊活動折扣，運費與季節性折扣操作回 403；折扣清單仍可跨店瀏覽。


違反商業規則回 **409**，未登入 **401**，角色不符 **403**，找不到 **404**，欄位格式錯 **422**。金額一律為整數（新台幣元）。

### AAS `/api/auth`
- `POST /register` `{loginid,name,password,email,address,phone?}` → 201 `User`（角色 customer）
- `POST /login` `{loginid,password}` → `{access_token, token_type:"bearer", user: User}`；停用帳號回 403
- `GET /me` → `User`；`PUT /me` `{name,email,address,phone}`；`PUT /me/password` `{old_password,new_password}`
- `User = {user_id, loginid, name, email, address, phone, is_active, roles: string[], created_at}`

### 平台管理 `/api/admin`（admin）
- `GET /users?q=&role=&is_active=` → `User[]`（q 比對 loginid、姓名、Email）
- `POST /users` `{loginid,name,password,email,address?,phone?,roles:string[],store_id?:int|null}` → 201 `User`
- `GET /users/{id}`、`PUT /users/{id}` `{name,email,address,phone,password?}`
- `PUT /users/{id}/roles` `{roles:string[]}`（整組取代，至少一個角色）
- `PUT /users/{id}/store` `{store_id:int|null}` → `User`（null 為總部；非 staff 回 409 BR-21，商店不存在回 404）
- `User`（含 `/api/auth/me`）新增 `store_id:int|null`、`store_name:string|null`。
- `PATCH /users/{id}/status` `{is_active:boolean}`
- `GET /stats` → `{users, customers, staff, admins, inactive}`

### STS `/api/stores`
- `GET /` → `Store[]`，`Store = {store_id,name,address,email,phone,product_count,avg_rating,review_count}`
- `GET /{id}` → `Store & {products: Product[], reviews: Review[]}`
- `POST /`（admin）`{name,address,email,phone}` → 201 `Store`（新增商店，SRS 未列，屬擴充）
- `PUT /{id}`（admin）`{name,address,email,phone}`
- `POST /{id}/reviews`（customer）`{order_id,rating,comment?}`；`Review = {order_id,store_id,rating,comment,reviewed_at,customer_name}`

### PMS `/api/products`
- `GET /?q=&category=&store_id=&sort=newest|price_asc|price_desc&include_unlisted=` → `Product[]`（include_unlisted 僅 staff）
- `GET /categories` → `string[]`
- `GET /{id}` → `Product & {also_bought: Product[]}`（下架商品僅 staff 可看）
- `POST /`、`PUT /{id}`（staff）`{store_id,name,description,category,image_url,price,stock,is_listed}`
- `DELETE /{id}`（staff）→ `{deleted:boolean, unlisted:boolean}`（被訂單引用時改下架，BR-20）
- `Product = {product_id,store_id,store_name,name,description,category,image_url,price,stock,is_listed,created_at,updated_at,event_discount: EventDiscount|null}`
- `EventDiscount = {discount_code,description,rate,buy_qty,free_qty,start_date,end_date}`

### SCS `/api/cart`（customer）
- `GET /` → `{items: [{product: Product, quantity, added_at, line_subtotal}], quote: Quote}`
- `POST /items` `{product_id, quantity}`（已在購物車則累加）、`PUT /items/{product_id}` `{quantity}`、`DELETE /items/{product_id}`、`DELETE /`
- 每個寫入操作都回傳與 `GET /` 相同的內容
- `Quote = {lines:[{product_id,product_name,store_id,unit_price,quantity,line_subtotal,event_discount,event_code,event_description,net_amount}], subtotal, event_discount, seasonal_discount, tax_base, tax_rate, tax, shipping_fee, shipping_discount, discount_total, total, applied_discounts:[{discount_code,discount_type,description,amount}]}`

### OMS `/api/orders`
- `GET /checkout-preview`（customer）→ `{quote: Quote, recipient: {name, phone, address}}`
- `POST /`（customer）`{recipient_name,recipient_phone,recipient_address}` → 201 `Order`
- `GET /mine`（customer）→ `OrderSummary[]`；`GET /?status=&date_from=&date_to=&q=`（staff）→ `OrderSummary[]`
- `GET /{id}`（本人或 staff）→ `Order`
- `POST /{id}/cancel`（本人）→ `Order`；`POST /{id}/status`（staff）`{status}` → `Order`
- `OrderSummary = {order_id,order_time,status,total,item_count,customer:{user_id,loginid,name},has_return,return_status}`
- `Order = OrderSummary & {recipient_name,recipient_phone,recipient_address,subtotal,discount_total,tax,shipping_fee,shipping_discount,paid_at, items:[{item_no,product_id,product_name,image_url,store_name,unit_price,quantity,line_subtotal,event_discount}], discounts:[{discount_code,discount_type,description,amount}], history:[{seq_no,status,changed_at,changed_by_name}], return_request: Return|null, next_status: string|null, can_cancel, can_return}`

### 退貨 `/api/returns`
- `POST /`（customer）`{order_id, reason, items:[{item_no, return_qty}]}` → 201 `Return`
- `GET /mine`（customer）、`GET /?status=`（staff）→ `Return[]`；`GET /{id}`（本人或 staff）
- `POST /{id}/approve`（staff）→ `Return`；`POST /{id}/reject`（staff）`{reject_reason}` → `Return`
- `Return = {return_id,order_id,requested_at,reason,status,processed_by_name,processed_at,reject_reason,refund_total,customer:{user_id,loginid,name},order_status,order_total, items:[{item_no,product_name,unit_price,quantity,return_qty,refund_amount}]}`

### DMS `/api/discounts`
- `GET /active`（公開）→ 今天有效的 `Discount[]`（給首頁顯示優惠）
- `GET /?type=&active_on=&q=`（staff）→ `Discount[]`
- `POST /`（staff）`{discount_type,description,start_date,end_date,rate?,min_amount?,buy_qty?,free_qty?,is_active?,product_ids?}` → 201，代碼由系統產生（`SHP-0100`、`SEA-0101`、`EVT-0102`）
- `GET /{code}`、`PUT /{code}`（同欄位，不可改代碼與類型）、`DELETE /{code}`（用過的回 409，BR-20）
- 特殊活動折扣期間與同商品重疊回 409，訊息含衝突的折扣代碼（DMS-F-008）
- `Discount = {discount_code,discount_type,description,start_date,end_date,rate,min_amount,buy_qty,free_qty,is_active,products:[{product_id,name}],used_count,is_current}`

### RSS `/api/reports`（staff）
- `GET /sales?period=day|week|month&date_from=&date_to=&store_id=` → `[{period_start, period_label, store_id, store_name, order_count, sales_total}]`（BR-23）
- `GET /top-products?date_from=&date_to=&store_id=&limit=10` → `[{store_id,store_name,product_id,product_name,quantity,revenue}]`
- `GET /summary?date_from=&date_to=` → `{order_count, sales_total, customer_count, pending_returns, orders_by_status:{status:count}}`

## 6. 完成標準

1. `./start.sh`（或 `docker compose up --build`）啟動 DB、後端、前端。
2. 瀏覽器走通：註冊/登入 → 搜尋 → 購物車 → 結帳（折扣、稅、運費）→ 訂單狀態 → 退貨審核；工作人員商品、折扣、報表；管理員帳號與角色。
3. `cd backend && .venv/bin/pytest` 全部通過，包含 BR 違規被拒絕的案例。
