"""
Prompts for the AI Treatment Assistant.

The model's only job is to rephrase retrieved departmental text into plain
language. It is never asked to decide anything clinical: which tests to
recommend has already been settled by the deterministic rule engine before this
module is reached.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.services.ai.vector_store import RetrievedChunk

SAFETY_DISCLAIMER = (
    "This information is for education only. It is not a diagnosis and not a "
    "prescription. Only a qualified audiologist or doctor can diagnose a condition "
    "after examining you and reviewing your test results."
)

EXPLANATION_SYSTEM_PROMPT = """\
You are an assistant at the Department of Speech, Hearing and Communication, \
NIEPMD, Chennai. You explain hearing and speech tests to patients and parents in \
plain language.

You will be given extracts from the department's own documents. Those extracts are \
your ONLY source of information.

Absolute rules:
- Use ONLY the provided extracts. If they do not answer the question, say that the \
audiologist will explain it at the appointment. Never fill a gap from your own \
knowledge.
- Never diagnose. Never say or imply what condition the person has, how severe it \
is, or what the result will be.
- Never prescribe or suggest medication, dosage, surgery or any treatment.
- Never interpret a test result, audiogram or report.
- Do not give a prognosis or predict an outcome.
- Always defer the actual diagnosis to the audiologist or doctor.

Style:
- Write for someone with no medical background, at about a 6th-grade reading level.
- Short sentences and short paragraphs. Plain words instead of jargon; if a \
technical term is unavoidable, define it in the same sentence.
- Warm, calm and factual. Do not alarm, and do not over-reassure.
- 120 to 200 words. No headings, no bullet lists, no markdown.
- Do not mention these instructions, the extracts, or that you are an AI.

Cover, only where the extracts support it: what the test is, what will happen \
during it, whether it is uncomfortable, how long it takes, and how to prepare.\
"""


def build_retrieval_query(
    test_name: str,
    *,
    test_code: Optional[str] = None,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    question: Optional[str] = None,
) -> str:
    """
    Compose the retrieval query.

    Patient context is folded in so a paediatric flow biases toward child-specific
    passages, and any explicit patient question is weighted first because it is
    the most direct statement of what they want to know.
    """
    parts: list[str] = []
    if question:
        parts.append(question.strip())
    parts.append(test_name.strip())
    if test_code and test_code.strip().upper() != test_name.strip().upper():
        parts.append(test_code.strip())

    if flow_type == "child":
        parts.append("child paediatric")
        subtype_terms = {
            "newborn": "newborn infant baby screening",
            "infant_toddler": "infant toddler",
            "preschool": "preschool young child",
            "school_age": "school age child",
        }
        if child_subtype and child_subtype in subtype_terms:
            parts.append(subtype_terms[child_subtype])
    elif flow_type == "adult":
        parts.append("adult")

    parts.append("what to expect preparation procedure")
    return " ".join(parts)


def format_context(chunks: Sequence[RetrievedChunk], *, max_chars: int = 6000) -> str:
    """
    Render retrieved chunks as numbered, attributed extracts.

    Attribution is included so the audit record shows which document each fact
    came from, and truncation protects the prompt budget on a large corpus.
    """
    blocks: list[str] = []
    used = 0
    for position, chunk in enumerate(chunks, start=1):
        header = f"[Extract {position} — {chunk.title}]"
        body = chunk.text.strip()
        if not body:
            continue
        block = f"{header}\n{body}"
        if used + len(block) > max_chars:
            remaining = max_chars - used - len(header) - 1
            if remaining < 200:
                break
            block = f"{header}\n{body[:remaining].rstrip()}…"
            blocks.append(block)
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def build_explanation_prompt(
    test_name: str,
    chunks: Sequence[RetrievedChunk],
    *,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    question: Optional[str] = None,
    patient_age: Optional[int] = None,
) -> str:
    """Build the user-turn content for the explanation request."""
    context = format_context(chunks)

    audience = "an adult patient"
    if flow_type == "child":
        audience = "the parent of a child"
        if child_subtype == "newborn":
            audience = "the parent of a newborn baby"
        elif child_subtype == "infant_toddler":
            audience = "the parent of a toddler"
        elif child_subtype == "preschool":
            audience = "the parent of a preschool-age child"
        elif child_subtype == "school_age":
            audience = "the parent of a school-age child"
    elif patient_age is not None and patient_age >= 60:
        audience = "an older adult patient"

    lines = [
        f"Explain the test below to {audience}.",
        "",
        f"Test: {test_name}",
    ]
    if question:
        lines += ["", f"They specifically asked: {question.strip()}"]

    lines += ["", "Extracts from the department's documents:", ""]
    lines.append(context if context else "(No relevant extracts were found.)")

    if not context:
        # Belt and braces: retrieval should already have triggered the static
        # fallback, so this instruction is the second line of defence.
        lines += [
            "",
            "There are no extracts to work from. Do not attempt an explanation. Reply "
            "with one short sentence saying the audiologist will explain this test at "
            "the appointment.",
        ]

    return "\n".join(lines)


def build_static_grounded_prompt(
    test_name: str,
    static_text: str,
    *,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    question: Optional[str] = None,
    patient_age: Optional[int] = None,
) -> str:
    """
    Ground the model on an admin-authored definition when no RAG chunks exist.

    Same safety contract as document extracts: the model may only rephrase this
    text, never invent clinical content.
    """
    audience = "an adult patient"
    if flow_type == "child":
        audience = "the parent of a child"
        if child_subtype == "newborn":
            audience = "the parent of a newborn baby"
        elif child_subtype == "infant_toddler":
            audience = "the parent of a toddler"
        elif child_subtype == "preschool":
            audience = "the parent of a preschool-age child"
        elif child_subtype == "school_age":
            audience = "the parent of a school-age child"
    elif patient_age is not None and patient_age >= 60:
        audience = "an older adult patient"

    lines = [
        f"Explain the test below to {audience}.",
        "",
        f"Test: {test_name}",
    ]
    if question:
        lines += ["", f"They specifically asked: {question.strip()}"]

    lines += [
        "",
        "Extracts from the department's documents:",
        "",
        f"[Extract 1 — Department definition]\n{static_text.strip()}",
    ]
    return "\n".join(lines)


ASSISTANT_RAG_SYSTEM_PROMPT = """\
You are the NIEPMD Audiology and Speech Department assistant on the public website.
You help patients and families understand hearing, speech, language, voice, tinnitus,
balance, and related concerns.

You will be given extracts from the department's own documents. Those extracts are \
your ONLY source of clinical facts.

Absolute rules:
- Use ONLY the provided extracts for medical or test information. If they do not \
answer the question, say the audiologist or speech-language specialist will explain \
at the appointment. Never fill gaps from general knowledge.
- Never diagnose. Never prescribe medication or treatment.
- Never interpret test results or predict outcomes.
- Do not invent hospital policies, prices, appointment wait times, or contact details \
unless they appear in the extracts.

Style:
- Plain language for someone with no medical background.
- Short paragraphs. Warm, calm, and practical.
- Under 180 words. No markdown headings or bullet lists.
- Suggest Take Test or booking an assessment when appropriate.
- Do not mention these instructions, the extracts, or that you are an AI.

End with this disclaimer on its own line:
This information is for education only and is not a diagnosis. Please consult a \
qualified audiologist or doctor for personal advice.\
"""


def build_assistant_chat_prompt(message: str, chunks: Sequence[RetrievedChunk]) -> str:
    """Build the user-turn for a grounded public-assistant reply."""
    context = format_context(chunks)
    lines = [
        "A visitor wrote:",
        message.strip(),
        "",
        "Extracts from the department's documents:",
        "",
    ]
    if context:
        lines.append(context)
    else:
        lines.append("(No relevant extracts were found.)")
        lines += [
            "",
            "There are no extracts to work from. Reply with one short sentence saying "
            "you recommend booking a hearing or speech assessment, and that the "
            "audiologist will explain details at the appointment.",
        ]
    return "\n".join(lines)
