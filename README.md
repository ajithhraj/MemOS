# MemOS

MemOS is a local-first memory layer for LLM applications. It extracts memorable facts from conversations, stores them in a graph plus vector index, decays stale memories over time, and exposes a dashboard for exploring what the system remembers.

## What is included

- Python package with memory models, extractor, scoring, decay, storage, retrieval, and FastAPI routes
- Local fallbacks so the project still runs without Anthropic, ChromaDB, or sentence-transformers
- React dashboard with live graph updates, query panel, and decay curve preview
- Pytest coverage for core decay and retrieval flows

## Backend setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn memos.api.main:app --reload --port 8000
```

Optional:

- Set `ANTHROPIC_API_KEY` to enable Claude-based extraction.
- Install the `vector` optional dependencies if you want ChromaDB and sentence-transformers in addition to the built-in JSON fallback.

## Frontend setup

```powershell
cd dashboard
npm install
npm run dev
```

The dashboard expects the API at `http://localhost:8000`.

## Useful endpoints

- `POST /memory/ingest`
- `POST /memory/query`
- `GET /memory/graph`
- `GET /memory/stats`
- `GET /memory/export`
- `POST /memory/{node_id}/reinforce`
- `DELETE /memory/{node_id}`
- `GET /memory/events`

## Example ingest payload

```json
{
  "message": "I am building MemOS for my portfolio and want the forgetting engine to stay visible in the UI."
}
```
