from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..core.extractor import extract
from .schemas import IngestRequest, QueryRequest, ReinforceRequest

router = APIRouter()


def _store(request: Request):
    return request.app.state.store


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/memory/ingest")
async def ingest(request: Request, payload: IngestRequest):
    store = _store(request)
    nodes = extract(payload.message)
    stored = [store.add(node) for node in nodes]
    return {"stored": len(stored), "nodes": [node.to_dict() for node in stored]}


@router.post("/memory/query")
async def query(request: Request, payload: QueryRequest):
    store = _store(request)
    from ..retrieval.injector import retrieve_context

    context = retrieve_context(payload.query, store, top_k=payload.top_k)
    return {"context": context}


@router.get("/memory/graph")
async def graph(request: Request):
    return _store(request).get_graph_json()


@router.get("/memory/stats")
async def stats(request: Request):
    return _store(request).stats()


@router.get("/memory/export")
async def export(request: Request):
    return _store(request).export()


@router.post("/memory/{node_id}/reinforce")
async def reinforce(request: Request, node_id: str, payload: ReinforceRequest):
    node = _store(request).reinforce(node_id, boost=payload.boost)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.delete("/memory/{node_id}")
async def forget(request: Request, node_id: str):
    if not _store(request).delete(node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    return {"deleted": node_id}


@router.get("/memory/events")
async def memory_events(request: Request):
    async def event_stream():
        while True:
            if await request.is_disconnected():
                break
            payload = {
                "stats": _store(request).stats(),
                "graph": _store(request).get_graph_json(),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
