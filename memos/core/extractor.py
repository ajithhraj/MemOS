from __future__ import annotations

from collections.abc import Iterable
import json
import os
import re
from typing import Any

from .models import MemoryNode
from .scorer import infer_entity_type, score_content

try:
    import anthropic
except Exception:  # pragma: no cover - optional dependency
    anthropic = None

SYSTEM_PROMPT = """You are a memory extractor. Given a message, extract memorable facts as JSON.
Each item must contain:
- content: short, human-readable fact
- entity_type: one of [person, project, decision, preference, fact, event]
- importance: float from 0.0 to 1.0
- relations: list of related names or entities
Return valid JSON only."""

CLAUDE_MODEL = os.getenv("MEMOS_EXTRACT_MODEL", "claude-3-5-haiku-latest")


def extract(text: str) -> list[MemoryNode]:
    """Extract memory nodes from user text."""
    normalized = text.strip()
    if len(normalized) < 3:
        return []

    if anthropic is not None and os.getenv("ANTHROPIC_API_KEY"):
        nodes = _extract_with_anthropic(normalized)
        if nodes:
            return nodes

    return _extract_with_rules(normalized)


def _extract_with_anthropic(text: str) -> list[MemoryNode]:
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        parts = getattr(response, "content", [])
        raw = "".join(getattr(part, "text", "") for part in parts).strip()
        payload = json.loads(raw)
        return _nodes_from_payload(payload, text)
    except Exception:
        return []


def _extract_with_rules(text: str) -> list[MemoryNode]:
    pinned = text.lower().startswith("!remember")
    cleaned = re.sub(r"^!remember\s*", "", text, flags=re.IGNORECASE).strip()
    segments = [segment.strip(" .") for segment in re.split(r"[.!?;\n]+", cleaned) if segment.strip()]
    nodes: list[MemoryNode] = []
    for segment in segments[:8]:
        entity_type = infer_entity_type(segment)
        relations = _extract_relations(segment)
        node = MemoryNode(
            content=segment,
            entity_type=entity_type,
            importance=score_content(segment, entity_type=entity_type, pinned=pinned),
            pinned=pinned,
            metadata={
                "source_text": cleaned[:300],
                "relations_raw": relations,
                "extractor": "rules",
            },
        )
        nodes.append(node)
    return _deduplicate(nodes)


def _nodes_from_payload(payload: Any, source_text: str) -> list[MemoryNode]:
    if not isinstance(payload, Iterable) or isinstance(payload, (str, bytes, dict)):
        return []

    nodes: list[MemoryNode] = []
    pinned = source_text.lower().startswith("!remember")
    for item in payload:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        entity_type = item.get("entity_type") or infer_entity_type(content)
        relations = item.get("relations") if isinstance(item.get("relations"), list) else []
        try:
            importance = float(item.get("importance", score_content(content, entity_type=entity_type, pinned=pinned)))
        except (TypeError, ValueError):
            importance = score_content(content, entity_type=entity_type, pinned=pinned)
        nodes.append(
            MemoryNode(
                content=content,
                entity_type=entity_type,
                importance=max(0.0, min(1.0, importance)),
                pinned=pinned,
                metadata={
                    "source_text": source_text[:300],
                    "relations_raw": [str(value) for value in relations],
                    "extractor": "anthropic",
                },
            )
        )
    return _deduplicate(nodes)


def _extract_relations(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+\b", text)
    lowered = {word.lower() for word in ("I", "My", "The")}
    seen: set[str] = set()
    relations: list[str] = []
    for value in candidates:
        if value.lower() in lowered:
            continue
        key = value.lower()
        if key in seen:
            continue
        relations.append(value)
        seen.add(key)
    return relations


def _deduplicate(nodes: list[MemoryNode]) -> list[MemoryNode]:
    seen: set[str] = set()
    unique: list[MemoryNode] = []
    for node in nodes:
        key = node.content.lower()
        if key in seen:
            continue
        unique.append(node)
        seen.add(key)
    return unique
