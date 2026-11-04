# 資料庫系統專題要求

## 專題目標

以團隊方式完成一個資料庫專題，實際運用關聯式 DBMS、SQL 與資料庫設計技術。重點為：

- Entity-Relationship（ER）建模
- 關聯式資料庫設計
- SQL
- 正規化
- 以 Web 為基礎的資料庫系統開發

## 團隊結構

- 每組 5～6 人，其中一人擔任組長。
- 每位組員都必須參與所有交付項目。

## 參考資料

- [專題說明](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/projectSpec.htm)
- [範例專題（HackMD）](https://hackmd.io/lbNiWMh5Td2n_5FnwRgDtg)／[GitHub](https://github.com/ntutselab/Database-System-Example-Project)

## 時程與配分

| 階段 | 配分 | 截止日 |
|---|---|---|
| Phase 1：需求分析 | 15% | 2026/10/07 |
| Phase 2：概念與邏輯資料庫設計 | 25% | 2026/10/30 |
| Midterm Review | — | （依課程公告） |
| Phase 3：資料庫實作 | 25% | 2026/12/04 |
| Phase 4：系統實作與測試（Iteration II） | 25% | 2026/12/30 |
| Final Demo | — | （依課程公告） |
| Final Report | 10% | 2027/01/07（網頁原文寫 01/07/2026，疑為筆誤，請向教授確認） |

> 配分合計：15 + 25 + 25 + 25 + 10 = 100%

---

## Phase 1：需求分析（15%，10/07）

交付 **System Requirement Specifications（SRS）**，內容包含：

1. 系統描述（system description）
2. 系統架構（system architecture）
3. 操作概念（operational concepts／user stories）
4. 功能需求（functional requirements）
5. 資料需求（data requirements）
6. 非功能需求（non-functional requirements）
7. 介面需求（interface requirements）
8. 業務規則與完整性限制（business rules and integrity constraints）

範例：[SRS.docx](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/SRS.docx)／[pdf](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/SRS.pdf)、[Phase 1 範例 1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase1_report_1.pdf)、[範例 2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase1_report_2.pdf)、[SRS 英文範例](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/SRS%20(english)%20example.pdf)

## Phase 2：概念與邏輯資料庫設計（25%，10/30）

1. **ER Diagram**：含實體、屬性、鍵、基數（cardinality）與參與限制（participation constraints）的說明
2. **Database Schema**

範例：[範例 1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase2_report_1.pdf)、[範例 2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase2_report_2.pdf)

## Midterm Review

報告內容：

- User stories（operational concepts）
- 系統架構圖
- ER model
- 生成式 AI 的使用（理解、需求蒐集、schema 產生、系統與 UI 設計、程式碼產生、測試資料產生、查詢撰寫、最佳化、code review 與測試、文件、簡報與報告、使用的 AI 工具等）
- 使用者介面（prototype 畫面截圖）

範例：[1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/mid_slide1.pdf)、[2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/mid_slide2.pdf)、[3](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/mid_slide3)、[4](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/mid_slide4.pdf)

## Phase 3：資料庫實作（25%，12/04）

1. 在目標 DBMS 中實作資料表（資料表截圖）
2. 建立資料庫與匯入資料的 SQL 語法
3. （選做）估計各資料表在操作情境中的資料庫操作次數（每日透過 SQL 的預估使用頻率）
4. （選做）估計各資料表大小（KB／MB）＝ schema 長度 × 平均 tuple 數
5. 資料庫系統的實作與展示（部分功能）（GUI 截圖）

範例：[範例 1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase3_report_1.pdf)、[範例 2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase3_report_2.pdf)

## Phase 4：系統實作與測試（Iteration II）（25%，12/30）

1. 找出資料庫 schema 的函數相依（functional dependencies）
2. 正規化後的更新 schema，以及建立該 schema 的 SQL 語法（若適用）
3. 資料庫系統的實作與展示（完整功能）（GUI 截圖）
4. （選做）資料庫調校建議：索引結構、資料庫設計或查詢
5. 額外的查詢與檢視表（views）（查詢與 view 實作截圖）

範例：[範例 1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase4_report_1.pdf)、[範例 2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/phase4_report_2.pdf)

## Final Demo

內容：

- 修訂後的 user stories
- 修訂後的 ER model
- 修訂後的系統架構
- 函數相依
- SQL 查詢與 view 實作
- 生成式 AI 的使用
- Live Demo
- Demo 影片

範例：簡報 [1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/final_slide1.pdf)、[2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/final_slide2.pdf)、[3](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/final_slide3)、[4](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/final_slide4.pdf)；影片 [1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/Final_Demo_Video1.mp4)、[2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/Final_Demo_Video2.mp4)、[3](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/Final_Demo_Video3.mp4)

---

## Final Report（10%，01/07）

範本：[finalReport.docx](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/finalReport.docx)／[pdf](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/finalReport.pdf)
範例：[1](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/DBfinal-Example1.pdf)、[2](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/DBfinal-Example2.pdf)、[3](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/DBfinal-Example3.pdf)、[4](https://istudy.ntut.edu.tw/base/10001/course/10101990/content/project/DBfinal-Example4.pdf)

報告至少包含以下章節（不限於此）：

1. **封面**：課程名稱、專題名稱、授課教師、組員姓名、日期
2. **目錄**：章節與對應頁碼
3. **簡介**：專題簡述與本報告的章節組織
4. **系統需求**
   - 資料庫系統的系統架構圖
   - 功能、資料、非功能需求
   - 介面需求（系統或各子系統）
5. **資料庫概念設計**
   - 完整的 ER model
   - ER model 的資料字典與業務規則（限制）
6. **邏輯資料庫 schema**
   - 由 ER 圖轉換而來的 schema，並標示適當的參考完整性限制
   - 建立 schema 的 SQL 語法
   - （選做）預期的資料庫操作與預估資料量
7. **函數相依與資料庫正規化**
   - 分析第 6 章每個 relation 的函數相依
   - 呈現正規化過程，以及各 relation 正規化到 3NF 的結果（若適用）
   - 正規化後更新 schema 的 SQL 語法（若適用）
8. **系統使用手冊**
   - 安裝與使用方式簡述
   - 以截圖逐步示範主要操作概念（user stories）
9. **資料庫調校建議**（選做）：索引結構、資料庫設計、查詢等
10. **額外的查詢與檢視表**
    - 至少 3 個複雜查詢和／或 2 個 view
    - 必須展示 aggregate operators、GROUP BY、ORDER BY 與巢狀查詢（nested queries）
    - 附上每個查詢／view 的 SQL 與執行結果
11. **生成式 AI 的使用**：說明使用的 AI 與工具、如何應用在專題各項工作、成果與心得
12. **結論與未來工作**
13. **參考文獻**
14. **附錄**：壓縮檔，包含簡報、期末報告、SQL 腳本、資料庫檔案與原始碼

### 附錄壓縮檔結構（所有組別皆須遵守）

```
/doc        所有文件與簡報
/project    所有原始碼、測試程式、資料、網頁、SQL 腳本、函式庫與可執行檔
README      說明如何安裝與使用程式
```
