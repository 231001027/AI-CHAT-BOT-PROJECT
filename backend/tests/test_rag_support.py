"""Unit tests for chunking, prompt construction and report assembly."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.ai.chunking import (
    UnsupportedDocumentError,
    chunk_text,
    extract_text,
    normalise_whitespace,
)
from app.services.ai.prompt_templates import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt,
    build_retrieval_query,
    format_context,
)
from app.services.ai.vector_store import RetrievedChunk
from app.services.report_service import (
    SAFETY_DISCLAIMER,
    build_report_json,
    report_filename,
)


def _chunk(text: str, title: str = "Audiology SOP", index: int = 0, score: float = 0.8):
    return RetrievedChunk(
        document_id="doc-1", title=title, chunk_index=index, text=text, score=score
    )


class TestNormaliseWhitespace:
    def test_collapses_spaces_and_tabs(self):
        assert normalise_whitespace("a    b\t\tc") == "a b c"

    def test_preserves_paragraph_breaks(self):
        assert normalise_whitespace("one\n\ntwo") == "one\n\ntwo"

    def test_squashes_excess_blank_lines(self):
        assert normalise_whitespace("one\n\n\n\n\ntwo") == "one\n\ntwo"

    def test_handles_empty_input(self):
        assert normalise_whitespace("") == ""
        assert normalise_whitespace(None) == ""


class TestChunkText:
    def test_empty_text_yields_no_chunks(self):
        assert chunk_text("") == []
        assert chunk_text("   \n\n  ") == []

    def test_short_text_is_a_single_chunk(self):
        chunks = chunk_text("A short paragraph about the OAE test.", chunk_size=2000)
        assert len(chunks) == 1
        assert "OAE" in chunks[0].text

    def test_long_text_splits_into_multiple_chunks(self):
        text = "\n\n".join(f"Paragraph number {i} about hearing tests." * 8 for i in range(30))
        chunks = chunk_text(text, chunk_size=600, overlap=100)
        assert len(chunks) > 1

    def test_chunks_are_indexed_sequentially(self):
        text = "\n\n".join(f"Para {i}. " * 40 for i in range(15))
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_chunks_respect_the_size_budget(self):
        text = "\n\n".join(f"Para {i}. " * 30 for i in range(20))
        chunks = chunk_text(text, chunk_size=800, overlap=100)
        # Allow one paragraph of slack, since a whole block is never split
        # mid-paragraph unless it alone exceeds the budget.
        assert all(len(c.text) <= 800 * 2 for c in chunks)

    def test_oversized_paragraph_is_split(self):
        giant = "This is a sentence about audiometry. " * 200
        chunks = chunk_text(giant, chunk_size=500, overlap=0)
        assert len(chunks) > 1
        assert all(len(c.text) <= 1000 for c in chunks)

    def test_paragraph_with_no_sentence_breaks_is_hard_wrapped(self):
        blob = "x" * 2000
        chunks = chunk_text(blob, chunk_size=400, overlap=0)
        assert len(chunks) > 1

    def test_overlap_carries_context_forward(self):
        paras = [f"Unique marker {i} in this paragraph." for i in range(12)]
        with_overlap = chunk_text("\n\n".join(paras), chunk_size=200, overlap=90)
        without = chunk_text("\n\n".join(paras), chunk_size=200, overlap=0)
        # Overlap repeats trailing content, so it produces at least as many chunks.
        assert len(with_overlap) >= len(without)

    def test_no_chunk_is_empty(self):
        text = "\n\n".join(f"Para {i}." for i in range(50))
        assert all(c.text.strip() for c in chunk_text(text, chunk_size=300, overlap=50))

    def test_overlap_is_clamped_below_chunk_size(self):
        # An overlap larger than the chunk would otherwise loop forever.
        chunks = chunk_text("a\n\nb\n\nc\n\nd", chunk_size=200, overlap=5000)
        assert chunks

    def test_tiny_chunk_size_is_raised_to_a_floor(self):
        assert chunk_text("Some text here about tests.", chunk_size=1)

    def test_result_is_deterministic(self):
        text = "\n\n".join(f"Para {i}. " * 20 for i in range(10))
        first = [c.text for c in chunk_text(text, chunk_size=500, overlap=80)]
        second = [c.text for c in chunk_text(text, chunk_size=500, overlap=80)]
        assert first == second


class TestExtractText:
    def test_reads_a_text_file(self, tmp_path: Path):
        path = tmp_path / "sop.txt"
        path.write_text("The OAE test is quick and painless.", encoding="utf-8")
        assert "OAE" in extract_text(path)

    def test_reads_a_markdown_file(self, tmp_path: Path):
        path = tmp_path / "guide.md"
        path.write_text("# Heading\n\nSome guidance.", encoding="utf-8")
        assert "guidance" in extract_text(path)

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(UnsupportedDocumentError):
            extract_text(tmp_path / "nope.txt")

    def test_unsupported_type_raises(self, tmp_path: Path):
        path = tmp_path / "image.png"
        path.write_bytes(b"\x89PNG")
        with pytest.raises(UnsupportedDocumentError):
            extract_text(path)


class TestRetrievalQuery:
    def test_includes_the_test_name(self):
        assert "Pure Tone Audiometry" in build_retrieval_query("Pure Tone Audiometry")

    def test_patient_question_leads_the_query(self):
        query = build_retrieval_query("OAE", question="Will it hurt my baby?")
        assert query.startswith("Will it hurt my baby?")

    def test_child_flow_adds_paediatric_terms(self):
        query = build_retrieval_query("OAE", flow_type="child", child_subtype="newborn")
        assert "paediatric" in query
        assert "newborn" in query

    def test_adult_flow_adds_adult_term(self):
        assert "adult" in build_retrieval_query("PTA", flow_type="adult")

    def test_code_is_not_duplicated_when_same_as_name(self):
        query = build_retrieval_query("OAE", test_code="OAE")
        assert query.count("OAE") == 1


class TestFormatContext:
    def test_numbers_and_attributes_each_extract(self):
        context = format_context([_chunk("First fact.", "Doc A"), _chunk("Second fact.", "Doc B")])
        assert "[Extract 1 — Doc A]" in context
        assert "[Extract 2 — Doc B]" in context

    def test_empty_input_yields_empty_string(self):
        assert format_context([]) == ""

    def test_blank_chunks_are_skipped(self):
        assert format_context([_chunk("   ")]) == ""

    def test_respects_the_character_budget(self):
        chunks = [_chunk("word " * 500, f"Doc {i}") for i in range(10)]
        assert len(format_context(chunks, max_chars=2000)) <= 2200


class TestExplanationPrompt:
    def test_system_prompt_forbids_diagnosis_and_prescription(self):
        lowered = EXPLANATION_SYSTEM_PROMPT.lower()
        assert "never diagnose" in lowered
        assert "never prescribe" in lowered
        assert "only source" in lowered

    def test_prompt_includes_the_test_and_extracts(self):
        prompt = build_explanation_prompt("OAE", [_chunk("The probe plays soft sounds.")])
        assert "OAE" in prompt
        assert "soft sounds" in prompt

    def test_child_flow_sets_a_parent_audience(self):
        prompt = build_explanation_prompt(
            "OAE", [_chunk("text")], flow_type="child", child_subtype="newborn"
        )
        assert "parent of a newborn" in prompt

    def test_older_adult_audience(self):
        prompt = build_explanation_prompt("PTA", [_chunk("text")], patient_age=72)
        assert "older adult" in prompt

    def test_patient_question_is_surfaced(self):
        prompt = build_explanation_prompt("PTA", [_chunk("text")], question="Is it painful?")
        assert "Is it painful?" in prompt

    def test_no_extracts_instructs_a_refusal(self):
        # Defence in depth: retrieval should already have triggered the fallback.
        prompt = build_explanation_prompt("PTA", [])
        assert "Do not attempt an explanation" in prompt


class TestBuildReportJson:
    @staticmethod
    def _report(**overrides):
        defaults = dict(
            patient={
                "name": "Test Patient",
                "age": 42,
                "gender": "female",
                "district": "Chennai",
                "phone": "9999999999",
                "user_type": "myself",
                "flow_type": "adult",
            },
            category={"name": "Hearing difficulty"},
            condition={"name": "Gradual loss", "description": "Slow decline"},
            answers=[
                {"question_text": "How long?", "answer_label": "1 to 6 months", "answer_value": "4"}
            ],
            recommended_tests=[
                {
                    "test_code": "PTA",
                    "test_name": "Pure Tone Audiometry",
                    "reason_text": "To measure hearing.",
                }
            ],
            general_recommendations=["Avoid loud noise."],
            session_id="abc-123",
        )
        defaults.update(overrides)
        return build_report_json(**defaults)

    def test_includes_institute_metadata(self):
        report = self._report()
        assert "NIEPMD" in report["meta"]["institute"]
        assert report["meta"]["session_id"] == "abc-123"

    def test_carries_patient_details(self):
        assert self._report()["patient"]["name"] == "Test Patient"

    def test_carries_answers_and_tests(self):
        report = self._report()
        assert report["answers"][0]["answer"] == "1 to 6 months"
        assert report["recommended_tests"][0]["test_code"] == "PTA"

    def test_always_includes_the_disclaimer(self):
        assert self._report()["disclaimer"] == SAFETY_DISCLAIMER

    def test_always_includes_the_urgent_notice(self):
        assert "emergency" in self._report()["urgent_notice"].lower()

    def test_embeds_explanations_by_test_code(self):
        report = self._report(explanations={"PTA": "This test measures hearing."})
        assert report["recommended_tests"][0]["explanation"] == "This test measures hearing."

    def test_missing_explanation_is_none(self):
        assert self._report()["recommended_tests"][0]["explanation"] is None

    def test_handles_no_tests(self):
        report = self._report(recommended_tests=[])
        assert report["recommended_tests"] == []
        assert report["disclaimer"]

    def test_handles_missing_category_and_condition(self):
        report = self._report(category=None, condition=None)
        assert report["presenting"]["category"] is None
        assert report["presenting"]["condition"] is None

    def test_answer_falls_back_to_key_when_text_missing(self):
        report = self._report(
            answers=[{"question_key": "duration_months", "answer_value": "4"}]
        )
        assert report["answers"][0]["question"] == "duration_months"


class TestReportFilename:
    def test_includes_a_sanitised_name(self):
        assert report_filename("Test Patient", "abcdef123456").startswith(
            "niepmd_guidance_Test_Patient_"
        )

    def test_strips_unsafe_characters(self):
        name = report_filename("A/B\\C:D*", "abcdef12")
        assert "/" not in name and "\\" not in name and ":" not in name

    def test_ends_with_pdf(self):
        assert report_filename("X", "abcdef12").endswith(".pdf")

    def test_handles_an_empty_name(self):
        assert "patient" in report_filename("   ", "abcdef12")

    def test_truncates_a_very_long_name(self):
        assert len(report_filename("A" * 200, "abcdef12")) < 100
