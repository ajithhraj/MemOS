from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import os
import re
from typing import Any

import networkx as nx

from .decay import decay_all, should_prune
from .models import MemoryNode

try:
    import chromadb
except Exception:  # pragma: no cover - optional dependency
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None

EMBED_MODEL = "all-MiniLM-L6-v2"


class SimpleEmbedder:
    """Small dependency-free fallback embedder."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            index = hash(token) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@dataclass
class VectorHit:
    node_id: str
    score: float


class LocalVectorCollection:
    """JSON-backed vector index used when ChromaDB is unavailable."""

    def __init__(self, path: Path):
        self.path = path
        self.records: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            self.records = json.loads(self.path.read_text(encoding="utf-8"))

    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        for item_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas, strict=True):
            self.records[item_id] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata,
            }
        self._save()

    def delete(self, ids: list[str]) -> None:
        for item_id in ids:
            self.records.pop(item_id, None)
        self._save()

    def count(self) -> int:
        return len(self.records)

    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict[str, list[list[Any]]]:
        query_vector = query_embeddings[0]
        ranked = sorted(
            (
                VectorHit(node_id=item_id, score=_cosine_similarity(query_vector, record["embedding"]))
                for item_id, record in self.records.items()
            ),
            key=lambda hit: hit.score,
            reverse=True,
        )[:n_results]
        return {
            "ids": [[hit.node_id for hit in ranked]],
            "distances": [[round(1.0 - hit.score, 6) for hit in ranked]],
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")


class MemoryStore:
    def __init__(self, user_id: str = "default", persist_path: str | os.PathLike[str] = "./memos_data"):
        self.user_id = user_id
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.graph_path = self.persist_path / f"{user_id}_graph.json"
        self.vector_path = self.persist_path / f"{user_id}_vectors.json"
        self.embedder = self._build_embedder()
        self.collection = self._build_collection()
        self.graph = self._load_graph()

    def add(self, node: MemoryNode) -> MemoryNode:
        node.embedding = self._embed(node.content)
        self.collection.upsert(
            ids=[node.id],
            embeddings=[node.embedding],
            documents=[node.content],
            metadatas=[
                {
                    "importance": node.importance,
                    "entity_type": node.entity_type,
                    "node_id": node.id,
                }
            ],
        )
        self.graph.add_node(node.id, **node.to_dict())
        self._wire_relations(node)
        self._save_graph()
        return node

    def get_node(self, node_id: str) -> MemoryNode | None:
        attrs = self.graph.nodes.get(node_id)
        if not attrs:
            return None
        return MemoryNode.from_dict(attrs)

    def all_nodes(self) -> list[MemoryNode]:
        return [MemoryNode.from_dict(data) for _, data in self.graph.nodes(data=True)]

    def touch(self, node_id: str, boost: float = 0.05) -> MemoryNode | None:
        node = self.get_node(node_id)
        if node is None:
            return None
        node.touch(boost=boost)
        self._update_node(node)
        return node

    def delete(self, node_id: str) -> bool:
        if node_id not in self.graph:
            return False
        self.graph.remove_node(node_id)
        self.collection.delete(ids=[node_id])
        self._save_graph()
        return True

    def query_vector(self, text: str, n: int = 15) -> list[MemoryNode]:
        total = min(n, self.collection.count())
        if total <= 0:
            return []
        embedding = self._embed(text)
        results = self.collection.query(query_embeddings=[embedding], n_results=total)
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        nodes: list[MemoryNode] = []
        for node_id, distance in zip(ids, distances, strict=False):
            attrs = self.graph.nodes.get(node_id)
            if not attrs:
                continue
            node = MemoryNode.from_dict(attrs)
            similarity = round(1.0 - float(distance), 4)
            node.metadata["_vector_similarity"] = max(0.0, similarity)
            nodes.append(node)
        return nodes

    def query_graph(self, entity_ids: list[str], depth: int = 2) -> list[MemoryNode]:
        if not entity_ids:
            return []
        visited: set[str] = set()
        frontier = [(entity_id, 0) for entity_id in entity_ids]
        while frontier:
            current, hops = frontier.pop(0)
            if current in visited or current not in self.graph:
                continue
            visited.add(current)
            if hops >= depth:
                continue
            for neighbor in self.graph.neighbors(current):
                frontier.append((neighbor, hops + 1))
            for neighbor in self.graph.predecessors(current):
                frontier.append((neighbor, hops + 1))
        nodes = []
        for node_id in visited:
            node = self.get_node(node_id)
            if node is None:
                continue
            node.metadata["_graph_relevance"] = node.importance
            nodes.append(node)
        return nodes

    def find_matching_ids(self, text: str) -> list[str]:
        query_terms = {term.lower() for term in re.findall(r"\w+", text) if len(term) > 2}
        matches: list[str] = []
        for node_id, data in self.graph.nodes(data=True):
            haystack = data.get("content", "").lower()
            if text.lower() in haystack:
                matches.append(node_id)
                continue
            haystack_terms = set(re.findall(r"\w+", haystack))
            if query_terms and haystack_terms.intersection(query_terms):
                matches.append(node_id)
        return matches

    def run_decay(self) -> int:
        nodes = self.all_nodes()
        decayed = decay_all(nodes)
        pruned = 0
        for node in decayed:
            if should_prune(node):
                self.delete(node.id)
                pruned += 1
            else:
                self._update_node(node)
        return pruned

    def get_graph_json(self) -> dict[str, Any]:
        return nx.node_link_data(self.graph, edges="links")

    def stats(self) -> dict[str, Any]:
        nodes = self.all_nodes()
        importances = [node.importance for node in nodes]
        return {
            "total_nodes": len(nodes),
            "avg_importance": round(sum(importances) / max(len(importances), 1), 3),
            "pinned": sum(1 for node in nodes if node.pinned),
            "entity_breakdown": _count_by(nodes, key=lambda item: item.entity_type),
        }

    def export(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "stats": self.stats(),
            "graph": self.get_graph_json(),
            "nodes": [node.to_dict() for node in self.all_nodes()],
        }

    def reinforce(self, node_id: str, boost: float = 0.5) -> MemoryNode | None:
        node = self.get_node(node_id)
        if node is None:
            return None
        node.pinned = True
        node.touch(boost=boost)
        self._update_node(node)
        return node

    def _wire_relations(self, node: MemoryNode) -> None:
        relation_ids: list[str] = []
        for relation_name in node.metadata.get("relations_raw", []):
            existing = self._find_by_content(str(relation_name))
            if existing is None:
                placeholder = MemoryNode(
                    content=str(relation_name),
                    entity_type="fact",
                    importance=0.35,
                    metadata={"source": "relation_placeholder"},
                )
                placeholder.embedding = self._embed(placeholder.content)
                self.graph.add_node(placeholder.id, **placeholder.to_dict())
                self.collection.upsert(
                    ids=[placeholder.id],
                    embeddings=[placeholder.embedding],
                    documents=[placeholder.content],
                    metadatas=[{"importance": placeholder.importance, "entity_type": placeholder.entity_type, "node_id": placeholder.id}],
                )
                existing = placeholder.id
            self.graph.add_edge(node.id, existing, relation=str(relation_name))
            relation_ids.append(existing)
        if relation_ids:
            attrs = self.graph.nodes[node.id]
            attrs["relations"] = relation_ids

    def _build_embedder(self) -> Any:
        if SentenceTransformer is None:
            return SimpleEmbedder()
        try:
            return SentenceTransformer(EMBED_MODEL)
        except Exception:
            return SimpleEmbedder()

    def _build_collection(self) -> Any:
        if chromadb is None:
            return LocalVectorCollection(self.vector_path)
        try:
            client = chromadb.PersistentClient(path=str(self.persist_path))
            return client.get_or_create_collection(
                name=f"memos_{self.user_id}",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            return LocalVectorCollection(self.vector_path)

    def _embed(self, text: str) -> list[float]:
        encoded = self.embedder.encode(text)
        if hasattr(encoded, "tolist"):
            return encoded.tolist()
        return list(encoded)

    def _find_by_content(self, name: str) -> str | None:
        lowered = name.lower()
        for node_id, data in self.graph.nodes(data=True):
            content = str(data.get("content", "")).lower()
            if lowered == content or lowered in content:
                return node_id
        return None

    def _load_graph(self) -> nx.DiGraph:
        if self.graph_path.exists():
            payload = json.loads(self.graph_path.read_text(encoding="utf-8"))
            return nx.node_link_graph(payload, directed=True, edges="links")
        return nx.DiGraph()

    def _save_graph(self) -> None:
        self.graph_path.write_text(
            json.dumps(nx.node_link_data(self.graph, edges="links"), indent=2),
            encoding="utf-8",
        )

    def _update_node(self, node: MemoryNode) -> None:
        self.graph.add_node(node.id, **node.to_dict())
        self.collection.upsert(
            ids=[node.id],
            embeddings=[node.embedding or [0.0]],
            documents=[node.content],
            metadatas=[{"importance": node.importance, "entity_type": node.entity_type, "node_id": node.id}],
        )
        self._save_graph()


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


def _count_by(nodes: list[MemoryNode], key: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        label = str(key(node))
        counts[label] = counts.get(label, 0) + 1
    return counts
