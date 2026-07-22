"""
HearConnect AI — FastAPI backend
Provides the chat engine and all domain data endpoints.
"""

from __future__ import annotations

import os
import re
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("hearconnect")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="HearConnect AI API",
    description="Chatbot engine and domain data for the HearConnect hearing-care platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS  (tighten ALLOWED_ORIGINS in production via env var)
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Request-timing middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ===========================================================================
# CHAT DATA  (mirrors chatData.ts)
# ===========================================================================

class ChatRule:
    """A single keyword-to-response mapping."""
    def __init__(
        self,
        keywords: list[str],
        response: str,
        followups: Optional[list[str]] = None,
    ):
        self.keywords = keywords
        self.response = response
        self.followups = followups or []


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
        keywords=["muffled", "can't hear", "cannot hear", "hearing loss", "asking repeat", "repeat"],
        response=(
            "Difficulty hearing or asking others to repeat may indicate hearing loss. A Pure Tone "
            "Audiometry (PTA) test is the first step to measure your hearing thresholds accurately."
        ),
        followups=["What is PTA?", "Book hearing test"],
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
        keywords=["speech", "delay", "talking", "talk", "language"],
        response=(
            "Delayed speech can be related to hearing difficulties. We recommend a combined hearing "
            "and speech-language assessment to identify the cause and start early intervention."
        ),
        followups=["Speech therapy options", "Book speech assessment"],
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
            "Hello! I'm HearConnect AI. I can help you understand hearing-related concerns and "
            "suggest next steps. Could you describe the problem you or your child are experiencing?"
        ),
        followups=["Hearing difficulty", "Ringing in ears", "Child hearing concern"],
    ),
]

DEFAULT_RESPONSE = ChatRule(
    keywords=[],
    response=(
        "Thanks for sharing that. Based on what you've described, I recommend booking a professional "
        "hearing assessment. Could you tell me a bit more about when the symptoms started and which "
        "ear is affected?"
    ),
    followups=["Book an assessment", "Talk to an audiologist"],
)


def find_response(text: str) -> ChatRule:
    """Return the first matching rule, or the default."""
    lowered = text.lower()
    for rule in CHAT_RULES:
        if any(k in lowered for k in rule.keywords):
            return rule
    return DEFAULT_RESPONSE


# ===========================================================================
# PYDANTIC SCHEMAS
# ===========================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message text")


class ChatResponse(BaseModel):
    response: str
    followups: list[str]
    matched_keywords: list[str]


class HearingProblem(BaseModel):
    id: str
    title: str
    accent: str
    symptoms: list[str]
    route: str


class AdultSection(BaseModel):
    id: str
    title: str
    accent: str
    questions: list[str]
    tests: list[str]


class SpecialTest(BaseModel):
    code: str
    name: str
    description: str


class ChildCategory(BaseModel):
    id: str
    title: str
    ageRange: str
    accent: str
    questions: list[str]
    tests: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float


# ===========================================================================
# DOMAIN DATA  (mirrors hearingData.ts + childData.ts — icon field omitted,
#               icons live in the frontend)
# ===========================================================================

HEARING_PROBLEMS: list[dict] = [
    {"id": "hearing-difficulty", "title": "Hearing Difficulty", "accent": "blue",
     "symptoms": ["Cannot hear properly", "Muffled sounds", "Asking people to repeat"],
     "route": "/adult-care#hearing-difficulty"},
    {"id": "tinnitus", "title": "Ringing in Ears (Tinnitus)", "accent": "purple",
     "symptoms": ["Ringing", "Buzzing", "Hissing"], "route": "/adult-care#tinnitus"},
    {"id": "dizziness", "title": "Dizziness / Balance", "accent": "green",
     "symptoms": ["Feeling dizzy", "Room spinning", "Difficulty walking"],
     "route": "/adult-care#balance-problems"},
    {"id": "ear-pain", "title": "Ear Pain / Discharge", "accent": "blue",
     "symptoms": ["Ear pain", "Fluid", "Infection"], "route": "/adult-care#ear-pain"},
    {"id": "child-concerns", "title": "Child Hearing Concerns", "accent": "purple",
     "symptoms": ["Delayed speech", "Doesn't respond to sounds", "Frequent ear infections"],
     "route": "/child-care"},
]

ADULT_SECTIONS: list[dict] = [
    {"id": "hearing-difficulty", "title": "Hearing Difficulty", "accent": "blue",
     "questions": ["When did it start?", "One ear or both?", "Sudden or gradual?",
                   "Noise exposure?", "Previous ear problems?"],
     "tests": ["PTA", "Speech Audiometry", "Tympanometry", "OAE", "SPIN"]},
    {"id": "tinnitus", "title": "Ringing in Ear", "accent": "purple",
     "questions": ["Which ear?", "Constant?", "Sleeping difficulty?", "Stress?"],
     "tests": ["PTA", "Tinnitus Assessment", "OAE", "SPIN"]},
    {"id": "hyperacusis", "title": "Hyperacusis", "accent": "green",
     "questions": ["Sensitive to sounds?", "Pain?", "Avoid loud places?"],
     "tests": ["LDL", "Audiometry", "Tympanometry", "SPIN"]},
    {"id": "balance-problems", "title": "Balance Problems", "accent": "blue",
     "questions": ["Spinning sensation?", "Vomiting?", "Walking issues?"],
     "tests": ["VEMP", "VNG", "PTA", "SPIN"]},
    {"id": "ear-pain", "title": "Ear Pain", "accent": "purple",
     "questions": ["Pain?", "Discharge?", "Fever?", "Recent infection?"],
     "tests": ["ENT Evaluation", "Tympanometry", "OAE"]},
    {"id": "other-hearing-problems", "title": "Other Hearing Problems", "accent": "green",
     "questions": ["Ear blockage?", "Speech understanding?", "Previous surgery?"],
     "tests": ["PTA", "Speech Audiometry", "Tympanometry"]},
]

SPECIAL_TESTS: list[dict] = [
    {"code": "ABR",  "name": "Auditory Brainstem Response",
     "description": "Measures hearing nerve and brain pathway responses."},
    {"code": "MLR",  "name": "Middle Latency Response",
     "description": "Evaluates middle-latency auditory evoked potentials."},
    {"code": "LLR",  "name": "Late Latency Response",
     "description": "Assesses cortical auditory processing."},
    {"code": "P300", "name": "Cognitive Evoked Potential",
     "description": "Detects attention and cognitive hearing processing."},
    {"code": "P500", "name": "P500 Response",
     "description": "Evaluates higher-level auditory discrimination."},
    {"code": "SRT",  "name": "Speech Reception Threshold",
     "description": "Lowest level at which speech is understood."},
    {"code": "WRS",  "name": "Word Recognition Score",
     "description": "Tests clarity of word recognition at conversational levels."},
    {"code": "PB Test", "name": "Phonetically Balanced Test",
     "description": "Measures speech discrimination with balanced words."},
    {"code": "SPIN", "name": "Speech in Noise Test",
     "description": "Assesses understanding of speech in background noise."},
]

CHILD_CATEGORIES: list[dict] = [
    {"id": "newborn", "title": "Newborn", "ageRange": "0-6 Months", "accent": "blue",
     "questions": ["NICU stay?", "Responding to sounds?", "Family history?"],
     "tests": ["OAE", "ABR", "BOA", "Tympanometry"]},
    {"id": "infant", "title": "Infant", "ageRange": "6 Months-2.5 Years", "accent": "purple",
     "questions": ["Responds to sounds?", "Delayed speech?", "Ear infections?"],
     "tests": ["VRA", "OAE", "Tympanometry", "ABR"]},
    {"id": "preschool", "title": "Preschool Child", "ageRange": "3-5 Years", "accent": "green",
     "questions": ["Speech delay?", "Instructions?", "Learning concerns?"],
     "tests": ["Play Audiometry", "OAE", "Speech Detection"]},
    {"id": "school-age", "title": "School Age Child", "ageRange": "6+ Years", "accent": "blue",
     "questions": ["Difficulty hearing?", "Academic concerns?"],
     "tests": ["PTA", "Speech Audiometry", "OAE", "Special Tests"]},
]


# ===========================================================================
# STARTUP TIME (for uptime reporting)
# ===========================================================================
_START_TIME = time.time()


# ===========================================================================
# ROUTES
# ===========================================================================

@app.get("/health", response_model=HealthResponse, tags=["Utility"])
def health_check():
    """Liveness probe — returns service status and uptime."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat(body: ChatRequest):
    """
    Accept a user message and return a contextual hearing-care response.

    The engine matches keywords against a curated rule set. If no rule matches
    it returns a generic follow-up prompt encouraging the user to book an assessment.
    """
    logger.info("chat | message_len=%d", len(body.message))
    rule = find_response(body.message)
    matched = [k for k in rule.keywords if k in body.message.lower()]
    return {
        "response": rule.response,
        "followups": rule.followups,
        "matched_keywords": matched,
    }


@app.get("/api/hearing-problems", response_model=list[HearingProblem], tags=["Data"])
def get_hearing_problems():
    """Return all hearing problem categories shown on the Assessment page."""
    return HEARING_PROBLEMS


@app.get("/api/adult-sections", response_model=list[AdultSection], tags=["Data"])
def get_adult_sections():
    """Return all adult care sections shown on the Adult Care page."""
    return ADULT_SECTIONS


@app.get("/api/special-tests", response_model=list[SpecialTest], tags=["Data"])
def get_special_tests():
    """Return the list of special audiological tests."""
    return SPECIAL_TESTS


@app.get("/api/child-categories", response_model=list[ChildCategory], tags=["Data"])
def get_child_categories():
    """Return all paediatric hearing assessment categories."""
    return CHILD_CATEGORIES


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
