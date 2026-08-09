"""Unit tests for deterministic knowledge retrieval."""

from __future__ import annotations

import pytest

from app.models.enums import AgentType, Vertical
from app.services.agent_seed_data import KNOWLEDGE_ENTRIES
from app.services.knowledge_base import (
    KnowledgeSnapshot,
    expand_query,
    format_answer,
    rank_entries,
    score_entry,
    tokenize,
)


def _snapshot(**overrides) -> KnowledgeSnapshot:
    defaults = {
        "slug": "test-entry",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": (),
        "topic": "Working hours",
        "question": "What are the working hours?",
        "answer": "Monday to Friday, 9 AM to 5 PM.",
        "keywords": ("timing", "hours", "open"),
        "priority": 0,
    }
    defaults.update(overrides)
    return KnowledgeSnapshot(**defaults)


def _seed_snapshots() -> list[KnowledgeSnapshot]:
    return [
        KnowledgeSnapshot(
            slug=e["slug"],
            vertical=e["vertical"],
            agent_types=tuple(e.get("agent_types") or ()),
            topic=e["topic"],
            question=e["question"],
            answer=e["answer"],
            keywords=tuple(e.get("keywords") or ()),
            priority=e.get("priority", 0),
        )
        for e in KNOWLEDGE_ENTRIES
    ]


class TestTokenize:
    def test_strips_punctuation_and_lowercases(self):
        assert tokenize("What ARE your Hours?!") == ["hours"]

    def test_drops_stopwords_and_single_chars(self):
        assert tokenize("I have a b hearing problem") == ["hearing", "problem"]

    def test_handles_empty_input(self):
        assert tokenize("") == []
        assert tokenize(None) == []


class TestExpandQuery:
    def test_adds_synonyms_both_directions(self):
        expanded = expand_query(["cost"])
        assert "fee" in expanded
        assert "charges" in expanded

    def test_variant_maps_back_to_canonical(self):
        expanded = expand_query(["stammer"])
        assert "speech" in expanded

    def test_unknown_token_survives_unchanged(self):
        assert expand_query(["zebra"]) == {"zebra"}


class TestScoreEntry:
    def test_keyword_hit_outranks_answer_only_hit(self):
        keyword_entry = _snapshot(slug="kw", keywords=("tinnitus",), question="x", answer="y", topic="z")
        answer_entry = _snapshot(slug="ans", keywords=(), question="x", answer="tinnitus", topic="z")
        terms = {"tinnitus"}
        assert score_entry(terms, keyword_entry).score > score_entry(terms, answer_entry).score

    def test_no_overlap_scores_zero(self):
        assert score_entry({"unrelated"}, _snapshot()).score == 0.0

    def test_empty_query_scores_zero(self):
        assert score_entry(set(), _snapshot()).score == 0.0

    def test_priority_raises_score(self):
        low = _snapshot(slug="low", priority=0)
        high = _snapshot(slug="high", priority=10)
        terms = {"hours"}
        assert score_entry(terms, high).score > score_entry(terms, low).score

    def test_matched_terms_reported(self):
        result = score_entry({"hours", "timing"}, _snapshot())
        assert set(result.matched_terms) == {"hours", "timing"}


class TestRankEntries:
    def test_returns_best_match_first(self):
        hits = rank_entries("what time do you open", _seed_snapshots(), limit=3)
        assert hits
        assert hits[0].entry.slug == "working-hours"

    def test_respects_limit(self):
        hits = rank_entries("hearing child appointment report", _seed_snapshots(), limit=2)
        assert len(hits) <= 2

    def test_filters_by_agent_type(self):
        entries = [
            _snapshot(slug="scheduling-only", agent_types=(AgentType.SCHEDULING.value,)),
            _snapshot(slug="everyone", agent_types=()),
        ]
        hits = rank_entries("hours", entries, agent_type=AgentType.COUNSELLING.value)
        slugs = {h.entry.slug for h in hits}
        assert "scheduling-only" not in slugs
        assert "everyone" in slugs

    def test_department_entries_visible_to_every_vertical(self):
        entries = [_snapshot(slug="dept", vertical=Vertical.DEPARTMENT.value)]
        hits = rank_entries("hours", entries, vertical=Vertical.SLP.value)
        assert [h.entry.slug for h in hits] == ["dept"]

    def test_vertical_filter_excludes_other_verticals(self):
        entries = [_snapshot(slug="aud", vertical=Vertical.AUDIOLOGY.value)]
        assert rank_entries("hours", entries, vertical=Vertical.SLP.value) == []

    def test_irrelevant_query_returns_nothing(self):
        assert rank_entries("cricket score yesterday", _seed_snapshots()) == []

    def test_ordering_is_deterministic(self):
        snapshots = _seed_snapshots()
        first = [h.entry.slug for h in rank_entries("appointment change", snapshots, limit=5)]
        second = [h.entry.slug for h in rank_entries("appointment change", snapshots, limit=5)]
        assert first == second

    @pytest.mark.parametrize(
        "query,expected_slug",
        [
            ("how do I reach the campus", "location-directions"),
            ("what documents should I bring", "documents-to-bring"),
            ("when will my report be ready", "report-turnaround"),
            ("is the hearing aid free", "hearing-aid-provision"),
            ("what if there is an emergency at night", "emergency-contact"),
        ],
    )
    def test_representative_questions_route_to_expected_entry(self, query, expected_slug):
        hits = rank_entries(query, _seed_snapshots(), limit=3)
        assert expected_slug in {h.entry.slug for h in hits}


class TestFormatAnswer:
    def test_single_hit_returns_bare_answer(self):
        hits = rank_entries("what time do you open", _seed_snapshots(), limit=1)
        assert format_answer(hits) == hits[0].entry.answer

    def test_multiple_hits_are_labelled_by_topic(self):
        hits = rank_entries("appointment", _seed_snapshots(), limit=3)
        if len(hits) > 1:
            assert hits[0].entry.topic in format_answer(hits)

    def test_no_hits_returns_empty_string(self):
        assert format_answer([]) == ""


class TestSeedDataIntegrity:
    def test_slugs_are_unique(self):
        slugs = [e["slug"] for e in KNOWLEDGE_ENTRIES]
        assert len(slugs) == len(set(slugs))

    def test_every_entry_has_keywords_and_answer(self):
        for entry in KNOWLEDGE_ENTRIES:
            assert entry["keywords"], f"{entry['slug']} has no keywords"
            assert entry["answer"].strip(), f"{entry['slug']} has an empty answer"

    def test_verticals_are_valid(self):
        valid = {v.value for v in Vertical}
        assert all(e["vertical"] in valid for e in KNOWLEDGE_ENTRIES)

    def test_declared_agent_types_are_valid(self):
        valid = {a.value for a in AgentType}
        for entry in KNOWLEDGE_ENTRIES:
            for agent_type in entry.get("agent_types") or []:
                assert agent_type in valid, f"{entry['slug']} references unknown agent {agent_type}"
