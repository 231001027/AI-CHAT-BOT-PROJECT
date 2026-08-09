"""
AI subsystem for the treatment-explanation module.

Deliberately isolated: nothing in the registration, questionnaire or
recommendation path imports from here, so a Qdrant or LLM outage cannot break
the clinically essential flow.
"""

from app.services.ai.chunking import Chunk, chunk_text, extract_text
from app.services.ai.embedding_service import (
    EmbeddingError,
    EmbeddingService,
    get_embedding_service,
)
from app.services.ai.prompt_templates import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt,
    build_retrieval_query,
)
from app.services.ai.vector_store import RetrievedChunk, VectorStore, get_vector_store

__all__ = [
    "Chunk",
    "chunk_text",
    "extract_text",
    "EmbeddingError",
    "EmbeddingService",
    "get_embedding_service",
    "EXPLANATION_SYSTEM_PROMPT",
    "build_explanation_prompt",
    "build_retrieval_query",
    "RetrievedChunk",
    "VectorStore",
    "get_vector_store",
]
