"""WebSocket endpoint for realtime job + log streaming."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.jobs import store

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    queue = await store.subscribe()
    try:
        # Initial snapshot
        snapshot = [j.to_info().model_dump() for j in store.list()]
        await ws.send_text(json.dumps({"type": "snapshot", "jobs": snapshot}))
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                await ws.send_text(json.dumps(payload))
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        store.unsubscribe(queue)
