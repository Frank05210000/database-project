# Final Demo 影片工作區

用程式腳本操作網站錄影，字幕在腳本裡跟著動作寫，所以字幕時間自動對齊；網站改版後重錄只要再跑一次。
沒有配音，只有燒進畫面的中英雙語字幕（另附 `.srt`）。

```
final/video/
├── tools/record.py       錄影：Playwright + Chrome 截圖串流 → 1920×1080 30fps raw.mp4 + captions.json
├── tools/make_video.py   剪輯：依 edit.json 串接片頭／片段／圖片，燒中英字幕，輸出 mp4 + srt
├── scenes/               每個使用者故事一個場景檔（_selftest.py 是不需網站的自我測試）
├── edit.json             剪輯清單（哪些片段、順序、裁切、加速、片頭字卡）
├── storyboard.md         分鏡與字幕草稿
├── assets/               psql 結果截圖、背景音樂等素材
├── raw/                  手動錄的影片（QuickTime 等）也可以放這裡一起剪
├── recordings/  work/  out/   產出（不進 git）
```

## 用法

1. 啟動網站（例如 `npm run dev`，預設 `http://localhost:5173`）。
2. 錄一個場景（加 `--headed` 可以看著它跑）：
   ```bash
   python3 final/video/tools/record.py final/video/scenes/s02_cart.py --base http://localhost:5173
   ```
3. 編輯 `edit.json` 排好順序，輸出影片（`--preview` 先快速預覽）：
   ```bash
   python3 final/video/tools/make_video.py final/video/edit.json --preview
   ```
   ```bash
   python3 final/video/tools/make_video.py final/video/edit.json
   ```
4. 自我測試（不需要網站）：
   ```bash
   python3 final/video/tools/record.py final/video/scenes/_selftest.py && python3 final/video/tools/make_video.py final/video/edit.selftest.json
   ```

## 場景檔 API（`d.*`）

| 方法 | 作用 |
|---|---|
| `d.cap(zh, en)` | 從現在開始顯示這句字幕（自動結束上一句）；`d.end_cap()` 結束 |
| `d.goto(path)` | 開頁面（相對於 `--base`） |
| `d.click(sel)` / `d.hover(sel)` | 游標平滑移過去再點（有可見游標與點擊波紋） |
| `d.type(sel, text)` | 逐字輸入 |
| `d.select(sel, value)` / `d.press(key)` | 下拉選單／按鍵 |
| `d.scroll(dy)` / `d.scroll_to(sel)` | 平滑捲動 |
| `d.highlight(sel, sec)` | 用橘框標出元素 |
| `d.wait(sec)` | 停留 |

場景檔可以定義 `async def setup(page, base)`：在開始錄影前先做（例如登入），不會出現在影片裡。

## 需求

- Python 3 + `playwright`、`Pillow`（anaconda 已有）；用本機 Google Chrome，不需另外下載瀏覽器
- Homebrew `ffmpeg`（`/opt/homebrew/bin/ffmpeg`）
- 字型：`~/Library/Fonts/NotoSansTC-Medium.ttf`
