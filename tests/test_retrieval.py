from __future__ import annotations

from memos.core.models import MemoryNode
from memos.core.store import MemoryStore
from memos.retrieval.injector import retrieve_context


def test_store_and_retrieval_end_to_end(tmp_path):
    store = MemoryStore(user_id="test", persist_path=tmp_path)
    store.add(MemoryNode(content="Ajith is building MemOS for his portfolio.", entity_type="project", importance=0.8))
    store.add(MemoryNode(content="MemOS uses a forgetting engine for memory decay.", entity_type="fact", importance=0.7))

    context = retrieve_context("What is MemOS building toward?", store, top_k=5)

    assert "MEMORY CONTEXT" in context
    assert "MemOS" in context
    assert store.stats()["total_nodes"] >= 2
