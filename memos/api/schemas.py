from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = "default"


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=25)


class ReinforceRequest(BaseModel):
    boost: float = Field(default=0.5, ge=0.0, le=1.0)


class MessageResponse(BaseModel):
    detail: str


class GraphResponse(BaseModel):
    nodes: list[dict[str, Any]]
    links: list[dict[str, Any]]
