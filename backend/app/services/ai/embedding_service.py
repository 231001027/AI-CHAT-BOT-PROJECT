"""
Pluggable embedding backends.

Anthropic does not offer an embeddings endpoint, so the default is fastembed,
which runs in-process and needs no key or outbound network. OpenAI and Voyage
adapters are provided for institutions that prefer a hosted model.

Every backend is loaded lazily so importing this module never pulls a heavy
dependency or opens a connection.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Sequence

import httpx

from app.config import get_settings

logger = logging.getLogger("nipmed.rag.embeddings")


class EmbeddingError(RuntimeError):
    """Raised when embeddings cannot be produced."""


class EmbeddingService(ABC):
    """Common interface over the embedding backends."""

    #: Vector width, needed to create the Qdrant collection.
    dimensions: int
    #: Human-readable model identifier recorded on audit rows.
    model_name: str

    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts as documents."""

    async def embed_query(self, text: str) -> list[float]:
        """
        Embed a single search query.

        Some models use a different prefix for queries than documents; the base
        implementation treats them identically.
        """
        vectors = await self.embed([text])
        if not vectors:
            raise EmbeddingError("Embedding backend returned no vector for the query.")
        return vectors[0]


class FastEmbedService(EmbeddingService):
    """
    Local embeddings via fastembed (ONNX, CPU).

    The model is downloaded once on first use and cached on disk. Encoding is
    synchronous and CPU-bound, so it runs in a worker thread to avoid blocking
    the event loop.
    """

    def __init__(self, model_name: str, dimensions: int) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self._model = None
        self._lock = asyncio.Lock()

    async def _get_model(self):
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is not None:
                return self._model
            try:
                from fastembed import TextEmbedding
            except ImportError as exc:
                raise EmbeddingError(
                    "The 'fastembed' package is not installed. Install it, or set "
                    "EMBEDDING_PROVIDER to 'openai' or 'voyage'."
                ) from exc

            logger.info("Loading fastembed model %s (first run downloads it)", self.model_name)
            self._model = await asyncio.to_thread(TextEmbedding, model_name=self.model_name)
            return self._model

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = await self._get_model()
        try:
            vectors = await asyncio.to_thread(lambda: [v.tolist() for v in model.embed(list(texts))])
        except Exception as exc:
            raise EmbeddingError(f"fastembed failed to encode: {exc}") from exc
        return vectors


class OpenAIEmbeddingService(EmbeddingService):
    """Embeddings via the OpenAI REST API."""

    def __init__(self, model_name: str, dimensions: int, api_key: str) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self._api_key = api_key

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            raise EmbeddingError("OPENAI_API_KEY is not set.")

        payload: dict[str, object] = {"model": self.model_name, "input": list(texts)}
        # Only the -3 models accept an explicit width.
        if self.dimensions and "text-embedding-3" in self.model_name:
            payload["dimensions"] = self.dimensions

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"OpenAI embeddings request failed: {exc}") from exc

        items = sorted(body.get("data", []), key=lambda d: d.get("index", 0))
        return [item["embedding"] for item in items]


class VoyageEmbeddingService(EmbeddingService):
    """Embeddings via Voyage AI, which pairs well with Claude."""

    def __init__(self, model_name: str, dimensions: int, api_key: str) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self._api_key = api_key

    async def _call(self, texts: Sequence[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            raise EmbeddingError("VOYAGE_API_KEY is not set.")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.voyageai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model_name,
                        "input": list(texts),
                        "input_type": input_type,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Voyage embeddings request failed: {exc}") from exc

        items = sorted(body.get("data", []), key=lambda d: d.get("index", 0))
        return [item["embedding"] for item in items]

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._call(texts, "document")

    async def embed_query(self, text: str) -> list[float]:
        # Voyage scores noticeably better when queries are marked as such.
        vectors = await self._call([text], "query")
        if not vectors:
            raise EmbeddingError("Voyage returned no vector for the query.")
        return vectors[0]


@lru_cache
def get_embedding_service() -> Optional[EmbeddingService]:
    """
    Build the configured backend, or None when embeddings are unavailable.

    Returning None rather than raising lets callers fall back to the static
    explanation instead of failing the request.
    """
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()

    if provider == "fastembed":
        return FastEmbedService(settings.embedding_model, settings.embedding_dimensions)

    if provider == "openai":
        if not settings.openai_api_key:
            logger.warning("EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is unset")
            return None
        return OpenAIEmbeddingService(
            settings.embedding_model, settings.embedding_dimensions, settings.openai_api_key
        )

    if provider == "voyage":
        if not settings.voyage_api_key:
            logger.warning("EMBEDDING_PROVIDER=voyage but VOYAGE_API_KEY is unset")
            return None
        return VoyageEmbeddingService(
            settings.embedding_model, settings.embedding_dimensions, settings.voyage_api_key
        )

    logger.warning("Unknown EMBEDDING_PROVIDER %r; RAG indexing disabled", provider)
    return None
