from __future__ import annotations

from ..core.store import MemoryStore
from ..core.models import MemoryNode


def search_similar(store: MemoryStore, text: str, top_n: int = 15) -> list[MemoryNode]:
    return store.query_vector(text, n=top_n)
