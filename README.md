# 可以 Pick — 個人靈感知識庫

把截圖、照片裡覺得有趣的概念、案例、語錄、視覺參考整理成一個可搜尋、可瀏覽的 GitHub Pages 網站。規格來源見 [ProjectB_知識庫架構規劃.md](ProjectB_知識庫架構規劃.md)。

## 網站結構

```
index.html              網站主頁（左側欄雙軸導覽＋右側閱讀區）
assets/css/style.css    樣式
assets/js/app.js        前端邏輯（讀取 data/index.json，渲染導覽與內容）
assets/images/          每則內容對應的圖片
content/items/*.md      每則內容一個檔案（frontmatter + 內文）
data/index.json         由 content/items/*.md 自動彙整產生，網站實際讀取的資料
scripts/build_index.py  重新產生 data/index.json 的腳本
scripts/analyze_inbox.py（選用）呼叫 Claude API 自動分析 /inbox 圖片產生草稿
inbox/                  待整理的新截圖丟這裡（處理完會移走）
原始照片/               所有原始照片/截圖的存放處（只留在本機，不會推上 GitHub）
```

`assets/images/` 是網站實際使用、已縮圖的版本；`原始照片/` 是原檔備份，兩者用途不同。

分類架構（type × category 雙軸）與 frontmatter 欄位定義請見規劃文件，這裡不重複。

## 本機預覽

不需要安裝任何東西，用 Python 內建的 http.server 就能跑（因為前端用 `fetch()` 讀本地檔案，不能直接用瀏覽器開 `index.html`，需要透過 http:// ）：

```bash
python -m http.server 8420
```

然後打開 http://localhost:8420 。

## 新增一則內容（兩種方式）

### 方式一：請 Claude Code 幫你處理（推薦，不需要 API key）

1. 把截圖/照片丟進 `/inbox` 資料夾
2. 開一個 Claude Code 對話，跟它說「請幫我處理 /inbox 裡的新截圖，依照這個專案的分類架構建立草稿」
3. Claude Code 會讀圖（有文字的話逐字轉錄，沒文字的話寫描述），建議 type/category/tags，在 `content/items/` 建立草稿 `.md`，複製圖片到 `assets/images/`，把原檔移到 `原始照片/`，並重新執行 `python scripts/build_index.py` 更新 `data/index.json`
4. 你檢查草稿內容（尤其是分類是否貼切、`source` 是否需要補上），滿意後 commit + push

### 方式二：自己手動寫

1. 在 `content/items/` 新增一個檔案，例如 `2026-09-18-001.md`，照現有檔案的 frontmatter 格式填寫
2. 把對應圖片放進 `assets/images/`
3. 執行 `python scripts/build_index.py` 重新產生 `data/index.json`
4. commit + push

### （進階/選用）批次腳本 `analyze_inbox.py`

如果你想要一個不用開對話、可以批次跑的腳本版本，設定環境變數 `ANTHROPIC_API_KEY` 後執行：

```bash
python scripts/analyze_inbox.py
python scripts/build_index.py
```

腳本會呼叫 Claude API 分析 `/inbox` 裡每張圖，產生草稿並把來源圖片搬到 `原始照片/`。這是選用工具，平常用方式一（直接請 Claude Code 處理）就夠了。

## 部署到 GitHub Pages

1. 在 GitHub 建一個新的 repository（public 或 private 皆可，private repo 的 Pages 需要 Pro 方案才能開放存取，一般建議 public）
2. 在這個資料夾裡初始化 git 並推上去：
   ```bash
   git init
   git add .
   git commit -m "Initial commit: 可以 Pick 知識庫"
   git branch -M main
   git remote add origin https://github.com/<你的帳號>/<repo名稱>.git
   git push -u origin main
   ```
3. 到 GitHub repo 的 Settings → Pages，Source 選 "Deploy from a branch"，Branch 選 `main` / `(root)`，儲存
4. 幾分鐘後網站會在 `https://<你的帳號>.github.io/<repo名稱>/` 上線

之後每次 `git push` 到 `main` 都會自動重新部署。

## 目前測試資料

已匯入 14 則範例內容（第一批 6 則文字類 + 第二批 8 則視覺參考類），對應規劃文件裡的分類討論範例，實際圖片取自資料夾中的截圖與照片。
