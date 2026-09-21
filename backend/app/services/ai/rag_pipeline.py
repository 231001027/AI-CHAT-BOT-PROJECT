"""
RAG pipeline for the AI Treatment Assistant.

Two entry points:
  * ``index_document``  — admin uploads a document, it becomes searchable.
  * ``explain_test``    — produce a grounded, patient-friendly explanation.

Degradation is the central design constraint. In order of preference an
explanation comes from grounded retrieval, then the admin-authored static text,
then a generic holding message. It is never an ungrounded LLM answer.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import AiConversation, HospitalDocument, StaticExplanation
from app.models.enums import DocumentStatus, ExplanationSource
from app.services.ai.chunking import UnsupportedDocumentError, chunk_text, extract_text
from app.services.ai.embedding_service import EmbeddingError, get_embedding_service
from app.services.ai.prompt_templates import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt,
    build_retrieval_query,
    build_static_grounded_prompt,
)
from app.services.ai.vector_store import RetrievedChunk, get_vector_store

logger = logging.getLogger("nipmed.rag.pipeline")

# Last-resort wording when there is no corpus and no admin fallback for a test.
GENERIC_FALLBACK = (
    "Your audiologist will explain this test in detail at your appointment, "
    "including what will happen and how to prepare. If you would like to know "
    "anything before then, please call the department on 044-2452-0639 and the "
    "staff will be glad to help."
)


@dataclass
class IndexResult:
    success: bool
    chunk_count: int = 0
    error: Optional[str] = None


@dataclass
class ExplanationResult:
    test_name: str
    explanation: str
    source: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


async def index_document(db: AsyncSession, document: HospitalDocument) -> IndexResult:
    """
    Extract, chunk, embed and index one uploaded document.

    Updates the document row with the outcome so the admin screen can show
    progress and any error, then commits.
    """
    settings = get_settings()

    document.status = DocumentStatus.INDEXING.value
    document.index_error = None
    await db.flush()

    embedder = get_embedding_service()
    if embedder is None:
        return await _fail(
            db,
            document,
            "No embedding backend is configured. Set EMBEDDING_PROVIDER and its API key.",
        )

    try:
        text = extract_text(Path(document.file_path), content_type=document.content_type)
    except UnsupportedDocumentError as exc:
        return await _fail(db, document, str(exc))
    except Exception as exc:
        logger.exception("Text extraction failed for %s", document.id)
        return await _fail(db, document, f"Could not read the file: {exc}")

    chunks = chunk_text(
        text, chunk_size=settings.rag_chunk_size, overlap=settings.rag_chunk_overlap
    )
    if not chunks:
        return await _fail(db, document, "The document contained no readable text.")

    try:
        vectors = await embedder.embed([c.text for c in chunks])
    except EmbeddingError as exc:
        return await _fail(db, document, str(exc))
    except Exception as exc:
        logger.exception("Embedding failed for %s", document.id)
        return await _fail(db, document, f"Embedding failed: {exc}")

    store = get_vector_store()
    try:
        # Replace any previous version of this document before writing.
        await store.delete_document(str(document.id))
        written = await store.upsert_chunks(
            document_id=str(document.id),
            title=document.title,
            category=document.category,
            test_tags=document.test_tags or [],
            chunks=[(c.index, c.text) for c in chunks],
            vectors=vectors,
        )
    except Exception as exc:
        logger.exception("Qdrant indexing failed for %s", document.id)
        return await _fail(db, document, f"Vector store rejected the document: {exc}")

    document.status = DocumentStatus.INDEXED.value
    document.vector_indexed = True
    document.chunk_count = written
    document.index_error = None
    await db.commit()
    logger.info("Indexed %s into %s chunks", document.title, written)
    return IndexResult(success=True, chunk_count=written)


async def _fail(db: AsyncSession, document: HospitalDocument, message: str) -> IndexResult:
    document.status = DocumentStatus.FAILED.value
    document.vector_indexed = False
    document.chunk_count = 0
    document.index_error = message
    await db.commit()
    logger.warning("Indexing failed for %s: %s", document.id, message)
    return IndexResult(success=False, error=message)


async def remove_document_vectors(document_id: uuid.UUID) -> bool:
    return await get_vector_store().delete_document(str(document_id))


# ---------------------------------------------------------------------------
# Retrieval and generation
# ---------------------------------------------------------------------------


async def retrieve(
    test_name: str,
    *,
    test_code: Optional[str] = None,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    question: Optional[str] = None,
) -> list[RetrievedChunk]:
    """
    Fetch grounding chunks for a test. Returns [] on any failure.

    Callers treat an empty list as "fall back to static", so no exception is
    allowed to escape into the request path.
    """
    settings = get_settings()
    embedder = get_embedding_service()
    if embedder is None:
        return []

    query = build_retrieval_query(
        test_name,
        test_code=test_code,
        flow_type=flow_type,
        child_subtype=child_subtype,
        question=question,
    )

    try:
        vector = await embedder.embed_query(query)
    except Exception as exc:
        logger.warning("Query embedding failed (%s); falling back", exc)
        return []

    tags = [t for t in {test_code, test_name} if t]
    return await get_vector_store().search(
        vector,
        limit=settings.rag_top_k,
        min_score=settings.rag_min_score,
        test_tags=tags,
    )


async def retrieve_for_message(message: str) -> list[RetrievedChunk]:
    """
    Retrieve grounding chunks for the public AI assistant.

    Uses the visitor's message as the query with no test-tag filter so general
    departmental guidance can surface alongside test-specific documents.
    """
    settings = get_settings()
    embedder = get_embedding_service()
    if embedder is None:
        return []

    query = message.strip()
    if not query:
        return []

    try:
        vector = await embedder.embed_query(query)
    except Exception as exc:
        logger.warning("Assistant query embedding failed (%s); falling back", exc)
        return []

    return await get_vector_store().search(
        vector,
        limit=settings.rag_top_k,
        min_score=settings.rag_min_score,
        test_tags=None,
    )


async def _generate(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call the configured LLM (Anthropic or Gemini). Returns None on failure."""
    from app.services.ai.llm import generate_text

    return await generate_text(system_prompt, user_prompt)


async def static_explanation_for(
    db: AsyncSession, *, test_code: Optional[str], test_name: str
) -> Optional[str]:
    """Look up the admin-authored fallback, by code then by name."""
    if test_code:
        row = await db.scalar(
            select(StaticExplanation).where(
                StaticExplanation.test_code == test_code.strip().upper()
            )
        )
        if row:
            return row.explanation

    row = await db.scalar(
        select(StaticExplanation).where(StaticExplanation.test_name.ilike(test_name.strip()))
    )
    return row.explanation if row else None


async def explain_test(
    db: AsyncSession,
    *,
    test_name: str,
    test_code: Optional[str] = None,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    patient_age: Optional[int] = None,
    question: Optional[str] = None,
    patient_id: Optional[uuid.UUID] = None,
    session_id: Optional[uuid.UUID] = None,
    log: bool = True,
) -> ExplanationResult:
    """
    Produce a patient-friendly explanation of a recommended test.

    Preference order:
      1. LLM answer grounded on retrieved chunks (source=rag)
      2. The retrieved chunks themselves, lightly formatted (source=rag) —
         used when the model is down so a corpus hit is never thrown away
      3. LLM rephrase of admin-authored static text (source=static_fallback)
      4. Raw admin-authored static text (source=static_fallback)
      5. Generic holding message (source=static_fallback)

    An ungrounded LLM answer is never returned.
    """
    settings = get_settings()

    chunks = await retrieve(
        test_name,
        test_code=test_code,
        flow_type=flow_type,
        child_subtype=child_subtype,
        question=question,
    )

    explanation: Optional[str] = None
    source = ExplanationSource.STATIC_FALLBACK.value
    model_used: Optional[str] = None
    # Preserve retrieval for the audit trail even if generation fails.
    audit_chunks = list(chunks)

    if chunks:
        user_prompt = build_explanation_prompt(
            test_name,
            chunks,
            flow_type=flow_type,
            child_subtype=child_subtype,
            question=question,
            patient_age=patient_age,
        )
        generated = await _generate(EXPLANATION_SYSTEM_PROMPT, user_prompt)
        if generated:
            explanation = generated
            source = ExplanationSource.RAG.value
            model_used = _model_label(settings)
        else:
            # Model unavailable — still serve the grounded extracts so a working
            # corpus is never discarded for a generic holding message.
            explanation = _format_extract_fallback(test_name, chunks)
            source = ExplanationSource.RAG.value

    if explanation is None:
        static = await static_explanation_for(db, test_code=test_code, test_name=test_name)
        audit_chunks = []
        if static:
            user_prompt = build_static_grounded_prompt(
                test_name,
                static,
                flow_type=flow_type,
                child_subtype=child_subtype,
                question=question,
                patient_age=patient_age,
            )
            generated = await _generate(EXPLANATION_SYSTEM_PROMPT, user_prompt)
            if generated:
                explanation = generated
                model_used = _model_label(settings)
            else:
                explanation = static
            source = ExplanationSource.STATIC_FALLBACK.value

    if explanation is None:
        explanation = GENERIC_FALLBACK
        source = ExplanationSource.STATIC_FALLBACK.value
        audit_chunks = []

    if log:
        db.add(
            AiConversation(
                patient_id=patient_id,
                session_id=session_id,
                recommended_test_name=test_name,
                question=question,
                prompt_context=[
                    {
                        "document_id": c.document_id,
                        "title": c.title,
                        "chunk_index": c.chunk_index,
                        "score": round(c.score, 4),
                        "text": c.text,
                    }
                    for c in audit_chunks
                ],
                response_text=explanation,
                source=source,
                model=model_used,
            )
        )
        await db.commit()

    return ExplanationResult(
        test_name=test_name,
        explanation=explanation,
        source=source,
        chunks=list(audit_chunks),
        model=model_used,
    )


def _model_label(settings) -> Optional[str]:
    provider = settings.active_llm_provider
    if provider == "ollama":
        return settings.ollama_model
    if provider == "gemini":
        return settings.gemini_model
    if provider == "anthropic":
        return settings.anthropic_model
    return provider


def _format_extract_fallback(test_name: str, chunks: Sequence[RetrievedChunk]) -> str:
    """
    Assemble a readable answer from retrieved extracts when the LLM is down.

    Kept deliberately plain: no diagnosis, no invention — only the hospital's own
    wording, attributed to its source documents.
    """
    parts = [
        f"Here is what the department's guidance says about {test_name}:",
        "",
    ]
    for index, chunk in enumerate(chunks[:3], start=1):
        body = " ".join(chunk.text.split())
        if len(body) > 1200:
            body = body[:1197].rstrip() + "…"
        parts.append(f"From “{chunk.title}” ({index}):")
        parts.append(body)
        parts.append("")
    parts.append(
        "Your audiologist will go through this with you at the appointment and "
        "answer any questions specific to your situation."
    )
    return "\n".join(parts).strip()


async def rag_status() -> dict[str, object]:
    """Health summary for the admin dashboard."""
    settings = get_settings()
    embedder = get_embedding_service()
    store = get_vector_store()
    return {
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model if embedder else None,
        "embeddings_available": embedder is not None,
        "llm_available": settings.llm_enabled,
        "llm_provider": settings.active_llm_provider,
        "llm_model": _model_label(settings),
        "vector_store_available": await store.health(),
        "collection": store.collection,
    }
