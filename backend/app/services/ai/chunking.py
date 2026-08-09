"""
Text extraction and semantic chunking for uploaded documents.

Pure functions with no network or database access, so chunking behaviour is
unit-testable without a running Qdrant.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nipmed.rag.chunking")

# Paragraph break: a blank line, optionally with trailing whitespace.
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
# Sentence end followed by whitespace and a capital or digit.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WHITESPACE = re.compile(r"[ \t]+")


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    char_start: int
    char_end: int

    @property
    def length(self) -> int:
        return len(self.text)


class UnsupportedDocumentError(ValueError):
    """Raised when a file type cannot be read as text."""


def normalise_whitespace(text: str) -> str:
    """
    Collapse runs of spaces and tabs, and trim trailing space on each line.

    Paragraph breaks are preserved because chunking relies on them.
    """
    if not text:
        return ""
    lines = [_WHITESPACE.sub(" ", line).strip() for line in text.splitlines()]
    collapsed = "\n".join(lines)
    # Squash 3+ newlines down to a single paragraph break.
    return re.sub(r"\n{3,}", "\n\n", collapsed).strip()


def extract_text(path: Path | str, *, content_type: Optional[str] = None) -> str:
    """
    Read a document into plain text.

    PDF support needs pypdf; when it is not installed a PDF raises rather than
    silently indexing nothing, so the upload is marked failed and the admin can
    see why.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise UnsupportedDocumentError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md", ".markdown"} or (content_type or "").startswith("text/"):
        return normalise_whitespace(file_path.read_text(encoding="utf-8", errors="replace"))

    if suffix == ".pdf":
        return normalise_whitespace(_extract_pdf(file_path))

    if suffix == ".docx":
        return normalise_whitespace(_extract_docx(file_path))

    raise UnsupportedDocumentError(
        f"Unsupported file type '{suffix or content_type}'. Upload PDF, DOCX, TXT or MD."
    )


def _extract_pdf(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on install
        raise UnsupportedDocumentError(
            "PDF support requires the 'pypdf' package. Install it or upload a TXT/DOCX copy."
        ) from exc

    reader = PdfReader(str(file_path))
    pages: list[str] = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pragma: no cover - malformed page
            logger.warning("Could not extract page %s of %s", number, file_path.name)
    text = "\n\n".join(p for p in pages if p.strip())
    if not text.strip():
        raise UnsupportedDocumentError(
            "No text could be extracted. The PDF may be a scan; run OCR before uploading."
        )
    return text


def _extract_docx(file_path: Path) -> str:
    try:
        import docx  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on install
        raise UnsupportedDocumentError(
            "DOCX support requires the 'python-docx' package."
        ) from exc

    document = docx.Document(str(file_path))
    return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())


def _split_long_block(block: str, max_chars: int) -> list[str]:
    """
    Break an oversized paragraph on sentence boundaries.

    A paragraph longer than max_chars is split between sentences where possible,
    and only mid-sentence as a last resort for text with no sentence breaks at
    all (tables, long lists).
    """
    if len(block) <= max_chars:
        return [block]

    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_SPLIT.split(block):
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
        # A single sentence longer than the budget: hard-wrap it.
        if len(sentence) > max_chars:
            for start in range(0, len(sentence), max_chars):
                pieces.append(sentence[start : start + max_chars])
            current = ""
        else:
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def chunk_text(
    text: str,
    *,
    chunk_size: int = 2400,
    overlap: int = 300,
) -> list[Chunk]:
    """
    Split text into overlapping chunks that respect paragraph boundaries.

    Paragraphs are packed until the size budget is reached rather than cutting at
    a fixed offset, so a chunk is much more likely to contain a complete idea.
    Overlap carries the tail of the previous chunk forward so a fact spanning a
    boundary is still retrievable.
    """
    cleaned = normalise_whitespace(text)
    if not cleaned:
        return []

    chunk_size = max(200, chunk_size)
    overlap = max(0, min(overlap, chunk_size // 2))

    blocks: list[str] = []
    for block in _PARAGRAPH_SPLIT.split(cleaned):
        stripped = block.strip()
        if stripped:
            blocks.extend(_split_long_block(stripped, chunk_size))

    chunks: list[Chunk] = []
    current: list[str] = []
    current_length = 0

    def flush() -> None:
        nonlocal current, current_length
        if not current:
            return
        body = "\n\n".join(current).strip()
        if not body:
            current, current_length = [], 0
            return
        start = cleaned.find(current[0])
        chunks.append(
            Chunk(
                index=len(chunks),
                text=body,
                char_start=max(start, 0),
                char_end=max(start, 0) + len(body),
            )
        )
        if overlap:
            # Carry forward whole trailing blocks up to the overlap budget.
            carried: list[str] = []
            carried_length = 0
            for block in reversed(current):
                if carried_length + len(block) > overlap:
                    break
                carried.insert(0, block)
                carried_length += len(block)
            current = carried
            current_length = carried_length
        else:
            current, current_length = [], 0

    for block in blocks:
        if current and current_length + len(block) > chunk_size:
            flush()
        current.append(block)
        current_length += len(block)

    # Final flush without generating overlap-only trailing content.
    if current:
        body = "\n\n".join(current).strip()
        if body and (not chunks or body != chunks[-1].text):
            start = cleaned.find(current[0])
            chunks.append(
                Chunk(
                    index=len(chunks),
                    text=body,
                    char_start=max(start, 0),
                    char_end=max(start, 0) + len(body),
                )
            )

    return chunks
