from __future__ import annotations

from ..core.store import MemoryStore
from ..core.models import MemoryNode


def traverse_related(store: MemoryStore, seed_ids: list[str], depth: int = 2) -> list[MemoryNode]:
    return store.query_graph(seed_ids, depth=depth)
