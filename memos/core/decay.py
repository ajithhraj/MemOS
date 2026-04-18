from __future__ import annotations

import math

from .models import MemoryNode

DECAY_RATE = 0.008
PINNED_FLOOR = 0.3
PRUNE_THRESHOLD = 0.05


def decay_node(node: MemoryNode, rate: float = DECAY_RATE) -> MemoryNode:
    """Apply Ebbinghaus-style exponential decay to one node."""
    hours = node.hours_since_access()
    new_importance = node.importance * math.exp(-rate * hours)
    if node.pinned:
        new_importance = max(new_importance, PINNED_FLOOR)
    node.importance = round(max(0.0, new_importance), 4)
    return node


def decay_all(nodes: list[MemoryNode], rate: float = DECAY_RATE) -> list[MemoryNode]:
    return [decay_node(node, rate=rate) for node in nodes]


def should_prune(node: MemoryNode, threshold: float = PRUNE_THRESHOLD) -> bool:
    return node.importance < threshold and not node.pinned


def importance_at(initial: float, hours: float, rate: float = DECAY_RATE, pinned: bool = False) -> float:
    projected = initial * math.exp(-rate * hours)
    if pinned:
        projected = max(projected, PINNED_FLOOR)
    return round(max(0.0, projected), 4)


def reinforcement_boost(node: MemoryNode, boost: float = 0.5) -> MemoryNode:
    node.importance = min(1.0, round(node.importance + boost, 4))
    node.pinned = True
    node.touch()
    return node
