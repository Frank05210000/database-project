# Final Demo 影片分鏡（草稿）

目標長度 6～8 分鐘。每一段對應一個場景檔 `scenes/<id>.py`，字幕直接寫在場景檔的 `d.cap(中文, English)` 裡，錄影時自動對時。
網站完成後只需要補上各場景的 CSS selector 和路徑；字幕文字可以照下面改。

每段最後會放一張 psql 查詢結果的截圖（`image` 段），用來證明資料真的寫進資料庫、限制是資料庫在檢查。這是資料庫課，這部分比畫面更重要。

| # | 場景檔 | 使用者故事 | 畫面 | 資料庫佐證（image 段） |
|---|---|---|---|---|
| 0 | （title） | — | 片頭：FUWA FUWA e-Shop／Database Systems Final Demo／組員 | — |
| 1 | `s01_guest_search.py` | US-01, US-02 | 訪客關鍵字搜尋 → 商品詳情 → 註冊 | `SELECT … FROM users WHERE loginid = …` |
| 2 | `s02_cart.py` | US-03, US-04 | 登入 → 加入購物車 → 改數量 → 移除 | `cart_item` 內容 |
| 3 | `s03_checkout.py` | US-05, US-06, US-07 | 結帳明細（小計、折扣、稅、運費、總額）→ 確認付款 | `product` 庫存減少、`orders` 狀態 received |
| 4 | `s04_orders.py` | US-08, US-09, US-10, US-11 | 歷史訂單、取消 received 訂單、退貨申請、評論 | `order_status_history`、`return_request` |
| 5 | `s05_staff_products.py` | US-12 | 工作人員新增／修改／刪除商品 | — |
| 6 | `s06_staff_orders.py` | US-13, US-14 | 訂單狀態 processing → shipping → closed；審核退貨 | `order_status_history` 依序寫入 |
| 7 | `s07_discounts.py` | US-15, US-16 | 新增三種折扣；特殊活動期間重疊 → 被拒絕 | trigger 的 `RAISE EXCEPTION BR-xx` 訊息 |
| 8 | `s08_reports.py` | US-17, US-18 | 日／週／月銷售報表、暢銷商品 | 對應 View V1、V2 |
| 9 | `s09_admin.py` | US-19、STS-F-005 | 管理員新增帳號、指派角色、新增商店、停用帳號 | `user_role` |
| 10 | （title） | — | 片尾：Thank you | — |

## 字幕草稿

> 中文一句以 20 字內為佳；英文一句 12 字內。一個畫面動作配一句。

### 0 片頭
- FUWA FUWA e-Shop：多商店線上購物系統｜FUWA FUWA e-Shop: a multi-store online shopping system

### 1 訪客搜尋與註冊（US-01、US-02）
- 訪客不用登入就能用關鍵字搜尋商品｜Guests can search products by keyword without logging in
- 點進商品可以看到價格、庫存與所屬商店｜Product pages show price, stock and the store
- 想購買時，先註冊成為顧客｜To buy, a guest first registers as a customer
- loginid 重複時，資料庫的 UNIQUE 限制會拒絕｜A duplicate loginid is rejected by a UNIQUE constraint

### 2 登入與購物車（US-03、US-04）
- 顧客用 loginid 與密碼登入｜The customer logs in with loginid and password
- 把商品加入購物車｜Add products to the shopping cart
- 數量必須大於零，且不能超過庫存｜Quantity must be positive and within stock
- 也可以把不要的商品移除｜Items can also be removed from the cart

### 3 結帳與下單（US-05、US-06、US-07）
- 結帳頁列出小計、折扣、稅、運費與總額｜Checkout shows subtotal, discounts, tax, shipping and total
- 有效期間內的折扣會自動套用｜Valid discounts are applied automatically
- 滿額免運、季節折扣與特殊活動可以同時使用｜Shipping, seasonal and special-event discounts can stack
- 確認付款後建立訂單，狀態為 received｜After payment the order is created as "received"
- 同一筆交易中扣除庫存並清空購物車｜Stock is deducted and the cart cleared in one transaction

### 4 訂單查詢、取消、退貨、評論（US-08～US-11）
- 顧客可以查詢歷史訂單與目前狀態｜Customers can view past orders and their status
- 尚未處理的訂單可以直接取消｜Orders still "received" can be cancelled directly
- 已處理的訂單只能申請退貨，每筆限一次｜Processed orders allow one return request
- 訂單完成後可以替商店評分與評論｜After completion, customers can rate the store

### 5 工作人員管理商品（US-12）
- 工作人員登入後進入管理後台｜Staff log in to the admin console
- 新增、修改、刪除商品與庫存｜Create, update and delete products and stock

### 6 處理訂單與退貨（US-13、US-14）
- 訂單狀態依序更新為 processing、shipping、closed｜Orders move to processing, shipping, then closed
- 每次狀態變更都記錄在 order_status_history｜Every change is logged in order_status_history
- 工作人員審核退貨申請，同意或拒絕｜Staff approve or reject return requests

### 7 折扣政策（US-15、US-16）
- 新增運費、季節性與特殊活動三種折扣｜Create shipping, seasonal and special-event discounts
- 系統自動產生唯一的折扣代碼｜The system assigns a unique discount code
- 同商品的特殊活動期間重疊時，trigger 會拒絕｜Overlapping special-event periods are rejected by a trigger

### 8 銷售報表（US-17、US-18）
- 各商店的日、週、月銷售報表｜Daily, weekly and monthly sales per store
- 報表資料來自檢視表 v_store_daily_sales｜Reports come from the view v_store_daily_sales
- 暢銷商品統計來自 v_product_sales｜Best sellers come from v_product_sales

### 9 平台管理員（US-19）
- 管理員可以新增帳號並指派角色｜Admins create accounts and assign roles
- 一個使用者可以同時有多個角色｜One user can hold several roles
- 平台管理員也可以新增商店｜Admins can also open a new store
- 違規帳號可以停用，停用後無法登入｜Deactivated accounts can no longer log in

### 10 片尾
- 感謝觀看｜Thank you for watching
