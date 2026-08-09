"""
Deterministic retrieval over clinician-authored knowledge entries.

HARD CONSTRAINT: assistants may only ever quote content that this module
returns. Ranking is plain keyword/token scoring — no embeddings, no LLM — so a
clinician can predict exactly which entry a given question will surface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

# Words carrying no retrieval signal for departmental questions.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if is are was were be been being do does did doing have has had
    i me my we our you your he she it they them this that these those to of in on at for
    with about from by as into over after before between during under again then once
    here there when where why how what which who whom whose all any both each few more
    most other some such no nor not only own same so than too very can will just should
    now please tell want need know get give would could may might us
    """.split()
)

# Terms a patient may use vs. the clinical term the knowledge base is written in.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "cost": ("fee", "fees", "charge", "charges", "price", "payment"),
    "fee": ("cost", "charges", "price"),
    "timing": ("time", "hours", "open", "opening", "schedule", "working"),
    "hours": ("timing", "time", "open", "opening"),
    "appointment": ("booking", "book", "slot", "visit", "reschedule", "cancel"),
    "booking": ("appointment", "book", "slot"),
    "report": ("result", "results", "reports"),
    "document": ("documents", "papers", "id", "proof", "card"),
    "hearing": ("hear", "deaf", "deafness", "audiology", "audiogram"),
    "screening": ("screen", "test", "checkup", "check"),
    "speech": ("talking", "talk", "language", "speaking", "stammer", "stutter"),
    "therapy": ("session", "sessions", "treatment", "training"),
    "child": ("baby", "infant", "toddler", "kid", "son", "daughter", "newborn"),
    "hearing_aid": ("aid", "aids", "machine", "device"),
    "implant": ("cochlear", "ci"),
    "location": ("address", "reach", "where", "directions", "place"),
}


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Plain snapshot of a KnowledgeEntry row so scoring stays DB-free."""

    slug: str
    vertical: str
    agent_types: tuple[str, ...]
    topic: str
    question: str
    answer: str
    keywords: tuple[str, ...]
    priority: int = 0


@dataclass(frozen=True)
class ScoredEntry:
    entry: KnowledgeSnapshot
    score: float
    matched_terms: tuple[str, ...] = field(default=())


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, drop stopwords and 1-character noise."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


# Suffixes stripped for keyword matching, longest first.
_SUFFIXES: tuple[str, ...] = ("ing", "ies", "es", "ed", "s")
_MIN_STEM_LENGTH = 3


def stem(word: str) -> str:
    """
    Crude suffix stripper so inflected words match curated keywords.

    Not linguistic stemming — "loss" becomes "los" — which is fine because both
    sides of every comparison are stemmed the same way. It exists so that
    "stammers", "stammering" and "stammer" all collide, without every keyword
    list having to enumerate its own inflections.
    """
    lowered = (word or "").lower()
    for suffix in _SUFFIXES:
        if lowered.endswith(suffix) and len(lowered) - len(suffix) >= _MIN_STEM_LENGTH:
            return lowered[: -len(suffix)]
    return lowered


def stem_all(words: Sequence[str]) -> set[str]:
    """Stem a collection of words into a set for membership tests."""
    return {stem(w) for w in words}


def expand_query(tokens: Sequence[str]) -> set[str]:
    """Add clinical synonyms so patient phrasing reaches clinician wording."""
    expanded = set(tokens)
    for token in tokens:
        for canonical, variants in SYNONYMS.items():
            if token == canonical or token in variants:
                expanded.add(canonical)
                expanded.update(variants)
    return expanded


def score_entry(query_terms: set[str], entry: KnowledgeSnapshot) -> ScoredEntry:
    """
    Weighted overlap between the query and an entry.

    Curated keywords are trusted most (weight 3), the question text next
    (weight 2), then topic (1.5) and answer body (0.5). `priority` acts as a
    small departmental thumb on the scale.
    """
    if not query_terms:
        return ScoredEntry(entry=entry, score=0.0)

    keyword_terms = {t for kw in entry.keywords for t in tokenize(kw)}
    question_terms = set(tokenize(entry.question))
    topic_terms = set(tokenize(entry.topic))
    answer_terms = set(tokenize(entry.answer))

    matched: set[str] = set()
    score = 0.0
    for weight, bucket in (
        (3.0, keyword_terms),
        (2.0, question_terms),
        (1.5, topic_terms),
        (0.5, answer_terms),
    ):
        hits = query_terms & bucket
        if hits:
            matched |= hits
            score += weight * len(hits)

    if score > 0:
        # Normalise by query size so long questions aren't unfairly favoured,
        # then apply the curated priority nudge.
        score = score / len(query_terms) + (entry.priority * 0.1)

    return ScoredEntry(entry=entry, score=round(score, 4), matched_terms=tuple(sorted(matched)))


def rank_entries(
    query: str,
    entries: Sequence[KnowledgeSnapshot],
    *,
    agent_type: Optional[str] = None,
    vertical: Optional[str] = None,
    limit: int = 3,
    min_score: float = 0.35,
) -> list[ScoredEntry]:
    """
    Rank entries for a query, filtered to the calling assistant's scope.

    An entry with an empty `agent_types` list is department-wide and visible to
    every assistant.
    """
    query_terms = expand_query(tokenize(query))

    candidates: list[KnowledgeSnapshot] = []
    for entry in entries:
        if agent_type and entry.agent_types and agent_type not in entry.agent_types:
            continue
        if vertical and entry.vertical not in (vertical, "department"):
            continue
        candidates.append(entry)

    scored = [score_entry(query_terms, e) for e in candidates]
    hits = [s for s in scored if s.score >= min_score]
    # Deterministic ordering: score desc, then priority desc, then slug asc so
    # identical scores never shuffle between requests.
    hits.sort(key=lambda s: (-s.score, -s.entry.priority, s.entry.slug))
    return hits[:limit]


def format_answer(hits: Sequence[ScoredEntry]) -> str:
    """Render ranked hits into the literal text an assistant is allowed to send."""
    if not hits:
        return ""
    if len(hits) == 1:
        return hits[0].entry.answer
    parts = [f"{h.entry.topic}: {h.entry.answer}" for h in hits]
    return "\n\n".join(parts)
