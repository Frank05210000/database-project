# Final Demo 簡報

沿用期中簡報的 FUWA FUWA 風格與敘事方式：每頁一個 kicker、一句中文主張＋英文副標、卡片重點、頁尾附資料來源。
故事線：期中設計 → 實作時發現要改的地方 → 怎麼改（FD、正規化）→ 資料庫怎麼守規則 → 查詢與報表 → AI 的角色 → Demo。

| # | 頁面 | 課程要求 |
|---|---|---|
| 1 | 封面 | |
| 2 | 期中之後（時程＋議程＋技術 stack） | |
| 3–4 | 每則使用者故事對應到表／檢視表／trigger | Revised user stories |
| 5 | ER 模型 | Revised ER model |
| 6 | 16 張表、5 處修訂（由 SQL 自動產生） | Revised schema diagram |
| 7 | 逐表 FD，找到 3 條造成重複的相依 | Functional dependency |
| 8 | 正規化到 BCNF，規則改由 trigger 與 view 守 | Functional dependency |
| 9 | 32 CHECK、19 FK、12 trigger | SQL implementation |
| 10 | V1、V2 檢視表＋實際執行結果 | SQL view implementation |
| 11 | Q1–Q4 查詢＋實際執行結果 | SQL query implementation |
| 12 | 資料庫調校（選配） | |
| 13 | 生成式 AI 的使用 | The use of Generative AI |
| 14 | Demo 影片（`video/FUWA_FUWA_Final_Demo.mp4`，6:36，封面 `video/poster.jpg`） | Demo |
| 15 | 結論與未來工作 | |
| 16 | Thank you / Q&A | |

## 檔案

- `index.html`：簡報本體（← → 換頁、F 全螢幕、點圖放大）；`base.css` 來自期中簡報
- `notes.json`：每頁講稿，會寫進 PPTX 的備忘稿
- `export/FUWA_FUWA_Final.pdf`、`export/FUWA_FUWA_Final.pptx`：匯出版（PPTX 每頁是整張圖，不能直接編輯文字）

## 重新產生

```bash
python3 final/slides/tools/make_figs.py      # ER、schema、FD 圖（phase4/*.tex → PNG）
python3 final/slides/tools/query_shots.py    # 在 e-Shop 的 PostgreSQL 容器跑 V1/V2/Q1–Q4，BEGIN…ROLLBACK 不改資料
python3 final/slides/tools/schema_data.py    # 從 db/init/01_schema.sql 產生第 6 頁的表格
python3 final/slides/tools/export.py         # 匯出 PNG、PDF、PPTX
```

## 待補（頁面上以紅色虛線框標示）

- 第 1 頁：指導老師、日期
- 第 13 頁：組員補充使用過的其他 AI 工具與心得
