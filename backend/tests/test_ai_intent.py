"""Heuristic AI intent fallback (no API key required)."""

from __future__ import annotations

from app.models.enums import ConcernType
from app.services.ai_intent import _heuristic_classify, phrase_static_content


def test_heuristic_tinnitus():
    r = _heuristic_classify("I hear constant ringing and buzzing in my ears")
    assert r.concern_type == ConcernType.TINNITUS
    assert r.confidence > 0
    assert r.reply


def test_heuristic_child():
    r = _heuristic_classify("My baby is not responding to sounds")
    assert r.concern_type == ConcernType.CHILD_CONCERNS


def test_heuristic_unknown():
    r = _heuristic_classify("What is the weather today?")
    assert r.concern_type is None


def test_phrase_fallback_returns_source():
    text = "PTA measures hearing thresholds."
    # Without API key, phrase_static_content returns source unchanged
    out = phrase_static_content(text)
    assert out.phrased == text
