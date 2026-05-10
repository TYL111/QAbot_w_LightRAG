# NTPC Economic Development QA Bot v2

A modern, modular QA system for New Taipei City (NTPC) Economic Development Bureau powered by LightRAG, featuring web scraping, RAG-based retrieval, and a web-based UI.

## Architecture

```
Frontend (React + TypeScript)  ←→  Backend API (FastAPI)  ←→  LightRAG + Neo4j
```

- **Frontend**: React 19 + TypeScript + Tailwind CSS + i18next (Traditional Chinese)
- **Backend**: FastAPI with async support
- **RAG**: LightRAG with Gemini 2.5 Flash Lite + Ollama BGE-M3 embeddings
- **Storage**: Neo4j for knowledge graph + JSON for KV storage
- **Data Source**: Web scraping from https://www.economic.ntpc.gov.tw

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama (for embeddings: `ollama run bge-m3`)
- Neo4j (Docker recommended)
- Gemini API key (from Google AI Studio)

### 1. Environment Setup

```bash
# Clone/navigate to project
cd v2

# Create .env from template
cp .env.example .env

# Edit .env with your credentials
# GEMINI_API_KEY=your_key_here
# NEO4J_PASSWORD=your_password_here
```

### 2. Start Infrastructure

```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Start Neo4j (via Docker)
docker run --rm -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/12345678 \
  neo4j:latest
```

### 3. Backend Setup

```bash
# Terminal 3: Backend
pip install -r requirements.txt
chmod +x run_backend.sh
./run_backend.sh
```

Or manually:
```bash
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`

### 4. Frontend Setup

```bash
# Terminal 4: Frontend
chmod +x run_frontend.sh
./run_frontend.sh
```

Or manually:
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 5. Data Pipeline

Once everything is running:

1. **Scrape data**: Visit Settings tab → Click "爬取網站" (Scrape Website)
   - Saves raw data to `storage/dicken/ntpc_raw.json`
   - Takes ~5-10 minutes depending on max_pages

2. **Process & Index**: Click "重新整理" (Refresh) in Settings
   - Processes raw data (deduplication, chunking)
   - Indexes into LightRAG
   - Creates Neo4j knowledge graph

3. **Query**: Switch to Chat tab and start asking questions

## API Endpoints

### Query
```bash
POST /api/query
{
  "question": "新北市有哪些投資優惠?",
  "mode": "hybrid",
  "top_k": 60,
  "chunk_top_k": 20
}
```

### Web Management
```bash
POST /api/scrape          # Trigger scraping
POST /api/refresh         # Rebuild RAG
GET  /api/documents       # List indexed documents
GET  /api/status          # RAG status
GET  /api/config          # Current config
GET  /api/health          # Health check
```

## Project Structure

```
v2/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── dependencies.py         # Dependency injection
│   ├── scraper/
│   │   ├── ntpc_scraper.py     # Selenium-based web crawler
│   │   └── data_processor.py   # Data cleaning & chunking
│   ├── rag/
│   │   └── rag_manager.py      # LightRAG wrapper
│   └── api/
│       ├── routes.py           # API endpoints
│       └── schemas.py          # Pydantic models
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app
│   │   ├── main.tsx            # Entry point
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── DocumentBrowser.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   └── useQuery.ts     # API interaction
│   │   ├── i18n/
│   │   │   └── zh.json         # Traditional Chinese
│   │   └── i18n.ts
│   ├── index.html
│   └── package.json
│
├── storage/                    # Generated storage
├── .env.example
├── .gitignore
└── requirements.txt
```

## Key Features

✅ **Web Scraping**: BFS-based crawler with rate limiting
✅ **Data Processing**: Deduplication, cleaning, chunking
✅ **Knowledge Graph**: Neo4j entity-relationship graph
✅ **Query Modes**: hybrid, local, global, mix, naive
✅ **Web UI**: Traditional Chinese interface with chat history
✅ **Document Management**: View indexed documents and metadata
✅ **API-First**: Full REST API with async support
✅ **Production-Ready**: Docker-compatible, configurable via env vars

## Configuration

### Query Modes

- **hybrid**: Combines local (entity-focused) + global (summary-based) retrieval
- **local**: Entity-focused context-dependent retrieval
- **global**: Community/summary-based broad retrieval
- **mix**: KG + vector retrieval with reranking
- **naive**: Direct vector similarity search

### Environment Variables

```env
# LLM & Embeddings
GEMINI_API_KEY=                # Required: Google Gemini API key
OLLAMA_BASE_URL=http://localhost:11434

# Storage
WORKING_DIR=./storage/dicken
WORKSPACE=ntpc_economic

# Graph Database
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=

# Query Parameters
TOP_K=60                       # Entities to retrieve
CHUNK_TOP_K=20                 # Text chunks to retrieve
MAX_ENTITY_TOKENS=6000
MAX_RELATION_TOKENS=8000
MAX_TOTAL_TOKENS=30000

# Web Scraper
SCRAPE_BASE_URL=https://www.economic.ntpc.gov.tw
SCRAPE_MAX_PAGES=100
SCRAPE_DELAY_SECONDS=2
```

## Troubleshooting

### RAG Not Initialized
**Error**: `AttributeError: __aenter__` or `KeyError: 'history_messages'`
**Fix**: Check backend logs. RAG must initialize storages on startup.

### Ollama Connection Failed
**Error**: `Connection refused at localhost:11434`
**Fix**: Start Ollama: `ollama serve` (in separate terminal)

### Neo4j Connection Failed
**Error**: `Failed to establish connection to neo4j://...`
**Fix**: Check Neo4j is running and credentials in .env match

### Web Scraping Too Slow
**Solution**: Increase `SCRAPE_DELAY_SECONDS` to reduce rate limiting

### Embedding Dimension Mismatch
**Solution**: Clear `storage/` directory and re-index if changing embedding models

## Development

### Linting Backend
```bash
cd backend
ruff check .
```

### Building Frontend
```bash
cd frontend
npm run build
```

### Running Tests
```bash
# Backend
pytest backend/tests

# Frontend
npm run test
```

## Deployment

### Docker
```bash
# Build image
docker build -t ntpc-qa-bot .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=xxx \
  -e NEO4J_PASSWORD=xxx \
  ntpc-qa-bot
```

### Production Checklist
- [ ] Set `DEBUG=false` in .env
- [ ] Configure CORS origins for production domain
- [ ] Use production Neo4j instance (not Docker)
- [ ] Set up SSL/TLS for API
- [ ] Configure logging to external service
- [ ] Set up monitoring & alerting

## Support

For issues, check:
1. Backend logs: `http://localhost:8000/docs`
2. Frontend console: Browser DevTools
3. API health: `http://localhost:8000/api/health`
4. RAG status: `http://localhost:8000/api/status`

## License

This project uses LightRAG framework. See LICENSE for details.
