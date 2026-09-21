#!/usr/bin/env python3
"""
Index bundled NIEPMD guidance documents into the RAG vector store (Qdrant).

Run after Postgres is up:
    cd backend && source .venv/bin/activate && python scripts/seed_rag_corpus.py

Requires Qdrant on QDRANT_URL (default http://localhost:6333). Skips gracefully
when Qdrant or embeddings are unavailable.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models import Doctor, HospitalDocument
from app.models.enums import DocumentStatus
from app.services.ai.rag_pipeline import index_document, rag_status
from app.services.rag_corpus_data import RAG_CORPUS_DOCUMENTS


async def seed_rag_corpus() -> None:
    settings = get_settings()
    health = await rag_status()
    if not health.get("embeddings_available"):
        print("Embeddings unavailable — skip RAG corpus seed")
        return
    if not health.get("vector_store_available"):
        print("Qdrant unreachable — start Qdrant (docker compose up -d qdrant) then retry")
        return

    storage = settings.document_storage_path
    storage.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as session:
        admin = await session.scalar(select(Doctor).where(Doctor.role == "admin").limit(1))
        admin_id = admin.id if admin else None

        indexed = 0
        skipped = 0
        for doc in RAG_CORPUS_DOCUMENTS:
            slug = str(doc["slug"])
            title = str(doc["title"])
            existing = await session.scalar(
                select(HospitalDocument).where(HospitalDocument.title == title)
            )
            if existing and existing.vector_indexed:
                skipped += 1
                continue

            content = str(doc["content"])
            file_name = f"rag_corpus_{slug}.txt"
            if existing:
                row = existing
                target = Path(row.file_path)
            else:
                document_id = uuid.uuid4()
                target = storage / f"{document_id}_{file_name}"
                row = HospitalDocument(
                    id=document_id,
                    title=title,
                    category=str(doc["category"]),
                    file_path=str(target),
                    original_filename=file_name,
                    content_type="text/plain",
                    size_bytes=len(content.encode("utf-8")),
                    test_tags=[str(t) for t in doc.get("test_tags", [])],
                    uploaded_by=admin_id,
                    status=DocumentStatus.UPLOADED.value,
                )
                session.add(row)
                await session.flush()

            target.write_text(content, encoding="utf-8")
            row.size_bytes = len(content.encode("utf-8"))
            row.status = DocumentStatus.UPLOADED.value
            row.index_error = None
            await session.flush()

            result = await index_document(session, row)
            if result.success:
                indexed += 1
                print(f"Indexed: {title} ({result.chunk_count} chunks)")
            else:
                print(f"Failed: {title} — {result.error}")
                continue

        print(f"RAG corpus seed done. indexed={indexed} skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(seed_rag_corpus())
