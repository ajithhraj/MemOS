from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
import uuid

EntityType = Literal["person", "project", "decision", "preference", "fact", "event"]


@dataclass
class MemoryNode:
    """Single memory unit stored in both the graph and vector layers."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    entity_type: EntityType = "fact"
    importance: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0
    relations: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    pinned: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self, boost: float = 0.05) -> None:
        """Refresh last access and lightly reinforce the memory."""
        self.last_accessed = datetime.now(UTC)
        self.access_count += 1
        self.importance = min(1.0, round(self.importance + boost, 4))

    def hours_since_access(self, now: datetime | None = None) -> float:
        reference = now or datetime.now(UTC)
        delta = reference - self.last_accessed
        return max(0.0, delta.total_seconds() / 3600)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "entity_type": self.entity_type,
            "importance": round(self.importance, 4),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "relations": list(self.relations),
            "embedding": list(self.embedding),
            "pinned": self.pinned,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryNode":
        payload = dict(data)
        for key in ("created_at", "last_accessed"):
            value = payload.get(key)
            if isinstance(value, str):
                payload[key] = datetime.fromisoformat(value)
        payload.setdefault("metadata", {})
        payload.setdefault("relations", [])
        payload.setdefault("embedding", [])
        return cls(**payload)


if __name__ == "__main__":
    node = MemoryNode(content="Ajith is building MemOS.", entity_type="project")
    print(node.to_dict())
