"""Application settings loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve backend/.env from this file's location so keys load whether you
# start uvicorn from repo root, backend/, or Docker's /app working directory.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NIPMED Audiology Chatbot API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    host: str = "0.0.0.0"
    port: int = 8000

    # Comma-separated origins (localhost and 127.0.0.1 are different origins in browsers)
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    database_url: str = "postgresql+asyncpg://nipmed:nipmed@localhost:55432/nipmed"

    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl_seconds: int = 86400

    # LLM provider: "auto" | "ollama" | "anthropic" | "gemini"
    # auto prefers Anthropic → Gemini → local Ollama (when OLLAMA_ENABLED=true).
    llm_provider: str = "auto"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    # Local Ollama (http://127.0.0.1:11434). No API key required.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "mistral:latest"
    ollama_enabled: bool = True
    ollama_timeout_seconds: float = 120.0

    # Agent runtime limits. The loop stops after this many tool round-trips so a
    # misbehaving model can never spin against the database indefinitely.
    agent_max_tool_iterations: int = 5
    agent_max_tokens: int = 1024

    # Departmental scheduling system integration.
    # "local"  — use our own appointment_slots tables (default, works offline)
    # "http"   — proxy to an existing HIS/HMIS REST API
    scheduling_provider: str = "local"
    scheduling_api_base_url: str = ""
    scheduling_api_key: str = ""
    scheduling_api_timeout_seconds: float = 10.0

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    jwt_refresh_expire_minutes: int = 20160  # 14 days

    # Qdrant vector store, used only by the RAG treatment-explanation module.
    # A Qdrant outage must never block registration, questionnaire or
    # recommendations, so every call site degrades to the static fallback.
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "niepmd_documents"
    qdrant_timeout_seconds: float = 10.0

    # Embeddings. Anthropic has no embedding endpoint, so the default is the
    # local fastembed model, which needs no API key or outbound network.
    #   "fastembed" — runs in-process (default)
    #   "openai"    — text-embedding-3-large et al, needs openai_api_key
    #   "voyage"    — Voyage AI, needs voyage_api_key
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384
    openai_api_key: str = ""
    voyage_api_key: str = ""

    # Chunking for document ingestion, in characters (~4 chars per token).
    rag_chunk_size: int = 2400
    rag_chunk_overlap: int = 300
    rag_top_k: int = 5
    # Below this cosine score a chunk is treated as irrelevant, and if nothing
    # clears the bar we serve the admin-authored static explanation instead of
    # letting the model answer ungrounded.
    rag_min_score: float = 0.35

    # Where uploaded hospital documents and generated PDFs are written.
    document_storage_dir: str = "data/hospital_documents"
    report_storage_dir: str = "data/reports"
    max_upload_bytes: int = 26_214_400  # 25 MB

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def anthropic_enabled(self) -> bool:
        """False when no usable Anthropic key is present."""
        key = self.anthropic_api_key
        return bool(key) and not key.startswith("sk-ant-your") and "your-key" not in key.lower()

    @property
    def gemini_enabled(self) -> bool:
        """False when no usable Gemini key is present."""
        key = (self.gemini_api_key or "").strip()
        return bool(key) and "your-key" not in key.lower() and key.lower() != "changeme"

    @property
    def ollama_ready(self) -> bool:
        """True when local Ollama is opted in and a base URL is set."""
        return bool(self.ollama_enabled and (self.ollama_base_url or "").strip())

    @property
    def llm_enabled(self) -> bool:
        """True when at least one configured LLM backend is usable."""
        return self.active_llm_provider is not None

    @property
    def active_llm_provider(self) -> str | None:
        """
        Which LLM backend will be used for text generation.

        ``auto`` prefers Anthropic → Gemini → Ollama. Agents that need Anthropic
        tool-calling still check ``anthropic_enabled`` separately.
        """
        choice = (self.llm_provider or "auto").strip().lower()
        if choice == "anthropic":
            return "anthropic" if self.anthropic_enabled else None
        if choice == "gemini":
            return "gemini" if self.gemini_enabled else None
        if choice == "ollama":
            return "ollama" if self.ollama_ready else None
        if self.anthropic_enabled:
            return "anthropic"
        if self.gemini_enabled:
            return "gemini"
        if self.ollama_ready:
            return "ollama"
        return None

    @property
    def embeddings_enabled(self) -> bool:
        """
        Whether an embedding backend is usable.

        fastembed runs locally so it is always available; the hosted providers
        need their key present.
        """
        provider = self.embedding_provider.lower()
        if provider == "fastembed":
            return True
        if provider == "openai":
            return bool(self.openai_api_key)
        if provider == "voyage":
            return bool(self.voyage_api_key)
        return False

    @property
    def document_storage_path(self) -> Path:
        path = Path(self.document_storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def report_storage_path(self) -> Path:
        path = Path(self.report_storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
