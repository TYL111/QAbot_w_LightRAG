# Quickstart 教學

這份文件會帶你在本機快速啟動這個 NTPC Economic QA Bot，並完成第一次問答流程。

## 1. 先準備環境

### 必要條件

- Python 3.10+
- Node.js 18+
- Docker（可選，但推薦用來啟動 Neo4j）
- OpenAI API Key（用於 GPT 問答與擷取）
- Ollama（用於 `bge-m3` embedding 模型）

### 建議的啟動方式

以下示例提供三種常見環境：Windows PowerShell、WSL / Linux Bash，以及 Git Bash。

#### Windows PowerShell

```powershell
cd D:\code\QAbot_w_LightRAG
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Linux / WSL / Bash

```bash
cd ~/code/QAbot_w_LightRAG
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> 若你看到 `bash: .venv/bin/activate: 沒有此一檔案或目錄` 或 `Command 'python' not found`，表示目前的 `.venv` 可能是 Windows 風格，或你還沒在 Linux/WSL 環境裡建立正確的虛擬環境。請先重建：
>
> ```bash
> cd ~/code/QAbot_w_LightRAG
> rm -rf .venv
> python3 -m venv .venv
> source .venv/bin/activate
> python -m pip install --upgrade pip
> pip install -r requirements.txt
> ```
>
> 在 Ubuntu / Debian / WSL 上，通常要用 `python3`，不要直接用 `python`。

#### Git Bash

```bash
cd /d/code/QAbot_w_LightRAG
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

---

## 2. 設定環境變數

這個專案會讀取根目錄的 `.env` 檔案。若尚未存在，請先複製範本：

```powershell
Copy-Item .env.example .env
```

若你是在 Linux / WSL / Bash 環境：

```bash
cp .env.example .env
```

打開 `.env`，確認以下內容大致正確：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=12345678
WORKING_DIR=./storage/dicken
WORKSPACE=ntpc_economic
```

> 若你已經有 `.env`，請補上這三個 OpenAI 設定並確認 Neo4j / Ollama 設定。將 `OPENAI_API_KEY` 換成有效的 Key；模型可透過 `OPENAI_MODEL` 修改為帳號可用的 GPT 模型。Key 只放在本機 `.env`，不要提交到 Git。

LLM 問答、關鍵字擷取與文件實體擷取會使用 GPT API；embedding 仍使用原本的 `bge-m3`（1024 維），既有向量資料可繼續使用。缺少 API Key 時後端會提示錯誤。既有 LightRAG 快取可能回傳先前模型的結果，驗證 GPT 輸出時請使用未查詢過的問題。

---

## 3. 啟動 Ollama 與 Neo4j

### 3.1 啟動 Ollama（僅用於 embedding）

在一個新終端機執行：

```powershell
ollama serve
```

接著下載必要模型：

```powershell
ollama pull bge-m3
```

### 3.2 啟動 Neo4j

```powershell
docker run --rm -p 7687:7687 -p 7474:7474 `
  -e NEO4J_AUTH=neo4j/12345678 `
  neo4j:latest
```

啟動後可在瀏覽器中打開：

- Neo4j Browser: http://localhost:7474
- Bolt 連線: neo4j://127.0.0.1:7687

---

## 4. 啟動後端 API

在專案根目錄執行：

```powershell
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

或直接使用預設腳本：

```powershell
./run_backend.sh
```

啟動成功後可檢查：

- API 文件: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

---

## 5. 啟動前端

在另一個終端機執行：

```powershell
cd frontend
npm install
npm run dev
```

或直接使用：

```powershell
./run_frontend.sh
```

前端通常會啟動在：

- http://localhost:5173

---

## 6. 第一次使用：抓取資料與建立索引

啟動前端後，請依序做以下動作：

1. 打開前端頁面 http://localhost:5173
2. 進入 Settings / 設定頁
3. 點擊「爬取網站」或對應的抓取按鈕
4. 等待資料下載到 `./data` 目錄
5. 再點擊「重新整理」或「Refresh」
6. 系統會處理資料、切塊並建立 LightRAG / Neo4j 索引

完成後即可切換到 Chat 頁面開始詢問問題。

---

## 7. 常見問題

### 7.1 Ollama 連線失敗

錯誤通常會顯示：

- connection refused
- cannot connect to localhost:11434

解法：

```powershell
ollama serve
```

確認模型存在：

```powershell
ollama list
```

### 7.2 Neo4j 無法連線

檢查：

- Docker 是否正在執行
- 7687 / 7474 port 是否有被占用
- `.env` 中 `NEO4J_PASSWORD` 是否與啟動時一致

### 7.3 後端啟動失敗

通常是因為 `.env` 缺少密碼，或 `PYTHONPATH` 沒有設定。你可以手動執行：

#### Windows PowerShell

```powershell
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Linux / WSL / Bash

```bash
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.4 前端開啟後沒有資料

請確認：

- 後端 API 正常啟動
- 你已經執行過「爬取網站」
- 已經成功點擊「重新整理」建立索引

---

## 8. 最小驗證流程

你可以用以下順序快速驗證整個系統：

#### Linux / WSL / Bash

```bash
# 1. 啟動 Ollama
ollama serve

# 2. 啟動 Neo4j
# Docker command from above

# 3. 啟動後端
cd ~/code/QAbot_w_LightRAG
source .venv/bin/activate
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 4. 啟動前端
cd frontend
npm install
npm run dev
```

#### Windows PowerShell

```powershell
# 1. 啟動 Ollama
ollama serve

# 2. 啟動 Neo4j
# Docker command from above

# 3. 啟動後端
cd D:\code\QAbot_w_LightRAG
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 4. 啟動前端
cd frontend
npm install
npm run dev
```

然後在瀏覽器中：

- 開啟 http://localhost:5173
- 點選設定頁「爬取網站」
- 再點「重新整理」
- 切到聊天頁，輸入：

```text
新北市有哪些投資優惠？
```

如果可以正常回應，代表系統已經跑起來了。

---

## 9. 下一步建議

- 先試著抓取幾個頁面確認流程穩定
- 再擴大爬取範圍與資料量
- 若需要調整查詢行為，可查看 `.env` 或 `backend/config.py`
- 若要查看 API 格式，可打開 http://localhost:8000/docs

---

這份 quickstart 足夠讓你先跑通本專案。如果你要，我也可以再補一份「Windows 專用完整安裝版」或「Docker 一鍵啟動版」教學。
