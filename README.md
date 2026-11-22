# FUWA FUWA e-Shop

北科大資料庫系統期末專題：多門市寵物用品電子商店。同一個網站依登入角色顯示**顧客購物介面**、**工作人員管理介面**、**平台管理介面**。

- 前端：React 18 + TypeScript + Vite（`fuwafuwa-shop/`）
- 後端：FastAPI + JWT + SQLAlchemy 2（`backend/`）
- 資料庫：PostgreSQL 16（`db/init/`）
- 文件：Phase 1/2 SRS（`phase1/`、`phase2/`）、開發計畫與 API 契約（`docs/DEVELOPMENT_PLAN.md`）

## 一個指令啟動

需要 Docker Desktop。

```bash
./start.sh
```

| 服務 | 網址 |
|---|---|
| 網站（三種介面） | http://localhost:5173 |
| 後端 API 文件（Swagger） | http://localhost:8001/docs |
| PostgreSQL | `localhost:5433`，帳號／密碼／資料庫皆為 `fuwa` |

`./start.sh reset` 清空資料庫重新套用 `db/init/*.sql`；`./start.sh down` 停止。也可以直接用 `docker compose up --build`。

### 示範帳號

| 帳號 | 密碼 | 角色 | 進入的介面 |
|---|---|---|---|
| `admin` | `admin123` | 平台管理員 | `/admin` 使用者帳號、角色、停用／啟用、新增／修改商店 |
| `staff` | `staff123` | 工作人員 | `/staff` 商品、訂單、退貨、折扣、報表 |
| `manager` | `staff123` | 工作人員＋平台管理員 | 兩者都可，頁首可切換 |
| `alice` | `customer123` | 顧客 | 購物、購物車、結帳、訂單、退貨 |
| `bob` | `customer123` | 顧客 | 同上 |
| `carol` | `customer123` | 顧客（已停用） | 無法登入，用來示範停用帳號 |

## 線上版（Vercel＋Neon）

- 網址：https://fuwafuwa-eshop.vercel.app （示範帳號同上）
- 前端由 Vercel 以 Vite 建置；`api/index.py` 把 `/api/*` 交給 `backend/` 的 FastAPI（Python serverless 函式）
- 資料庫為 Neon PostgreSQL（Vercel Marketplace），已套用 `db/init/*.sql`，時區設為 Asia/Taipei
- 重新部署：`vercel deploy --prod`
- 重設線上資料庫為示範資料（連線字串由 `vercel env pull` 取得，存在 `.env.local`，不進版控）：

```bash
set -a; . ./.env.local; set +a
(echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; cat db/init/0*.sql) | docker run --rm -i postgres:16-alpine psql "$DATABASE_URL_UNPOOLED" -v ON_ERROR_STOP=1 -q
```

## 資料庫

`db/init/` 依檔名順序在資料庫第一次啟動時執行：

| 檔案 | 內容 |
|---|---|
| `01_schema.sql` | 15 張表（沿用 Phase 2 並正規化到 3NF：`product_discount`、`return_item` 拆乾淨、`orders.total` 改由檢視表 `v_orders` 計算；新增 `return_request.refund_total`：核准退貨時依 BR-26 算好存起來） |
| `02_triggers.sql` | Phase 2 SRS 4.3 節的規則：BR-13 特殊活動折扣期間不重疊、BR-19 狀態流轉並自動寫狀態歷程、BR-21 角色、BR-24 評價、BR-25 退貨（含 UPDATE 防護）、BR-21 狀態變更須由正確操作者、BR-06 購物車庫存、BR-18 折扣代碼不可改、至少保留一位平台管理員 |
| `03_seed.sql` | 系統參數、6 位使用者與角色、3 間商店、15 項商品、8 筆折扣政策 |
| `04_demo_data.sql` | 示範交易：13 筆訂單（六種狀態都有）、明細、套用折扣、狀態歷程、4 筆退貨申請（部分核准、全部核准、拒絕、待審核）、評價、購物車。由 `backend/scripts/gen_demo_data.py` 用後端的金額計算服務產生，依業務流程執行，所有 trigger 都會檢查 |

## 後端測試

```bash
docker compose up -d db
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest
```

每個測試都在全新的 `fuwa_test` 資料庫上執行（套用 01～03），包含正常流程與 BR 違規被拒絕的案例（後端檢查與直接改資料庫時 trigger 的拒絕）。

### 全系統端對端測試

系統啟動後（`./start.sh`），經由前端 proxy 走完顧客、工作人員、管理員的主要流程與 BR 違規案例（27 項）：

```bash
cd backend && .venv/bin/python scripts/e2e_smoke.py
```

## 本機開發（不用 Docker 跑前後端）

```bash
docker compose up -d db
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001
cd fuwafuwa-shop && npm install && npm run dev      # Vite 會把 /api 轉到 localhost:8001
```

## 主要流程

1. 顧客：註冊／登入 → 搜尋商品 → 加入購物車 → 結帳（顯示特殊活動折扣、季節性折扣、稅、運費、運費折扣）→ 我的訂單看狀態歷程 → 取消（received）或申請退貨（processing／shipping／closed）。
2. 工作人員：商品與庫存 CRUD（被訂單引用的商品改為下架）→ 依序推進訂單狀態 → 審核退貨（核准時計算退款並回補庫存）→ 管理三種折扣（系統產生代碼、期間重疊會被拒絕）→ 日／週／月銷售報表（BR-23 比例分攤）。
3. 平台管理員：新增、查詢、修改使用者 → 指派或移除 customer／staff／admin 角色 → 停用或啟用帳號 → 新增與修改商店資料（STS-F-002；SRS 只寫修改，新增為擴充）。
