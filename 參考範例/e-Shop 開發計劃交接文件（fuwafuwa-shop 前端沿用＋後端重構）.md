# e-Shop 開發計劃交接文件（fuwafuwa-shop 前端沿用＋後端重構）

Oct 7, 2026 · @lin

## 背景與目標

決策：沿用 [fuwafuwa-shop](https://github.com/NariakiShipo/fuwafuwa-shop) 的前端畫面，後端改為自建 API 加關聯式資料庫，用來完成課程作業「e-Shop 線上電子商務系統」。

作業評分重點是資料庫設計：ER Diagram、Entity、Attribute、Primary Key、Foreign Key、Relationship、Cardinality、Integrity Constraints、Database Schema。網站功能完整度是次要的。

作業核心需求：

- 三種角色：顧客、工作人員、系統管理員（管理員可同時是工作人員）。工作人員與管理員資料預先存在於初始資料庫中。
- 以 loginid 加密碼登入；顧客自行註冊為選配。
- 顧客：搜尋商品、購物車加入與移除、結帳、查詢歷史訂單。
- 訂單總額 = 各商品小計 + 稅 + 運費 − 適用折扣。不需處理第三方支付。
- 工作人員：商品 CRUD、處理訂單並更新狀態、折扣政策 CRUD、銷售報表（日、週、月）。
- 三種折扣：運費折扣、季節性折扣（皆作用於整筆訂單）、特殊活動折扣（作用於指定商品）。每個折扣政策有唯一折扣代碼，三種可同時套用。
- 訂單狀態：received → processing → shipping → closed。
- 必存實體：使用者、商品、商店、訂單；loginid、productid、storeid、orderid、discount code 皆須唯一。
- 完整性限制：購買數量為大於 0 的整數且不超過庫存；同一商品同一期間至多一個特殊活動折扣，且期間不得重疊。
- 選配：訂單確認 Email、暢銷商品報表、商品與商店購買統計、商店評分評論、商品推薦。

## fuwafuwa-shop 現況

技術棧：React 18 + TypeScript + Vite + React Router v6，後端為 Firebase（Auth + Firestore），程式碼約 3,900 行。顧客端畫面完整，資料層多處未接上。

分層：pages → hooks / contexts（`useCart`、`useOrders`、`AuthContext`、`LanguageContext`）→ `services/` → Firebase。只有 `services/` 直接存取 Firestore，因此替換後端時主要改寫這一層。

路由：`/`、`/product/:id`、`/cart`、`/login`、`/order`、`/order-success/:orderId`、`/my-orders`、`/order/:orderId`。首頁上半部是寵物互動區（`PetRoom`），下半部是商品格（`ShopGrid`，僅有分類篩選）。

| Service | Firestore 集合 | 實際狀態 |
| --- | --- | --- |
| cartService | carts/{uid} | 運作中，經 useCart 呼叫 |
| orderService | orders/{自動 ID} | 運作中，經 useOrders 與 3 個頁面呼叫 |
| userService | users/{uid} | 文件從未建立：`createOrUpdateUser` 無人呼叫 |
| petService | userPets/{uid} | 未接上：`usePet` 無人使用 |
| productService | products/{id} | 未接上：商品寫死在 HomePage 與 ProductDetail |

已知問題（後端重構時一併處理或作為反例）：

- `useCart` 是 Hook 而非 Context，各元件各持一份 state，商品頁加入後導覽列數量不會更新。
- `createOrder` 依序執行 addDoc、更新使用者統計、清空購物車，三步非原子操作；金額在前端計算，規則只檢查 userId。
- 下單不檢查也不扣庫存；稅金與運費在 OrderPage 與 createOrder 各算一次；購物車被清空兩次。
- `petService.playWithPet` 使用 `(pet.energy || 100)`，energy 為 0 時會被當成 100。應改用 `??`。
- `productService.getProduct` 會更新 viewCount，但 firestore.rules 禁止寫入 products，一接上就會 permission-denied。
- cartService 的 localStorage 快取只寫不讀。
- 訂單狀態為 pending／processing／shipped／completed／cancelled，與作業規定不同。

## 與作業需求的差距

現有專案只涵蓋顧客端基本購物流程；角色、折扣、商店、報表與資料庫約束皆缺。根本問題是 Firestore 為 NoSQL，沒有外鍵、JOIN、UNIQUE、CHECK，無法呈現課程要求的資料庫設計。

| 需求 | 現況 |
| --- | --- |
| 三種角色與權限 | 缺：無 role 欄位 |
| loginid + 密碼登入 | 部分：以 Email 登入 |
| 顧客自行註冊（選配） | 部分：有 signup 函式，註冊連結為 href="#" |
| 商品搜尋 | 部分：僅分類篩選 |
| 購物車加入／移除 | 有 |
| 小計＋稅＋運費−折扣 | 部分：無折扣 |
| 歷史訂單 | 有 |
| 工作人員商品 CRUD | 缺 |
| 工作人員更新訂單狀態 | 缺 |
| 三種折扣政策與唯一代碼 | 缺：僅寫死滿 1000 免運 |
| 銷售報表（日、週、月） | 缺 |
| 商店實體 | 缺 |
| 訂單狀態 received→closed | 部分：名稱不同 |
| 數量為正整數且不超過庫存 | 缺 |
| 各編號唯一性約束 | 部分：僅靠文件 ID |

估計顧客端畫面約七成可沿用；工作人員與管理員介面需全部新寫。

## 討論過程與決策

1. 使用者請 AI 導讀 fuwafuwa-shop。AI 複製 repo 並讀過原始碼，說明分層架構、型別關係與結帳流程，指出商品寫死、寵物未存檔、useCart 狀態不同步等問題。
2. 使用者要求深入 services 層。AI 逐一分析五個 service，找出非原子建單、前端算金額、`||` 誤判 0、viewCount 違反安全規則等問題。
3. 使用者提供 e-Shop 作業說明並詢問是否符合。AI 判定差距很大，主因是 Firestore 無法呈現關聯式資料庫設計。
4. 使用者提議沿用 fuwafuwa-shop 當前端、重構後端，認為比重做實際。AI 同意，理由是只有 services 層碰資料庫，保留函式簽名即可替換。

已確定：

- 沿用 fuwafuwa-shop 前端（React + TypeScript + Vite）。
- 後端改為自建 REST API 加關聯式資料庫，捨棄 Firebase Auth 與 Firestore。
- 先完成 ER Diagram 與 SQL schema，再寫 API，最後改前端。

AI 提議、使用者尚未確認：

- 後端使用 Python：FastAPI + SQLAlchemy + PostgreSQL（或 SQLite）。理由是使用者熟悉 Python，且 FastAPI 會自動產生 API 文件。

## 開發計劃

四個階段依序進行，第一階段最重要，未定案前不寫 API。

### 階段 1：資料庫設計（評分核心）

產出 ER Diagram、SQL schema（DDL）、約束說明、初始資料（工作人員、管理員、商店、商品）。實體草案如下，欄位待依待釐清問題調整：

| 資料表 | 主鍵 | 主要欄位與外鍵 |
| --- | --- | --- |
| users | user\_id | loginid UNIQUE、name、password\_hash、email、address、is\_customer／is\_staff／is\_admin |
| stores | storeid | name、address、email、phone |
| products | productid | storeid FK、name、description、price、stock CHECK ≥ 0、image\_url |
| carts / cart\_items | (user\_id, productid) | quantity CHECK > 0 |
| orders | orderid | user\_id FK、order\_time、subtotal、tax、shipping\_fee、discount\_total、total、status CHECK IN (received, processing, shipping, closed) |
| order\_items | (orderid, productid) | 下單當下的 product\_name、unit\_price、quantity CHECK > 0 |
| discounts | discount\_code | type（shipping／seasonal／special\_event）、description、start\_date、end\_date、rate、min\_amount、rule 參數 |
| product\_discounts | (productid, discount\_code) | 僅限 special\_event；同商品期間不得重疊 |
| order\_discounts | (orderid, discount\_code) | 該訂單實際折抵金額 |

較難的約束：

- 特殊活動折扣期間不重疊：PostgreSQL 可用 `EXCLUDE USING gist (productid WITH =, daterange(start_date, end_date, '[]') WITH &&)`；SQLite／MySQL 需用 trigger。
- 數量不超過庫存：下單於同一交易內 `SELECT … FOR UPDATE` 鎖定商品列，檢查後扣庫存；或用 trigger 檢查 stock 不為負。
- 管理員可同時是工作人員：用布林欄位或 user\_roles 關聯表，不用單一 role 欄位。

### 階段 2：後端 API

- 認證：loginid + 密碼（bcrypt 雜湊），JWT 或 session，依角色授權。
- 顧客：商品列表與關鍵字搜尋、購物車 CRUD、結帳（伺服器端計算金額、套用折扣、扣庫存，全部在單一交易內）、歷史訂單。
- 工作人員：商品 CRUD、訂單狀態更新、折扣政策 CRUD、銷售報表（日、週、月，依商店彙總）。
- 管理員：使用者帳號建立與管理。
- 結帳順序：小計 → 特殊活動折扣（商品層級）→ 季節性折扣（訂單層級）→ 稅 → 運費折扣判斷。順序需與使用者確認。

### 階段 3：前端接上新後端

- 改寫 `src/services/*.ts`，保留函式名稱與回傳型別，內部改為 fetch API。
- 改寫 `AuthContext`：移除 Firebase，改為 loginid 登入並保存 token 與角色。
- 更新 `src/types/index.ts`：訂單狀態、role、storeid、折扣相關型別。
- 把 `useCart` 改為 `CartProvider` Context，修正導覽列不同步。
- HomePage 與 ProductDetail 改為向 API 取商品，移除寫死的陣列；ShopGrid 加關鍵字搜尋框。
- 移除 `libs/firebase.ts`、`firestore.rules`、`firebase.json` 與 firebase 依賴。

### 階段 4：新增後台頁面

- 工作人員：商品管理、訂單處理、折扣政策管理、銷售報表。
- 管理員：使用者管理。
- 依角色顯示導覽列項目，並在路由層擋下未授權存取。

交付物：ER Diagram、DDL、約束說明文件、可執行的前後端、示範資料。

## 待釐清問題

接手的 AI 開始階段 1 前，應先向使用者確認以下事項：

- [ ] 資料庫：PostgreSQL、MySQL 或 SQLite？授課教師是否有指定？此選擇決定期間不重疊約束的寫法。
- [ ] 後端技術：是否採用 FastAPI + SQLAlchemy？
- [ ] 商店模型：是單一商店還是多商店平台？每個商品是否只屬於一間商店？作業提到「每間商店的暢銷商品」，暗示多商店。
- [ ] 折扣率寫法：作業範例「0.05%」是指 5% 還是 0.05%？
- [ ] 折扣套用順序與稅基：稅金按折扣前或折扣後金額計算？季節性折扣與特殊活動折扣是否疊加？
- [ ] 買一送一的規則參數如何存（例如 buy\_qty、free\_qty）？
- [ ] 是否保留取消訂單？作業狀態只有四種，沒有 cancelled。
- [ ] 稅率 5% 與運費 100 元是否沿用，或改由設定表管理？
- [ ] 寵物互動功能是否保留？與作業無關，可保留為純前端裝飾或移除。
- [ ] 個人或小組作業？繳交期限？決定階段 4 與選配功能做到哪裡。
- [ ] ER Diagram 的繪製工具與格式要求（Chen 記號或 Crow's Foot）？

使用者偏好：繁體中文輸出；熟悉 Python；同時使用 Mac（Apple Silicon）與 Windows，開發環境需跨平台。
