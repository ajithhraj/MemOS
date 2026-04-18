from __future__ import annotations

from .models import EntityType

ENTITY_HINTS: dict[EntityType, tuple[str, ...]] = {
    "decision": ("decide", "decision", "chose", "will", "must", "plan to"),
    "preference": ("prefer", "like", "love", "hate", "favorite", "usually"),
    "project": ("build", "project", "app", "system", "prototype", "portfolio"),
    "event": ("today", "tomorrow", "yesterday", "meeting", "launch", "deadline"),
    "person": ("my name is", "i am", "works at", "teammate", "friend"),
    "fact": tuple(),
}

BASE_SCORES: dict[EntityType, float] = {
    "decision": 0.9,
    "preference": 0.75,
    "project": 0.7,
    "person": 0.65,
    "event": 0.6,
    "fact": 0.5,
}


def infer_entity_type(text: str) -> EntityType:
    lowered = text.lower()
    for entity_type, hints in ENTITY_HINTS.items():
        if any(hint in lowered for hint in hints):
            return entity_type
    if any(token.istitle() for token in text.split()):
        return "person"
    return "fact"


def score_content(content: str, entity_type: EntityType | None = None, pinned: bool = False) -> float:
    resolved = entity_type or infer_entity_type(content)
    score = BASE_SCORES[resolved]
    if len(content.split()) > 12:
        score += 0.05
    if any(word in content.lower() for word in ("critical", "important", "remember")):
        score += 0.1
    if pinned:
        score += 0.1
    return min(1.0, round(score, 4))
