"""System resource endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import require_token
from app.schemas import SystemResources
from app.services.system_service import collect_resources


router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(require_token)])


@router.get("/resources", response_model=SystemResources)
def system_resources() -> SystemResources:
    return collect_resources()
