"""
Guards the contract between the rule engine and the test dictionary.

If a rule recommends a code the catalogue does not describe, the patient sees a
bare acronym with no explanation of how to prepare — which is exactly the
situation that sends someone to an ABR appointment with an awake baby and oiled
hair, wasting the slot.
"""

from __future__ import annotations

from app.services.clinical_seed_data import RULES
from app.services.seed_data import TEST_CATALOG
from app.services.test_catalog_data import CLINICAL_TEST_CATALOG

CATALOG_BY_CODE = {item["code"].upper(): item for item in CLINICAL_TEST_CATALOG}
RULE_CODES = sorted({t["test_code"].upper() for rule in RULES for t in rule["tests"]})

# Preparation matters most where getting it wrong costs the appointment.
PREP_CRITICAL = {"ABR", "ASSR", "VNG", "DIX_HALL", "SWALLOW_ASSESS", "OAE", "VOICE_ASSESS"}


class TestCatalogStructure:
    def test_codes_are_unique(self):
        codes = [item["code"].upper() for item in CLINICAL_TEST_CATALOG]
        assert len(codes) == len(set(codes))

    def test_codes_are_machine_safe(self):
        for item in CLINICAL_TEST_CATALOG:
            code = item["code"]
            assert code == code.upper(), f"{code} should be uppercase"
            assert code.replace("_", "").isalnum(), f"{code} has unsafe characters"

    def test_every_entry_has_a_name_and_description(self):
        for item in CLINICAL_TEST_CATALOG:
            assert item["name"].strip()
            assert len(item["description"].strip()) > 40, f"{item['code']} description is thin"

    def test_categories_are_from_the_known_set(self):
        allowed = {
            "basic",
            "special",
            "paediatric",
            "vestibular",
            "speech",
            "referral",
            "counselling",
        }
        for item in CLINICAL_TEST_CATALOG:
            assert item["category"] in allowed, f"{item['code']} has category {item['category']}"

    def test_durations_are_plausible(self):
        for item in CLINICAL_TEST_CATALOG:
            duration = item.get("duration_minutes")
            assert duration is None or 5 <= duration <= 240, f"{item['code']}: {duration}"

    def test_every_entry_has_preparation_guidance(self):
        for item in CLINICAL_TEST_CATALOG:
            assert item.get("preparation", "").strip(), f"{item['code']} has no preparation text"

    def test_prep_critical_tests_have_substantial_guidance(self):
        for code in PREP_CRITICAL:
            entry = CATALOG_BY_CODE[code]
            assert len(entry["preparation"]) > 100, (
                f"{code} needs detailed preparation guidance; got "
                f"{len(entry['preparation'])} chars"
            )

    def test_no_diagnostic_or_prescriptive_language(self):
        # This text is shown directly to patients alongside a disclaimer that the
        # department does not diagnose through the app. Phrases are chosen to catch
        # assertions about the reader's condition, not innocent conditionals like
        # "if you have a cold".
        banned = (
            "you have hearing loss",
            "your diagnosis",
            "the diagnosis is",
            "you are suffering",
            "we will prescribe",
            "you should take",
            "this will cure",
            "you definitely",
        )
        for item in CLINICAL_TEST_CATALOG:
            blob = f"{item['description']} {item.get('preparation', '')}".lower()
            for phrase in banned:
                assert phrase not in blob, f"{item['code']} contains {phrase!r}"


class TestRuleCoverage:
    def test_every_recommended_code_is_in_the_catalogue(self):
        missing = [code for code in RULE_CODES if code not in CATALOG_BY_CODE]
        assert not missing, f"rules recommend codes with no catalogue entry: {missing}"

    def test_catalogue_has_no_unreachable_entries(self):
        # An entry no rule can emit is dead content that will silently rot.
        unreachable = sorted(set(CATALOG_BY_CODE) - set(RULE_CODES))
        assert not unreachable, f"catalogue entries no rule recommends: {unreachable}"

    def test_rule_test_names_refer_to_the_catalogued_procedure(self):
        """
        A rule may relabel a test for context — ENT_REF is shown as "Urgent ENT
        Consultation" for sudden hearing loss, and that urgency is clinically
        meaningful. What it must not do is attach a code to a different procedure,
        so the two names have to share a distinctive word.
        """
        filler = {
            "and", "or", "of", "the", "a", "for", "test", "testing", "assessment",
            "examination", "review", "consultation", "referral", "urgent",
            "clinical", "check", "session", "programme", "scheduled",
        }

        def significant(name: str) -> set[str]:
            words = name.lower().replace("(", " ").replace(")", " ").replace("-", " ").split()
            kept = {w.strip("/,") for w in words} - filler
            # Compare on stems so "Otoscopic" matches "Otoscopy".
            return {w[:6] for w in kept if w}

        for rule in RULES:
            for test in rule["tests"]:
                entry = CATALOG_BY_CODE[test["test_code"].upper()]
                if test["test_name"] == entry["name"]:
                    continue
                shared = significant(test["test_name"]) & significant(entry["name"])
                assert shared, (
                    f"rule '{rule['name']}' labels {test['test_code']} as "
                    f"'{test['test_name']}', which shares no distinctive word with "
                    f"the catalogued '{entry['name']}' — likely the wrong code"
                )

    def test_legacy_catalogue_codes_do_not_conflict(self):
        """
        The legacy triage catalogue is merged into the same table by code. Where a
        code appears in both, the clinical entry wins, so the two must at least
        agree on what the code means.
        """
        legacy = {item["code"].upper(): item for item in TEST_CATALOG}
        for code, entry in CATALOG_BY_CODE.items():
            if code in legacy:
                # Same abbreviation must not refer to two different procedures.
                assert legacy[code]["name"].split("(")[0].strip().lower()[:6] in (
                    entry["name"].lower()
                ) or entry["name"].lower()[:6] in legacy[code]["name"].lower(), (
                    f"{code}: legacy '{legacy[code]['name']}' vs "
                    f"clinical '{entry['name']}'"
                )
