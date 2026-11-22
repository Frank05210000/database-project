# FUWA FUWA e-Shop — 資料庫系統期末專題（第 13 組）

多商店的寵物用品線上購物系統。資料庫為 PostgreSQL 16，後端 FastAPI，前端 React + Vite。
這份 INDEX 是整個 repo 的索引：每個階段交了什麼、檔案在哪裡、怎麼重新產生。

- 線上版：<https://fuwafuwa-eshop.vercel.app>（Vercel + Neon PostgreSQL）
- 本機版：在根目錄執行 `./start.sh`（需要 Docker Desktop），網址 <http://localhost:5173>
- 網站程式（`fuwafuwa-shop/`、`backend/`、`db/`、`docs/`）的安裝與架構說明見 [README.md](README.md)
- `.github/workflows/ci.yml`：每次 push 由 GitHub Actions 以 PostgreSQL 16 執行後端測試並建置前端

## 快速導覽

| 繳交物 | 檔案 |
|---|---|
| Phase 1 需求分析 SRS | [phase1/Phase1_SRS_e-Shop.pdf](phase1/Phase1_SRS_e-Shop.pdf) |
| Phase 2 ER 模型與 Schema | [phase2/Phase2_SRS_e-Shop.pdf](phase2/Phase2_SRS_e-Shop.pdf) |
| 期中簡報 | [slides/index.html](slides/index.html)、[slides/FUWA_FUWA_e-Shop.pptx](slides/FUWA_FUWA_e-Shop.pptx) |
| Phase 3 資料庫實作 | [phase3/Team13_phase3.pdf](phase3/Team13_phase3.pdf) |
| Phase 4 正規化、查詢與系統展示 | [phase4/Team13_phase4.pdf](phase4/Team13_phase4.pdf) |
| 期末簡報 | [final/slides/export/FUWA_FUWA_Final.pdf](final/slides/export/FUWA_FUWA_Final.pdf)、[.pptx](final/slides/export/FUWA_FUWA_Final.pptx)、[HTML 版](final/slides/index.html) |
| 期末 Demo 影片 | [final/slides/video/FUWA_FUWA_Final_Demo.mp4](final/slides/video/FUWA_FUWA_Final_Demo.mp4) |
| 課程要求 | [參考範例/requirements.md](參考範例/requirements.md) |

## 各資料夾內容

報告都用 LaTeX 撰寫，`srs.tex` 是原始檔，`srs.pdf` 是編譯結果，再複製成繳交用的檔名。

### `phase1/` 需求分析
- `srs.tex` → `Phase1_SRS_e-Shop.pdf`：使用者故事、功能需求、商業規則

### `phase2/` 概念與邏輯設計
- `srs.tex`、`sec34.tex` → `Phase2_SRS_e-Shop.pdf`
- `ER圖/`：ER 圖。`ER_drawio.tex`（TikZ）編譯成 `ER_drawio.pdf`；`ER.drawio`、`er.json` 是排版來源
- `schema圖/schema_diagram.tex`：Schema 圖（TikZ）
- `schema.sql`：Phase 2 的資料表定義
- `backup/`：舊版報告

### `phase3/` 資料庫實作
- `srs.tex` → `Team13_phase3.pdf`；Section 4 以後的內容拆在 `sec_phase3.tex`（實作說明）、`dbshots.tex`（資料庫截圖）、`demo.tex`、`install.tex`（安裝）、`gui.tex`（部分功能的 GUI）
- `sql/01_schema.sql`～`04_demo_data.sql`：建表、trigger、初始資料、示範資料（正規化前的版本）
- `sizes.py` → `size_table.tex`、`freq_table.tex`：4.4、4.5 節的操作頻率與資料量估計
- `tools/make_db_shots.sh`：在 PostgreSQL 容器執行 psql，再用 `term2png.py` 把輸出畫成截圖（`shot.sh` 負責單張）
- `img/`：資料庫截圖與 GUI 截圖；`ER圖/`、`schema圖/`：報告用的圖

### `phase4/` 正規化、查詢與系統展示
- `srs.tex` → `Team13_phase4.pdf`；新增的章節在 `sec_phase4.tex`（FD 與正規化）、`queries.tex`（檢視表與查詢）、`tuning.tex`（調校與實測），`gui.tex` 是完整 GUI
- `sql/`：正規化後的最終 SQL，與網站 `db/init/` 相同
- `sql_q/`：檢視表 V1、V2 與查詢 Q1–Q4
- `sql_bench/bench_data.sql`：Section 7 效能實測用的測試資料（10 萬項商品、10.95 萬筆訂單，不是真實資料）
- `fd.py` → `fd_before.tex`、`fd_after.tex`：正規化前後的函數相依圖
- `sizes.py`：同 Phase 3，改用正規化後的欄位計算
- `tools/`
  - `make_db_shots.sh`：資料庫截圖
  - `make_query_shots.sh`：查詢結果截圖
  - `make_bench_shots.sh`：加索引前後的 EXPLAIN ANALYZE 截圖
  - `gui_shots.py`：用 Playwright 擷取 GUI 截圖

### `slides/` 期中簡報
- `index.html`：簡報本體（HTML）；`build_pptx.js` 產生 `FUWA_FUWA_e-Shop.pptx`；`img/` 為素材

### `final/slides/` 期末簡報
- `index.html`、`base.css`：簡報本體；`notes.json`：每頁講稿；`outline.md`：頁面與課程要求的對照
- `tools/`
  - `make_figs.py`：ER、schema、FD 圖
  - `query_shots.py`：查詢結果截圖
  - `schema_data.py` → `schema_data.js`：schema 表格資料
  - `export.py`：匯出 PNG、PDF、PPTX
- `export/`：匯出結果；`video/`：簡報內嵌的 Demo 影片與封面

### `final/video/` Demo 影片
- `scenes/s01`～`s09`：每段情境的操作腳本（字幕寫在腳本裡）；`storyboard.md`：分鏡
- `tools/record.py` 錄影、`tools/make_video.py` 依 `edit.json` 剪輯並燒字幕
- `assets/`：影片中穿插的 psql 截圖；`raw/`：可放手動錄製的片段
- 錄影與剪輯的產出（`recordings/`、`work/`、`out/`）不進 git

### `參考範例/`
課程提供的報告範例（各 phase 的 PDF）與要求（`requirements.md`），以及前端沿用的交接文件。

## 如何重新產生

| 要做的事 | 指令或說明 |
|---|---|
| 編譯報告 | `cd phase4 && tectonic -X compile srs.tex`，再把 `srs.pdf` 複製成 `Team13_phase4.pdf`（其他 phase 相同） |
| 資料庫與 GUI 截圖 | 先用 `./start.sh` 或 Docker 容器載入 `sql/`，再執行 `phase4/tools/` 下的腳本（各腳本開頭有用法） |
| 期末簡報 | 步驟見 [final/slides/outline.md](final/slides/outline.md) |
| Demo 影片 | 步驟見 [final/video/README.md](final/video/README.md) |
