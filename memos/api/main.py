from __future__ import annotations

from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.store import MemoryStore
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="MemOS API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    data_dir = Path(__file__).resolve().parents[2] / "memos_data"
    app.state.store = MemoryStore(user_id="default", persist_path=data_dir)

    scheduler = BackgroundScheduler()
    scheduler.add_job(app.state.store.run_decay, "interval", hours=1, id="memory-decay", replace_existing=True)
    scheduler.start()
    app.state.scheduler = scheduler

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        scheduler.shutdown(wait=False)

    app.include_router(router)
    return app


app = create_app()
