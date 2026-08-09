"""Health / liveness endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse

router = APIRouter(tags=["Utility"])

_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe — returns service status and uptime."""
    return {
        "status": "ok",
        "version": settings.version,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }
