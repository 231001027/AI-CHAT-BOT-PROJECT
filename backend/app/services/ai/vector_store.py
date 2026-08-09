"""
Qdrant vector store wrapper.

Every method is failure-tolerant: if Qdrant is unreachable, search returns no
hits and indexing reports failure, rather than raising into the request path. The
caller then serves the admin-authored static explanation.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional, Sequence

from app.config import get_settings

logger = logging.getLogger("nipmed.rag.vector_store")


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: Optional[str]
    title: str
    chunk_index: int
    text: str
    score: float
    category: Optional[str] = None


class VectorStore:
    """Thin async wrapper over the Qdrant client."""

    def __init__(self, url: str, api_key: str, collection: str, dimensions: int, timeout: float):
        self._url = url
        self._api_key = api_key or None
        self._collection = collection
        self._dimensions = dimensions
        self._timeout = timeout
        self._client = None
        self._ensured = False

    @property
    def collection(self) -> str:
        return self._collection

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import AsyncQdrantClient
        except ImportError as exc:
            raise RuntimeError(
                "The 'qdrant-client' package is not installed; RAG retrieval is unavailable."
            ) from exc

        self._client = AsyncQdrantClient(
            url=self._url, api_key=self._api_key, timeout=self._timeout
        )
        return self._client

    async def ensure_collection(self) -> bool:
        """Create the collection if absent. Returns False if Qdrant is unreachable."""
        if self._ensured:
            return True
        try:
            from qdrant_client.models import Distance, VectorParams

            client = self._get_client()
            existing = await client.get_collections()
            names = {c.name for c in existing.collections}
            if self._collection not in names:
                await client.create_collection(
                    collection_name=self._collection,
                    vectors_config=VectorParams(
                        size=self._dimensions, distance=Distance.COSINE
                    ),
                )
                logger.info("Created Qdrant collection %s", self._collection)
            self._ensured = True
            return True
        except Exception as exc:
            logger.warning("Qdrant unavailable (%s); retrieval will fall back", exc)
            return False

    async def health(self) -> bool:
        try:
            client = self._get_client()
            await client.get_collections()
            return True
        except Exception:
            return False

    async def upsert_chunks(
        self,
        *,
        document_id: str,
        title: str,
        category: str,
        test_tags: Sequence[str],
        chunks: Sequence[tuple[int, str]],
        vectors: Sequence[Sequence[float]],
    ) -> int:
        """
        Index a document's chunks. Returns the number of points written.

        Raises on failure so the caller can mark the document as failed and show
        the reason on the admin screen.
        """
        if not chunks:
            return 0
        if len(chunks) != len(vectors):
            raise ValueError("chunk/vector count mismatch")

        from qdrant_client.models import PointStruct

        if not await self.ensure_collection():
            raise RuntimeError("Qdrant is not reachable.")

        client = self._get_client()
        points = [
            PointStruct(
                # Deterministic id so re-indexing replaces rather than duplicates.
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{index}")),
                vector=list(vector),
                payload={
                    "document_id": document_id,
                    "title": title,
                    "category": category,
                    "test_tags": list(test_tags),
                    "chunk_index": index,
                    "text": text,
                },
            )
            for (index, text), vector in zip(chunks, vectors)
        ]
        await client.upsert(collection_name=self._collection, points=points, wait=True)
        return len(points)

    async def search(
        self,
        vector: Sequence[float],
        *,
        limit: int = 5,
        min_score: float = 0.0,
        test_tags: Optional[Sequence[str]] = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve the nearest chunks, or an empty list if Qdrant is unavailable.

        ``test_tags`` biases results toward documents tagged for this test, but
        the filter is applied as a preference: if it yields nothing, the search is
        retried unfiltered so a mistagged corpus still returns something useful.
        """
        if not await self.ensure_collection():
            return []

        client = self._get_client()

        async def _run(with_filter: bool) -> list[Any]:
            query_filter = None
            if with_filter and test_tags:
                from qdrant_client.models import FieldCondition, Filter, MatchAny

                query_filter = Filter(
                    should=[
                        FieldCondition(
                            key="test_tags", match=MatchAny(any=list(test_tags))
                        )
                    ]
                )
            return await client.search(
                collection_name=self._collection,
                query_vector=list(vector),
                limit=limit,
                score_threshold=min_score or None,
                query_filter=query_filter,
            )

        try:
            hits = await _run(with_filter=bool(test_tags))
            if not hits and test_tags:
                # Unfiltered retry only keeps chunks that actually mention one of
                # the requested tags — otherwise a PTA document would be served
                # as an explanation of VNG just because it was nearest.
                loose = await _run(with_filter=False)
                needles = [t.lower() for t in test_tags if t]
                hits = [
                    h
                    for h in loose
                    if _chunk_mentions_test(h.payload or {}, needles)
                ]
        except Exception as exc:
            logger.warning("Qdrant search failed (%s); falling back", exc)
            return []

        results: list[RetrievedChunk] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                RetrievedChunk(
                    document_id=payload.get("document_id"),
                    title=payload.get("title", "Untitled document"),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    text=payload.get("text", ""),
                    score=float(hit.score or 0.0),
                    category=payload.get("category"),
                )
            )
        return results

    async def delete_document(self, document_id: str) -> bool:
        """Remove every chunk of a document. False if Qdrant is unreachable."""
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            if not await self.ensure_collection():
                return False
            client = self._get_client()
            await client.delete(
                collection_name=self._collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
                wait=True,
            )
            return True
        except Exception as exc:
            logger.warning("Could not delete document %s from Qdrant: %s", document_id, exc)
            return False


def _chunk_mentions_test(payload: dict[str, Any], needles: Sequence[str]) -> bool:
    """True when a chunk's tags, title or body refer to the requested test."""
    tags = [str(t).lower() for t in (payload.get("test_tags") or [])]
    if any(n in tags for n in needles):
        return True
    blob = f"{payload.get('title', '')} {payload.get('text', '')}".lower()
    return any(n in blob for n in needles)


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection=settings.qdrant_collection,
        dimensions=settings.embedding_dimensions,
        timeout=settings.qdrant_timeout_seconds,
    )
