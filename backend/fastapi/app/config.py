"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the fastapi service root (backend/fastapi/.env)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


class Settings:
    app_name: str = "HearConnect AI API"
    version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Comma-separated frontend origins
    allowed_origins: list[str] = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000",
        ).split(",")
        if o.strip()
    ]

    # SQLite by default — zero-config local persistence
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_ROOT / 'data' / 'hearconnect.db'}",
    )


settings = Settings()
