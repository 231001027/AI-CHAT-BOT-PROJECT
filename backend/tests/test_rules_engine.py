"""Unit tests for the deterministic rules engine.

No LLM / network — pure functions + seed snapshots.
Covers every adult concern_type and every child age_band.
"""

from __future__ import annotations

import pytest

from app.services.rules_engine import (
    CatalogEntry,
    ConcernConfigSnapshot,
    enrich_with_catalog,
    general_recommendations_for,
    recommend_tests,
)
from app.services.seed_data import CONCERN_CONFIGS, TEST_CATALOG


def _snapshot(concern_type: str, age_band: str | None = None) -> ConcernConfigSnapshot:
    for row in CONCERN_CONFIGS:
        if row["concern_type"] == concern_type and row.get("age_band") == age_band:
            return ConcernConfigSnapshot(
                concern_type=row["concern_type"],
                age_band=row.get("age_band"),
                recommended_tests=list(row["recommended_tests"]),
                what_it_helps=row["what_it_helps"],
                outcome_options=row.get("outcome_options"),
                conditional_rules=row.get("conditional_rules"),
                common_signs=row.get("common_signs"),
            )
    raise AssertionError(f"Missing seed config: {concern_type} / {age_band}")


def _catalog() -> dict[str, CatalogEntry]:
    return {
        t["code"]: CatalogEntry(
            code=t["code"],
            name=t["name"],
            category=t["category"],
            description=t["description"],
        )
        for t in TEST_CATALOG
    }


ADULT_TYPES = [
    "hearing_difficulty",
    "tinnitus",
    "hyperacusis",
    "dizziness_balance",
    "ear_pain_discharge",
]

CHILD_BANDS = ["newborn", "infant_toddler", "preschool", "school_age"]


@pytest.mark.parametrize("concern_type", ADULT_TYPES)
def test_adult_base_recommendations(concern_type: str):
    cfg = _snapshot(concern_type)
    result = recommend_tests(cfg)
    assert result.test_codes, f"{concern_type} should recommend at least one test"
    assert result.what_it_helps
    assert result.outcome_options is None
    # Every code must exist in catalog
    catalog = _catalog()
    for code in result.test_codes:
        assert code in catalog, f"{code} missing from TestCatalog for {concern_type}"


@pytest.mark.parametrize("age_band", CHILD_BANDS)
def test_child_age_band_recommendations(age_band: str):
    cfg = _snapshot("child_concerns", age_band)
    result = recommend_tests(cfg)
    assert result.test_codes, f"child/{age_band} should recommend tests"
    assert result.outcome_options, "child pathways should expose outcome options"
    assert "Hearing Aid" in result.outcome_options
    catalog = _catalog()
    for code in result.test_codes:
        assert code in catalog, f"{code} missing from TestCatalog for child/{age_band}"


def test_child_router_config_has_no_base_tests():
    cfg = _snapshot("child_concerns", None)
    result = recommend_tests(cfg)
    assert result.test_codes == []
    assert result.outcome_options


def test_hearing_difficulty_sudden_adds_abr():
    cfg = _snapshot("hearing_difficulty")
    base = recommend_tests(cfg)
    assert "ABR" not in base.test_codes

    with_sudden = recommend_tests(cfg, {"sudden": "It was sudden yesterday"})
    assert "ABR" in with_sudden.test_codes
    assert "ABR" in with_sudden.reasons
    assert "sudden" in with_sudden.reasons["ABR"].lower() or "ABR" in with_sudden.reasons["ABR"]


def test_dizziness_conditionals_add_posturography_and_spin():
    cfg = _snapshot("dizziness_balance")
    result = recommend_tests(
        cfg,
        {"unsteady": "yes, very unsteady", "hearing_or_ringing": "some ringing"},
    )
    assert "Posturography" in result.test_codes
    assert "SPIN" in result.test_codes


def test_newborn_nicu_adds_assr():
    cfg = _snapshot("child_concerns", "newborn")
    result = recommend_tests(cfg, {"nicu": "yes, 2 weeks in NICU"})
    assert "ASSR" in result.test_codes


def test_school_age_academic_adds_srt_wrs():
    cfg = _snapshot("child_concerns", "school_age")
    result = recommend_tests(cfg, {"academic": "falling behind in class"})
    assert "SRT" in result.test_codes
    assert "WRS" in result.test_codes


def test_negative_answer_does_not_trigger_truthy_rule():
    cfg = _snapshot("dizziness_balance")
    result = recommend_tests(cfg, {"unsteady": "no"})
    assert "Posturography" not in result.test_codes


def test_enrich_with_catalog_preserves_order_and_reason():
    cfg = _snapshot("tinnitus")
    result = recommend_tests(cfg)
    enriched = enrich_with_catalog(result, _catalog())
    assert [e["code"] for e in enriched] == result.test_codes
    assert all(e["description"] for e in enriched)
    assert all(e["reason"] for e in enriched)


def test_general_recommendations_branch():
    adult = general_recommendations_for("tinnitus")
    child = general_recommendations_for("child_concerns", "preschool")
    assert "Consult an audiologist" in " ".join(adult)
    assert "paediatric" in " ".join(child).lower() or "Hearing Aid" in " ".join(child)


def test_all_seed_concern_configs_present():
    """Guardrail: seed must include 5 adult + 1 child router + 4 age bands = 10."""
    assert len(CONCERN_CONFIGS) == 10
    adult = [c for c in CONCERN_CONFIGS if c["age_band"] is None and c["concern_type"] != "child_concerns"]
    assert len(adult) == 5
    child_bands = [c for c in CONCERN_CONFIGS if c["concern_type"] == "child_concerns" and c["age_band"]]
    assert len(child_bands) == 4


def test_test_catalog_contains_required_codes():
    required = {
        "PTA", "Speech Audiometry", "Tympanometry", "OAE", "SPIN",
        "Tinnitus Assessment", "LDL", "VEMP", "VNG", "Posturography",
        "Ear Evaluation (ENT)", "Immittance Test", "ABR", "MLR", "LLR",
        "P300", "P500", "SRT", "WRS", "PB Tests", "VRA", "BOA", "ASSR",
        "Play Audiometry", "Speech Detection Threshold",
    }
    codes = {t["code"] for t in TEST_CATALOG}
    missing = required - codes
    assert not missing, f"Missing catalog codes: {missing}"
