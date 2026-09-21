"""
Public AI assistant chat for the /ai-assistant page.

Uses RAG (Qdrant + local embeddings + Ollama) when a corpus is available.
Falls back to curated keyword rules when retrieval or the model is unavailable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config import get_settings
from app.services.ai.llm import generate_text
from app.services.ai.prompt_templates import (
    ASSISTANT_RAG_SYSTEM_PROMPT,
    build_assistant_chat_prompt,
)
from app.services.ai.rag_pipeline import retrieve_for_message
from app.services.ai.vector_store import RetrievedChunk

logger = logging.getLogger("nipmed.assistant_chat")

SYSTEM_PROMPT = """You are the NIEPMD Audiology and Speech Department assistant.
Help patients and families with hearing, speech, language, voice, tinnitus,
balance, and related concerns.

Rules:
- Be clear, calm, and practical. Use short paragraphs.
- Do not diagnose or prescribe medication.
- Suggest appropriate assessments or when to see an audiologist / ENT / SLP.
- Mention Take Test or booking an assessment when it helps.
- If the message is a greeting, welcome them and ask what concern they have.
- Keep answers under 180 words.
- Do not invent hospital policies, prices, or wait times you were not given.
"""


@dataclass
class ChatRule:
    keywords: list[str]
    response: str
    followups: list[str] = field(default_factory=list)


CHAT_RULES: list[ChatRule] = [
    ChatRule(
        keywords=["child", "kid", "baby", "son", "daughter", "infant"],
        response=(
            "This could indicate hearing loss in your child. We recommend scheduling a hearing "
            "assessment with a paediatric audiologist. Early detection greatly improves speech "
            "and language development outcomes."
        ),
        followups=["Book a child assessment", "Learn about OAE test", "Speech delay concerns"],
    ),
    ChatRule(
        keywords=["not responding", "respond", "no response", "doesn't respond", "ignore"],
        response=(
            "Not responding to sounds is an important early sign. If this happens repeatedly, "
            "a hearing screening (OAE / ABR) is strongly recommended to rule out hearing loss."
        ),
        followups=["What is OAE?", "What is ABR?", "Schedule screening"],
    ),
    ChatRule(
        keywords=["ringing", "buzzing", "hissing", "tinnitus"],
        response=(
            "Ringing or buzzing in the ears is called tinnitus. It is often linked to noise "
            "exposure, stress, or inner-ear changes. An audiologist can assess severity and "
            "suggest management strategies."
        ),
        followups=["Tinnitus management tips", "Book tinnitus assessment"],
    ),
    ChatRule(
        keywords=["dizzy", "dizziness", "vertigo", "spinning", "balance", "walking"],
        response=(
            "Dizziness and balance issues may relate to the inner ear. Tests such as VNG and VEMP "
            "help evaluate vestibular function. Please consult an ENT specialist if symptoms are "
            "severe or sudden."
        ),
        followups=["What is VNG?", "Balance assessment"],
    ),
    ChatRule(
        keywords=["pain", "ear pain", "ache", "discharge", "fluid", "infection"],
        response=(
            "Ear pain with discharge often signals an ear infection. Keep the ear dry and see an "
            "ENT specialist promptly. Tympanometry can confirm whether fluid is present behind the "
            "eardrum."
        ),
        followups=["Find ENT specialist", "What is tympanometry?"],
    ),
    ChatRule(
        keywords=["muffled", "can't hear", "cannot hear", "hearing loss", "asking repeat", "repeat", "hearing difficulty"],
        response=(
            "Difficulty hearing or asking others to repeat may indicate hearing loss. A Pure Tone "
            "Audiometry (PTA) test is the first step to measure your hearing thresholds accurately."
        ),
        followups=["What is PTA?", "Book hearing test", "Take Test"],
    ),
    ChatRule(
        keywords=["hearing aid", "aid", "device", "amplification"],
        response=(
            "Hearing aids can significantly improve quality of life. An audiologist will recommend "
            "the right type based on your hearing loss severity, lifestyle, and budget."
        ),
        followups=["Types of hearing aids", "Hearing aid maintenance"],
    ),
    ChatRule(
        keywords=["cochlear", "implant"],
        response=(
            "Cochlear implants are an option for severe to profound hearing loss where hearing aids "
            "provide limited benefit. A thorough evaluation by a cochlear implant team is required."
        ),
        followups=["Cochlear implant evaluation", "Candidacy criteria"],
    ),
    ChatRule(
        keywords=["speech", "delay", "talking", "talk", "language", "stutter", "voice", "swallow"],
        response=(
            "Speech, language, voice or swallowing concerns can be related to hearing or need a "
            "speech-language assessment. We recommend a combined hearing and speech-language "
            "evaluation to identify the cause and start early support."
        ),
        followups=["Speech therapy options", "Book speech assessment", "Take Test"],
    ),
    ChatRule(
        keywords=["noise", "loud", "concert", "workplace", "earmuffs", "earplugs"],
        response=(
            "Noise exposure is a leading cause of preventable hearing loss. Always use ear "
            "protection in loud environments and limit listening volumes to safe levels (below 80 dB)."
        ),
        followups=["Hearing protection tips", "Safe listening levels"],
    ),
    ChatRule(
        keywords=["newborn", "0-6", "nicu", "screening"],
        response=(
            "Newborn hearing screening is recommended within the first month. OAE and ABR are "
            "painless tests done while the baby sleeps. Early screening enables timely intervention."
        ),
        followups=["Newborn screening details", "What is ABR?"],
    ),
    ChatRule(
        keywords=["school", "academic", "class", "teacher", "grades"],
        response=(
            "Hearing issues can affect academic performance. A school-age hearing test "
            "(PTA + Speech Audiometry) can identify whether hearing is contributing to learning "
            "difficulties."
        ),
        followups=["School-age assessment", "Classroom strategies"],
    ),
    ChatRule(
        keywords=["sleep", "insomnia", "tinnitus sleep"],
        response=(
            "Tinnitus can disturb sleep. Sound therapy, relaxation techniques, and quiet background "
            "noise at bedtime often help. Please discuss persistent sleep issues with your audiologist."
        ),
        followups=["Tinnitus management", "Sound therapy"],
    ),
    ChatRule(
        keywords=["stress", "anxiety", "worried", "depressed"],
        response=(
            "Stress can worsen tinnitus and perceived hearing difficulties. Counselling, mindfulness, "
            "and hearing therapy together can provide meaningful relief."
        ),
        followups=["Counselling services", "Stress reduction tips"],
    ),
    ChatRule(
        keywords=["blockage", "blocked", "wax", "earwax", "plugged"],
        response=(
            "A blocked sensation is often caused by earwax build-up. Avoid inserting cotton buds — "
            "an ENT or audiologist can safely remove wax and check the eardrum."
        ),
        followups=["Safe ear care", "Book ear cleaning"],
    ),
    ChatRule(
        keywords=["surgery", "operation", "mastoid", "tube", "grommet"],
        response=(
            "If you have had previous ear surgery, share the details with your audiologist. It "
            "affects which tests are suitable and the interpretation of your results."
        ),
        followups=["Pre-surgery hearing test", "Post-surgery follow-up"],
    ),
    ChatRule(
        keywords=["fever", "temperature", "sick"],
        response=(
            "Fever alongside ear symptoms may indicate an active infection. Please consult a doctor "
            "promptly, especially in young children, to prevent complications."
        ),
        followups=["Find ENT specialist", "When to seek urgent care"],
    ),
    ChatRule(
        keywords=["family", "history", "genetic", "hereditary"],
        response=(
            "A family history of hearing loss increases risk. A baseline hearing test is recommended, "
            "and periodic monitoring helps detect changes early."
        ),
        followups=["Book baseline test", "Genetic counselling"],
    ),
    ChatRule(
        keywords=["hyperacusis", "sensitive", "too loud", "painful sound"],
        response=(
            "Hyperacusis is increased sensitivity to everyday sounds. Sound therapy and gradual "
            "exposure under an audiologist can help desensitise and improve comfort."
        ),
        followups=["What is LDL test?", "Hyperacusis management"],
    ),
    ChatRule(
        keywords=["hello", "hi", "hey", "start", "help"],
        response=(
            "Hello! I'm the NIEPMD Audiology and Speech assistant. I can help you understand "
            "hearing and speech-related concerns and suggest next steps. Could you describe the "
            "problem you or your child are experiencing?"
        ),
        followups=["Hearing difficulty", "Ringing in ears", "Child hearing concern"],
    ),
]

DEFAULT_RESPONSE = ChatRule(
    keywords=[],
    response=(
        "Thanks for sharing that. Based on what you've described, I recommend booking a professional "
        "hearing or speech assessment. You can also start a guided Take Test for personalised next steps."
    ),
    followups=["Take Test", "Talk to an audiologist"],
)


def find_response(text: str) -> ChatRule:
    lowered = text.lower()
    for rule in CHAT_RULES:
        if any(k in lowered for k in rule.keywords):
            return rule
    return DEFAULT_RESPONSE


def match_keywords(text: str, rule: ChatRule) -> list[str]:
    lowered = text.lower()
    return [k for k in rule.keywords if k in lowered]


def _format_rag_extract_fallback(chunks: list[RetrievedChunk]) -> str:
    """Plain answer from retrieved extracts when the LLM is unavailable."""
    parts = [
        "Here is what the department's guidance says:",
        "",
    ]
    for index, chunk in enumerate(chunks[:3], start=1):
        body = " ".join(chunk.text.split())
        if len(body) > 900:
            body = body[:897].rstrip() + "…"
        parts.append(f"From “{chunk.title}” ({index}):")
        parts.append(body)
        parts.append("")
    parts.append(
        "This information is for education only and is not a diagnosis. "
        "Please consult a qualified audiologist or doctor for personal advice."
    )
    return "\n".join(parts).strip()


def answer_message(message: str) -> dict[str, object]:
    """Synchronous keyword-only answer (tests / fallbacks)."""
    rule = find_response(message)
    return {
        "response": rule.response,
        "followups": rule.followups,
        "matched_keywords": match_keywords(message, rule),
        "source": "keyword",
    }


async def answer_message_async(message: str) -> dict[str, object]:
    """
    RAG-first assistant: retrieve departmental documents, generate with Ollama,
    then degrade to extract text or keyword rules.
    """
    rule = find_response(message)
    followups = rule.followups or DEFAULT_RESPONSE.followups
    matched = match_keywords(message, rule)
    settings = get_settings()

    chunks = await retrieve_for_message(message)

    if chunks:
        if settings.llm_enabled:
            user_prompt = build_assistant_chat_prompt(message, chunks)
            text = await generate_text(
                ASSISTANT_RAG_SYSTEM_PROMPT,
                user_prompt,
                max_tokens=450,
            )
            if text:
                logger.info(
                    "Public assistant RAG reply via %s (%s chunks)",
                    settings.active_llm_provider,
                    len(chunks),
                )
                return {
                    "response": text,
                    "followups": followups,
                    "matched_keywords": matched,
                    "source": "rag",
                }

        logger.info("RAG chunks found but LLM unavailable — using extract fallback")
        return {
            "response": _format_rag_extract_fallback(chunks),
            "followups": followups,
            "matched_keywords": matched,
            "source": "rag_extract",
        }

    logger.warning("No RAG chunks — using keyword fallback")
    return {
        "response": rule.response,
        "followups": followups,
        "matched_keywords": matched,
        "source": "keyword",
    }
