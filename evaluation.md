# Evaluation Notes

MemOS is still an early-stage project, so the evaluation here is lightweight and qualitative by design. The goal is to show that the retrieval layer surfaces the right memories for representative questions and that the forgetting engine behaves predictably over time.

## Retrieval walkthroughs

The file [`evaluation/retrieval_examples.json`](../evaluation/retrieval_examples.json) contains concrete retrieval examples generated from a seeded memory store.

| Query | Expected concepts | Match ratio |
| --- | --- | --- |
| `What is MemOS building toward?` | `MemOS`, `local-first`, `portfolio` | `1.00` |
| `How does memory decay work?` | `forgetting`, `decay`, `0.008`, `pinned` | `1.00` |
| `What should stay visible in the UI?` | `visible`, `UI`, `forgetting engine` | `1.00` |

These are not benchmark claims. They are sanity checks that the current retrieval mix of graph relevance, vector similarity, and recency is surfacing the memories a human would expect.

## Decay behavior

The forgetting engine applies exponential decay with a default rate of `0.008` per hour. Pinned memories never fall below `0.30`.

![Decay behavior chart](assets/decay-behavior.svg)

The raw numbers used for the chart live in [`evaluation/decay_projection.csv`](../evaluation/decay_projection.csv).

### Sample points

| Hours since access | Regular memory | Pinned memory |
| --- | --- | --- |
| `0` | `1.0000` | `1.0000` |
| `24` | `0.8253` | `0.8253` |
| `72` | `0.5621` | `0.5621` |
| `120` | `0.3829` | `0.3829` |
| `168` | `0.2608` | `0.3000` |

## Reproducing the artifacts

Run the script below from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\generate_eval_artifacts.py
```

That command refreshes the retrieval examples JSON, the decay CSV, and the SVG chart used in this document.
