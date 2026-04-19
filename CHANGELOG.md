# Changelog

All notable changes to MemOS are documented here.

---

## [0.1.0] — 2026-04-19

### Added

- `MemoryNode` dataclass with importance scoring, access tracking, and pinned flag
- Ebbinghaus exponential decay engine (`decay_rate=0.008`, half-life ≈ 87 hours)
- LLM-based entity extractor using Claude Haiku with structured JSON output
- Lightweight keyword extractor fallback — runs without an Anthropic API key
- `MemoryStore` — dual-layer persistence via NetworkX graph + ChromaDB vector store
- JSON-only fallback for vector storage when ChromaDB is not installed
- Context injector — merges graph traversal and vector similarity, ranks by `0.6 × graph + 0.3 × vector + 0.1 × recency`
- FastAPI server with 8 endpoints: ingest, query, graph, stats, export, reinforce, delete, SSE events
- `!remember` prefix support — pins a memory so it never decays below 0.3
- Hourly decay scheduler via APScheduler (background thread, no Redis required)
- React dashboard with react-force-graph-2d — live graph, retrieval panel, decay curve preview
- Evaluation artifacts: retrieval walkthroughs, decay projection CSV, SVG decay chart
- `scripts/generate_eval_artifacts.py` — regenerates all evaluation and doc assets
- `pyproject.toml` with optional dependency groups: `llm`, `vector`, `all`, `dev`
- MIT license
