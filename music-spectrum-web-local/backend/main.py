"""Music Spectrum Lyrics Studio - FastAPI entry point."""
from __future__ import annotations


import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    BACKGROUNDS_DIR,
    CORS_ORIGINS,
    HOST,
    LOGOS_DIR,
    LYRICS_DIR,
    MUSIC_DIR,
    OUTPUTS_DIR,
    PORT,
    PROJECT_ROOT,
)
from app.routers import ffmpeg as ffmpeg_router
from app.routers import health as health_router
from app.routers import outputs as outputs_router
from app.routers import render as render_router
from app.routers import uploads as uploads_router
from app.routers import ws as ws_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Music Spectrum Lyrics Studio",
        description="Local web app untuk render video spectrum musik + lirik dengan FFmpeg native.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router, prefix="/api")
    app.include_router(ffmpeg_router.router, prefix="/api")
    app.include_router(uploads_router.router, prefix="/api")
    app.include_router(render_router.router, prefix="/api")
    app.include_router(outputs_router.router, prefix="/api")
    app.include_router(ws_router.router)

    # Serve user storage (read-only) so frontend can preview files.
    app.mount("/storage/music", StaticFiles(directory=str(MUSIC_DIR)), name="music")
    app.mount("/storage/lyrics", StaticFiles(directory=str(LYRICS_DIR)), name="lyrics")
    app.mount("/storage/backgrounds", StaticFiles(directory=str(BACKGROUNDS_DIR)), name="backgrounds")
    app.mount("/storage/logos", StaticFiles(directory=str(LOGOS_DIR)), name="logos")
    app.mount("/storage/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

    # Optional: serve built frontend if frontend/dist exists.
    frontend_dist = PROJECT_ROOT / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


app = create_app()


def run() -> None:  # pragma: no cover
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":  # pragma: no cover
    run()
