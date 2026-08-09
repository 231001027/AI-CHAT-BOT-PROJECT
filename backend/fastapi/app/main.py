"""FastAPI application factory."""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import assessments, chat, contact, domain, health, sessions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("hearconnect")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Chatbot engine, domain data, and persistence APIs for the "
            "HearConnect hearing-care platform."
        ),
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    @app.on_event("startup")
    def on_startup():
        init_db()
        logger.info(
            "HearConnect API started | env=%s | db=%s",
            settings.environment,
            settings.database_url.split("://")[0],
        )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(domain.router)
    app.include_router(assessments.router)
    app.include_router(sessions.router)
    app.include_router(contact.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled error on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app
