"""NIPMED Audiology Chatbot — FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    agents,
    ai,
    auth,
    booking,
    catalog,
    chat,
    concerns,
    guidance,
    patients,
    recommendations,
    reports,
    scheduling,
    session,
    sessions,
    symptoms,
    tests,
)
from app.config import get_settings
from app.core.redis_client import close_redis
from app.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("nipmed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    yield
    await close_redis()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend for the NIEPMD Department of Speech, Hearing and Communication.\n\n"
            "Three layers share one database:\n"
            "* **Clinical flow** — registration, branching questionnaire, deterministic "
            "clinical rule engine, treatment plan and server-rendered PDF report.\n"
            "* **Assistant suite** — five agentic assistants (patient enquiry, appointment "
            "scheduling, parent counselling, hearing screening information, "
            "speech-language therapy guidance) across the Audiology, SLP and Early "
            "Intervention verticals.\n"
            "* **AI Treatment Assistant** — RAG-grounded explanations of recommended "
            "tests, drawn only from departmental documents.\n\n"
            "Clinical decisions are always deterministic. The LLM only rephrases "
            "clinician-authored content and never decides what is true, what a person "
            "has, or what they should take. If retrieval or the model is unavailable, "
            "approved static wording is served instead of an ungrounded answer."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Clinical flow: registration through report
    app.include_router(auth.router)
    app.include_router(patients.router)
    app.include_router(catalog.router)
    app.include_router(sessions.router)
    app.include_router(recommendations.router)
    app.include_router(ai.router)
    app.include_router(reports.router)
    app.include_router(admin.router)

    # Assistant suite
    app.include_router(agents.router)
    app.include_router(scheduling.router)
    app.include_router(guidance.router)

    # Original triage chat flow
    app.include_router(session.router)
    app.include_router(chat.public_router)
    app.include_router(chat.router)
    app.include_router(concerns.router)
    app.include_router(symptoms.router)
    app.include_router(tests.router)
    app.include_router(booking.router)

    @app.get("/health", response_model=HealthResponse, tags=["Utility"])
    async def health():
        return HealthResponse(
            status="ok",
            version=settings.app_version,
            environment=settings.environment,
        )

    return app


app = create_app()
