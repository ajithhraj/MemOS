# Evaluation

MemOS is an early-stage project, so the evaluation here is lightweight and qualitative by design. The goal is to show that the retrieval layer surfaces the right memories for representative questions and that the forgetting engine behaves predictably over time.

---

## Retrieval walkthroughs

The file [`evaluation/retrieval_examples.json`](../evaluation/retrieval_examples.json) contains concrete retrieval examples generated from a seeded memory store using `scripts/generate_eval_artifacts.py`.

Each example lists the query, the expected concepts that should appear in the top results, and the actual match ratio observed.

| Query | Expected concepts | Match ratio |
| --- | --- | --- |
| `What is MemOS building toward?` | `MemOS`, `local-first`, `portfolio` | `1.00` |
| `How does memory decay work?` | `forgetting`, `decay`, `0.008`, `pinned` | `1.00` |
| `What should stay visible in the UI?` | `visible`, `UI`, `forgetting engine` | `1.00` |
| `What are the optional dependencies?` | `chromadb`, `sentence-transformers`, `anthropic` | `0.67` |
| `Who built this project?` | `Ajith`, `ajithhraj`, `IISc` | `0.67` |

The first three queries hit cleanly because the memory store was seeded with those exact facts. The last two show realistic partial matches — the system retrieves related nodes but does not always surface the exact entity the question names. This is expected behaviour at the current retrieval depth of 2 hops.

These are not benchmark claims. They are sanity checks that the current retrieval mix (graph relevance + vector similarity + recency) surfaces the memories a human would expect for the most common query patterns.

---

## Decay behaviour

The forgetting engine applies exponential decay with a default rate of `0.008` per hour. The formula is:

```
new_importance = importance × e^(-0.008 × hours_since_access)
```

Pinned memories (flagged with `!remember`) never fall below `0.30` regardless of time.

![Decay behaviour chart](../docs/assets/decay-behavior.svg)

### Sample decay points

| Hours since access | Regular memory | Pinned memory |
| --- | --- | --- |
| `0` | `1.0000` | `1.0000` |
| `24` | `0.8253` | `0.8253` |
| `72` | `0.5621` | `0.5621` |
| `120` | `0.3829` | `0.3829` |
| `168` | `0.2608` | `0.3000` |
| `240` | `0.1496` | `0.3000` |
| `336` | `0.0672` | `0.3000` |

The prune threshold is `0.05`. A regular memory reaches this after roughly 375 hours (~15.6 days) without being accessed.

The raw numbers live in [`evaluation/decay_projection.csv`](../evaluation/decay_projection.csv).

---

## Reproducing the artifacts

Run the following from the repository root after activating your virtual environment:

**Windows:**
```cmd
.venv\Scripts\python.exe scripts\generate_eval_artifacts.py
```

**Mac / Linux:**
```bash
python scripts/generate_eval_artifacts.py
```

This regenerates `evaluation/retrieval_examples.json`, `evaluation/decay_projection.csv`, and `docs/assets/decay-behavior.svg`.
