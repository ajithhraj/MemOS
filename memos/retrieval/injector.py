from __future__ import annotations

from ..core.extractor import extract
from ..core.models import MemoryNode
from ..core.store import MemoryStore


def retrieve_context(
    query: str,
    store: MemoryStore,
    top_k: int = 8,
    graph_weight: float = 0.6,
    vector_weight: float = 0.3,
    recency_weight: float = 0.1,
) -> str:
    """Build ranked memory context for an LLM prompt."""
    query_nodes = extract(query)
    query_ids: list[str] = []
    for query_node in query_nodes:
        query_ids.extend(store.find_matching_ids(query_node.content))
    query_ids.extend(store.find_matching_ids(query))
    query_ids = list(dict.fromkeys(query_ids))

    graph_results = store.query_graph(query_ids, depth=2)
    vector_results = store.query_vector(query, n=15)

    merged: dict[str, MemoryNode] = {}
    for node in graph_results:
        merged[node.id] = node
    for node in vector_results:
        if node.id in merged:
            merged[node.id].metadata["_vector_similarity"] = node.metadata.get("_vector_similarity", 0.0)
        else:
            merged[node.id] = node

    ranked = sorted(
        merged.values(),
        key=lambda node: _score_node(
            node=node,
            graph_weight=graph_weight,
            vector_weight=vector_weight,
            recency_weight=recency_weight,
        ),
        reverse=True,
    )[:top_k]

    if not ranked:
        return ""

    for node in ranked:
        store.touch(node.id)

    lines = ["[MEMORY CONTEXT]", "Use these memories if they improve the answer:"]
    for index, node in enumerate(ranked, start=1):
        lines.append(
            f"{index}. [{node.entity_type.upper()}] {node.content} "
            f"(importance={node.importance:.2f}, last_seen={_age_label(node)})"
        )
    return "\n".join(lines)


def _score_node(node: MemoryNode, graph_weight: float, vector_weight: float, recency_weight: float) -> float:
    graph_relevance = node.metadata.get("_graph_relevance", node.importance)
    vector_similarity = node.metadata.get("_vector_similarity", 0.0)
    recency_bonus = 1.0 / (1.0 + node.hours_since_access())
    return (
        graph_weight * float(graph_relevance)
        + vector_weight * float(vector_similarity)
        + recency_weight * float(recency_bonus)
    )


def _age_label(node: MemoryNode) -> str:
    hours = node.hours_since_access()
    if hours < 24:
        return f"{int(hours)}h ago"
    return f"{int(hours / 24)}d ago"
