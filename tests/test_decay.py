from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math

from memos.core.decay import DECAY_RATE, PINNED_FLOOR, decay_node, importance_at, reinforcement_boost, should_prune
from memos.core.models import MemoryNode


def test_decay_matches_expected_curve():
    node = MemoryNode(content="Portfolio project", importance=1.0)
    node.last_accessed = datetime.now(UTC) - timedelta(hours=72)

    decay_node(node)

    expected = round(math.exp(-DECAY_RATE * 72), 4)
    assert node.importance == expected


def test_pinned_memories_do_not_fall_below_floor():
    node = MemoryNode(content="Pinned memory", importance=0.1, pinned=True)
    node.last_accessed = datetime.now(UTC) - timedelta(days=30)

    decay_node(node)

    assert node.importance == PINNED_FLOOR


def test_reinforcement_marks_node_as_pinned():
    node = MemoryNode(content="Remember this", importance=0.2)

    reinforcement_boost(node, boost=0.4)

    assert node.pinned is True
    assert node.importance > 0.2
    assert node.access_count == 1


def test_importance_at_projects_future_value():
    assert importance_at(1.0, 24) < 1.0


def test_should_prune_low_unpinned_memories():
    node = MemoryNode(content="Disposable fact", importance=0.01)
    assert should_prune(node) is True
