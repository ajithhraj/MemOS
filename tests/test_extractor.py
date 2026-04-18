from __future__ import annotations

from memos.core.extractor import extract


def test_rule_extractor_returns_memory_nodes():
    nodes = extract("I am building a memory system for LLMs with Ajith.")

    assert nodes
    assert any(node.content.lower().startswith("i am building") for node in nodes)
    assert all(0.0 <= node.importance <= 1.0 for node in nodes)


def test_remember_prefix_creates_pinned_memories():
    nodes = extract("!remember I prefer concise project updates.")

    assert nodes
    assert all(node.pinned for node in nodes)
