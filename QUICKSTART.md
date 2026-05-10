# Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama running: `ollama serve`
- Neo4j running: `docker run --rm -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/12345678 neo4j`

## Setup (5 minutes)

```bash
# 1. Environment Setup
cp .env.example .env
# Edit .env with your Gemini API key and Neo4j password

# 2. Install Python Dependencies
pip install -r requirements.txt

# 3. Install Frontend Dependencies
cd frontend && npm install && cd ..

# 4. Start Backend (Terminal 1)
./run_backend.sh
# Or: export PYTHONPATH="${PWD}:${PYTHONPATH}" && python -m uvicorn backend.main:app --reload

# 5. Start Frontend (Terminal 2)
./run_frontend.sh
# Or: cd frontend && npm run dev
```

## Usage

1. Open http://localhost:5173 in browser
2. Go to **Settings** tab → Click "爬取網站" (Scrape Website)
   - Takes 5-10 minutes to crawl and save data
3. Click "重新整理" (Refresh) to process & index
4. Switch to **Chat** tab and start asking questions
   - Example: "新北市有哪些投資優惠?"

## API Endpoints

```bash
# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "新北市有哪些投資優惠?", "mode": "hybrid"}'

# Status
curl http://localhost:8000/api/status

# Trigger scrape
curl -X POST http://localhost:8000/api/scrape

# Refresh RAG
curl -X POST http://localhost:8000/api/refresh
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: backend.config` | Use `./run_backend.sh` or set `PYTHONPATH` |
| `Connection refused at localhost:11434` | Start Ollama: `ollama serve` |
| `Neo4j connection failed` | Check Neo4j is running and password matches .env |
| `GEMINI_API_KEY not found` | Update .env with your Gemini API key |
| Frontend can't connect to API | Check backend is running on port 8000 |

## Project Structure

```
v2/
├── backend/          # FastAPI + RAG backend
├── frontend/         # React web UI
├── storage/          # Generated data (auto-created)
├── .env             # Your configuration
├── .env.example      # Template
└── README.md         # Full documentation
```

## Next Steps

- ✅ Data scraping working?
- ✅ RAG queries returning answers?
- ✅ Web UI displaying results?
- 📝 Deploy to production (see README.md)
- 📊 Monitor with logs and dashboards

For detailed configuration & deployment, see README.md
