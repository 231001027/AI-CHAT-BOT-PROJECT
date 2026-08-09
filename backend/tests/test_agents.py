"""
Unit tests for the assistant registry and supervisor routing.

No database or network required: these check the static wiring of the suite and
the deterministic routing tier.
"""

from __future__ import annotations

import pytest

from app.agents.registry import AGENTS, TOOLS, get_agent, list_agents, tools_for
from app.agents.router import (
    DEFAULT_AGENT,
    route_by_keywords,
    route_message,
    score_agents,
)
from app.agents.runtime import (
    _first_age_in_years,
    _guess_age_band,
    _guess_therapy_domain,
    _infer_fallback_args,
)
from app.models.enums import AGENT_VERTICALS, AgentType, TherapyDomain
from app.services.agent_seed_data import (
    COUNSELLING_RESOURCES,
    SCREENING_PROTOCOLS,
    SERVICES,
    THERAPY_GUIDELINES,
)
from app.services.knowledge_base import tokenize


class TestRegistry:
    def test_all_five_assistants_are_registered(self):
        assert len(list_agents()) == 5
        assert set(AGENTS) == set(AgentType)

    def test_lookup_by_id_works(self):
        spec = get_agent("scheduling")
        assert spec is not None
        assert spec.agent_type == AgentType.SCHEDULING

    def test_unknown_id_returns_none(self):
        assert get_agent("radiology") is None
        assert get_agent("") is None

    def test_every_declared_tool_exists(self):
        for spec in list_agents():
            for name in spec.tool_names:
                assert name in TOOLS, f"{spec.id} declares missing tool {name}"

    def test_every_assistant_has_tools_and_prompts(self):
        for spec in list_agents():
            assert spec.tool_names, f"{spec.id} has no tools"
            assert spec.sample_prompts, f"{spec.id} has no sample prompts"
            assert spec.routing_keywords, f"{spec.id} has no routing keywords"

    def test_fallback_tool_is_permitted_for_that_assistant(self):
        for spec in list_agents():
            if spec.fallback_tool:
                assert spec.fallback_tool in spec.tool_names

    def test_every_assistant_can_escalate(self):
        for spec in list_agents():
            assert "escalate_to_staff" in spec.tool_names

    def test_verticals_match_the_escalation_routing_map(self):
        for spec in list_agents():
            assert spec.vertical == AGENT_VERTICALS[spec.agent_type]

    def test_tools_for_returns_definitions(self):
        spec = get_agent("scheduling")
        names = {t.name for t in tools_for(spec)}
        assert "book_appointment" in names

    def test_only_scheduling_can_write_bookings(self):
        for spec in list_agents():
            if spec.agent_type is not AgentType.SCHEDULING:
                assert "book_appointment" not in spec.tool_names

    def test_tool_schemas_are_well_formed(self):
        for name, tool in TOOLS.items():
            schema = tool.input_schema
            assert schema["type"] == "object", f"{name} schema is not an object"
            assert "properties" in schema, f"{name} schema has no properties"
            for required in schema.get("required", []):
                assert required in schema["properties"], f"{name} requires undeclared {required}"

    def test_system_prompt_carries_shared_guardrails(self):
        for spec in list_agents():
            prompt = spec.system_prompt()
            assert "Never diagnose" in prompt
            assert "NIEPMD" in prompt
            assert spec.instructions.strip()[:40] in prompt


class TestKeywordRouting:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("I want to book an appointment for next week", AgentType.SCHEDULING),
            ("Please cancel my appointment", AgentType.SCHEDULING),
            ("What are your working hours and fees?", AgentType.ENQUIRY),
            ("Where are you located and what documents do I bring?", AgentType.ENQUIRY),
            ("My newborn was referred after hearing screening", AgentType.SCREENING),
            ("What is an OAE test?", AgentType.SCREENING),
            ("My child stammers when he talks", AgentType.SLP_GUIDANCE),
            ("She cannot pronounce many sounds", AgentType.SLP_GUIDANCE),
            ("I feel guilty and scared about the diagnosis", AgentType.COUNSELLING),
            ("I am overwhelmed and cannot cope", AgentType.COUNSELLING),
        ],
    )
    def test_representative_messages_route_correctly(self, message, expected):
        assert route_by_keywords(message).agent_type == expected

    def test_unmatched_message_falls_back_to_default(self):
        decision = route_by_keywords("hello there")
        assert decision.agent_type == DEFAULT_AGENT
        assert decision.method == "default"
        assert decision.confidence == 0.0

    def test_confidence_is_bounded(self):
        decision = route_by_keywords(
            "book appointment slot schedule reschedule cancel available tomorrow"
        )
        assert 0.0 <= decision.confidence <= 1.0

    def test_stronger_signal_yields_higher_confidence(self):
        weak = route_by_keywords("appointment")
        strong = route_by_keywords("I want to book an appointment slot and reschedule another")
        assert strong.confidence >= weak.confidence

    def test_scores_cover_every_assistant(self):
        scores = score_agents("book an appointment")
        assert set(scores) == set(AgentType)

    def test_multiword_keyword_matches_as_phrase(self):
        assert score_agents("can I come next week")[AgentType.SCHEDULING] > 0

    def test_empty_message_is_handled(self):
        decision = route_by_keywords("")
        assert decision.agent_type == DEFAULT_AGENT


class TestRouteMessage:
    async def test_confident_keyword_route_skips_the_llm(self):
        # Many scheduling keywords => confident, so no API key is needed.
        decision = await route_message("book an appointment slot to reschedule tomorrow")
        assert decision.agent_type == AgentType.SCHEDULING
        assert decision.method == "keyword"

    async def test_falls_back_to_keywords_without_an_api_key(self):
        decision = await route_message("hello")
        assert decision.agent_type == DEFAULT_AGENT


class TestFallbackArgumentInference:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("my newborn baby", "newborn"),
            ("my 4 month old", "newborn"),
            ("my 18 months old child", "infant_toddler"),
            ("my toddler is not talking", "infant_toddler"),
            ("my 3 year old", "preschool"),
            ("preschool child", "preschool"),
            ("my 8 year old", "school_age"),
            ("he struggles in the classroom", "school_age"),
        ],
    )
    def test_age_band_is_inferred(self, message, expected):
        assert _guess_age_band(message, set(tokenize(message))) == expected

    def test_age_band_is_none_when_absent(self):
        message = "what are your fees"
        assert _guess_age_band(message, set(tokenize(message))) is None

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("18 months", 1.5),
            ("6-month-old", 0.5),
            ("3 years", 3.0),
            ("5 yr", 5.0),
        ],
    )
    def test_age_expressions_are_parsed(self, message, expected):
        assert _first_age_in_years(message) == pytest.approx(expected)

    def test_unparseable_age_returns_none(self):
        assert _first_age_in_years("no numbers here") is None

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("he stutters a lot", TherapyDomain.FLUENCY.value),
            ("choking while feeding", TherapyDomain.FEEDING_SWALLOWING.value),
            ("her voice is hoarse", TherapyDomain.VOICE.value),
            ("cannot pronounce r", TherapyDomain.ARTICULATION.value),
            ("uses a cochlear implant", TherapyDomain.AUDITORY_VERBAL.value),
            ("only says a few words", TherapyDomain.LANGUAGE_DELAY.value),
        ],
    )
    def test_therapy_domain_is_inferred(self, message, expected):
        assert _guess_therapy_domain(set(tokenize(message))) == expected

    def test_therapy_domain_is_none_when_unrelated(self):
        assert _guess_therapy_domain(set(tokenize("what are your timings"))) is None

    def test_knowledge_search_passes_the_raw_question(self):
        args = _infer_fallback_args("search_knowledge_base", "what are your fees")
        assert args["query"] == "what are your fees"

    def test_screening_fallback_extracts_age_band(self):
        args = _infer_fallback_args("get_screening_protocol", "my 3 year old needs a test")
        assert args == {"age_band": "preschool"}

    def test_therapy_fallback_extracts_domain_and_band(self):
        args = _infer_fallback_args("get_therapy_guideline", "my 4 year old stutters")
        assert args["domain"] == TherapyDomain.FLUENCY.value
        assert args["age_band"] == "preschool"

    def test_tool_without_inference_gets_empty_args(self):
        assert _infer_fallback_args("list_therapy_domains", "anything") == {}


class TestSeedContentIntegrity:
    def test_service_codes_are_unique(self):
        codes = [s["code"] for s in SERVICES]
        assert len(codes) == len(set(codes))

    def test_every_age_band_has_a_screening_protocol(self):
        bands = {p["age_band"] for p in SCREENING_PROTOCOLS}
        assert bands == {"newborn", "infant_toddler", "preschool", "school_age"}

    def test_protocols_declare_tests_and_criteria(self):
        for protocol in SCREENING_PROTOCOLS:
            assert protocol["test_codes"], f"{protocol['age_band']} lists no tests"
            assert protocol["referral_criteria"], f"{protocol['age_band']} lists no criteria"
            assert protocol["timeline"].strip()

    def test_every_therapy_domain_is_covered(self):
        covered = {g["domain"] for g in THERAPY_GUIDELINES}
        assert covered == {d.value for d in TherapyDomain}

    def test_guidelines_are_unique_per_domain_and_band(self):
        keys = [(g["domain"], g.get("age_band")) for g in THERAPY_GUIDELINES]
        assert len(keys) == len(set(keys))

    def test_guidelines_carry_activities_and_red_flags(self):
        for guideline in THERAPY_GUIDELINES:
            assert guideline["home_activities"], f"{guideline['title']} has no activities"
            assert guideline["red_flags"], f"{guideline['title']} has no red flags"

    def test_counselling_slugs_are_unique(self):
        slugs = [r["slug"] for r in COUNSELLING_RESOURCES]
        assert len(slugs) == len(set(slugs))

    def test_counselling_resources_carry_next_steps(self):
        for resource in COUNSELLING_RESOURCES:
            assert resource["talking_points"], f"{resource['slug']} has no talking points"
            assert resource["next_steps"], f"{resource['slug']} has no next steps"
