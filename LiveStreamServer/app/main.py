"""FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts, auth, server, streams, system, videos
from app.config import get_settings
from app.services.stream_manager import get_stream_manager
from app.utils.bootstrap import bootstrap_environment


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    bootstrap_environment(settings)
    manager = get_stream_manager()
    manager.start_monitor()
    try:
        yield
    finally:
        manager.shutdown()


app = FastAPI(
    title="LiveStream Server",
    description="API server untuk multi-live streaming dengan FFmpeg.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


app.include_router(auth.router)
app.include_router(server.router)
app.include_router(videos.router)
app.include_router(accounts.router)
app.include_router(streams.router)
app.include_router(system.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    settings = get_settings()
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "version": app.version,
    }
