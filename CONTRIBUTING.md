# Contributing to MemOS

Thanks for your interest. MemOS is an early-stage project and contributions are welcome.

---

## Setup

```bash
git clone https://github.com/ajithhraj/MemOS.git
cd MemOS

python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate

pip install -e ".[dev,llm,vector]"
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env` if you want to run the full extraction pipeline. Without it, MemOS falls back to the lightweight keyword extractor.

---

## Running tests

```bash
pytest
```

Core tests in `tests/` cover the decay math, extraction fallback, and end-to-end retrieval. They run without an API key or a running server.

---

## Areas open for contribution

- **Memory consolidation** — merge near-duplicate nodes (cosine similarity > 0.92) into a single enriched node.
- **Conflict detection** — flag when a new memory contradicts an existing one, surface it to the user.
- **Export formats** — add a JSONL export alongside the existing JSON export for streaming-friendly use cases.
- **Dashboard polish** — the React dashboard is functional but sparse. Better node tooltips, a timeline view, and a stats panel are all welcome.
- **More tests** — especially for the FastAPI routes and the SSE events stream.

---

## Pull request guidelines

- Keep PRs focused on one thing. A PR that fixes a bug and adds a feature is hard to review.
- Add or update tests for any behaviour change.
- Run `pytest` before pushing and make sure it passes.
- If you are adding a new dependency, update both `pyproject.toml` and `requirements.txt` and explain why it is needed.

---

## Reporting issues

Open a GitHub issue with a description of the problem, the Python version, OS, and the full error traceback if applicable.
