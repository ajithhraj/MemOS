from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evaluation"
ASSETS_DIR = ROOT / "docs" / "assets"
sys.path.insert(0, str(ROOT))

from memos.core.decay import DECAY_RATE, importance_at
from memos.core.models import MemoryNode
from memos.core.store import MemoryStore
from memos.retrieval.injector import retrieve_context


def main() -> None:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    retrieval_results = build_retrieval_examples()
    write_retrieval_json(retrieval_results)

    decay_rows = build_decay_rows()
    write_decay_csv(decay_rows)
    write_decay_svg(decay_rows)


def build_retrieval_examples() -> list[dict[str, object]]:
    cases = [
        {
            "query": "What is MemOS building toward?",
            "expected_keywords": ["MemOS", "local-first", "portfolio"],
        },
        {
            "query": "How does memory decay work?",
            "expected_keywords": ["forgetting", "decay", "0.008", "pinned"],
        },
        {
            "query": "What should stay visible in the UI?",
            "expected_keywords": ["visible", "UI", "forgetting engine"],
        },
    ]

    results: list[dict[str, object]] = []
    for case in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(user_id="eval", persist_path=temp_dir)
            for node in seed_nodes():
                store.add(node)
            context = retrieve_context(case["query"], store, top_k=4)
            lowered = context.lower()
            matched = [term for term in case["expected_keywords"] if term.lower() in lowered]
            results.append(
                {
                    "query": case["query"],
                    "expected_keywords": case["expected_keywords"],
                    "matched_keywords": matched,
                    "match_ratio": round(len(matched) / len(case["expected_keywords"]), 2),
                    "context": context,
                }
            )
    return results


def seed_nodes() -> list[MemoryNode]:
    return [
        MemoryNode(
            content="Ajith is building MemOS as a local-first memory layer for LLM applications and portfolio demos.",
            entity_type="project",
            importance=0.92,
            metadata={"relations_raw": ["Ajith", "MemOS", "LLM"]},
        ),
        MemoryNode(
            content="MemOS uses an Ebbinghaus-style forgetting engine with a default decay rate of 0.008 per hour.",
            entity_type="fact",
            importance=0.88,
            metadata={"relations_raw": ["MemOS", "forgetting engine"]},
        ),
        MemoryNode(
            content="Pinned memories never decay below an importance floor of 0.3.",
            entity_type="decision",
            importance=0.91,
            pinned=True,
            metadata={"relations_raw": ["pinned", "importance floor"]},
        ),
        MemoryNode(
            content="The dashboard shows a live memory graph, a retrieval panel, and a decay curve preview.",
            entity_type="fact",
            importance=0.77,
            metadata={"relations_raw": ["dashboard", "graph", "retrieval panel"]},
        ),
        MemoryNode(
            content="Ajith wants the forgetting engine to stay visible in the UI because it is the most novel part of MemOS.",
            entity_type="preference",
            importance=0.84,
            metadata={"relations_raw": ["Ajith", "UI", "forgetting engine"]},
        ),
    ]


def write_retrieval_json(results: list[dict[str, object]]) -> None:
    output_path = EVAL_DIR / "retrieval_examples.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")


def build_decay_rows() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for hours in range(0, 169, 12):
        rows.append(
            {
                "hours": float(hours),
                "regular_importance": importance_at(1.0, hours, rate=DECAY_RATE, pinned=False),
                "pinned_importance": importance_at(1.0, hours, rate=DECAY_RATE, pinned=True),
            }
        )
    return rows


def write_decay_csv(rows: list[dict[str, float]]) -> None:
    output_path = EVAL_DIR / "decay_projection.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["hours", "regular_importance", "pinned_importance"])
        writer.writeheader()
        writer.writerows(rows)


def write_decay_svg(rows: list[dict[str, float]]) -> None:
    width, height = 860, 340
    padding = 48
    inner_width = width - padding * 2
    inner_height = height - padding * 2
    max_hours = max(row["hours"] for row in rows) or 1

    def point(hours: float, value: float) -> tuple[float, float]:
        x = padding + (hours / max_hours) * inner_width
        y = padding + (1 - value) * inner_height
        return round(x, 2), round(y, 2)

    def path_for(key: str) -> str:
        segments = []
        for index, row in enumerate(rows):
            x, y = point(row["hours"], row[key])
            command = "M" if index == 0 else "L"
            segments.append(f"{command} {x} {y}")
        return " ".join(segments)

    tick_lines = []
    for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = padding + (1 - ratio) * inner_height
        tick_lines.append(f'<line x1="{padding}" y1="{y}" x2="{width - padding}" y2="{y}" stroke="#d7e3f1" stroke-opacity="0.16"/>')

    x_ticks = []
    for row in rows[::2]:
        x, _ = point(row["hours"], 0)
        x_ticks.append(
            f'<text x="{x}" y="{height - 14}" text-anchor="middle" fill="#7e93ad" font-size="12">{int(row["hours"])}h</text>'
        )

    y_ticks = []
    for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
        _, y = point(0, ratio)
        y_ticks.append(
            f'<text x="16" y="{y + 4}" fill="#7e93ad" font-size="12">{ratio:.2f}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#081018"/>
      <stop offset="100%" stop-color="#122334"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" rx="24" fill="url(#bg)"/>
  <text x="{padding}" y="26" fill="#f4f8fc" font-size="20" font-weight="700">Decay behavior over time</text>
  <text x="{padding}" y="48" fill="#8ea4bf" font-size="13">Default decay rate = {DECAY_RATE} per hour. Pinned memories flatten at 0.30.</text>
  {''.join(tick_lines)}
  <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#8ea4bf" stroke-opacity="0.5"/>
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#8ea4bf" stroke-opacity="0.5"/>
  <path d="{path_for('regular_importance')}" fill="none" stroke="#38b48b" stroke-width="4" stroke-linecap="round"/>
  <path d="{path_for('pinned_importance')}" fill="none" stroke="#ff9b71" stroke-width="4" stroke-linecap="round" stroke-dasharray="10 7"/>
  <circle cx="{width - 216}" cy="73" r="5" fill="#38b48b"/>
  <text x="{width - 202}" y="78" fill="#e7f0f8" font-size="12">Regular memory</text>
  <circle cx="{width - 216}" cy="99" r="5" fill="#ff9b71"/>
  <text x="{width - 202}" y="104" fill="#e7f0f8" font-size="12">Pinned memory floor</text>
  {''.join(x_ticks)}
  {''.join(y_ticks)}
</svg>"""

    (ASSETS_DIR / "decay-behavior.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
