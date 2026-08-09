"""
Seed data for ConcernConfig + TestCatalog.

Symptom question prompts are EDITABLE PLACEHOLDERS — update wording here
(or via a future admin API) without changing rules-engine logic.
"""

from __future__ import annotations

from typing import Any

# ── Test catalog ──────────────────────────────────────────────────────────────

TEST_CATALOG: list[dict[str, str]] = [
    {"code": "PTA", "name": "Pure Tone Audiometry", "category": "basic",
     "description": "Measures hearing thresholds across frequencies using pure tones."},
    {"code": "Speech Audiometry", "name": "Speech Audiometry", "category": "basic",
     "description": "Assesses ability to hear and understand spoken words."},
    {"code": "Tympanometry", "name": "Tympanometry", "category": "basic",
     "description": "Evaluates middle-ear function and eardrum mobility."},
    {"code": "OAE", "name": "Otoacoustic Emissions", "category": "basic",
     "description": "Checks outer hair cell function in the cochlea."},
    {"code": "SPIN", "name": "Speech in Noise Test", "category": "basic",
     "description": "Assesses understanding of speech in background noise."},
    {"code": "Tinnitus Assessment", "name": "Tinnitus Assessment", "category": "basic",
     "description": "Characterises tinnitus pitch, loudness, and impact."},
    {"code": "LDL", "name": "Loudness Discomfort Level", "category": "basic",
     "description": "Measures the level at which sounds become uncomfortably loud."},
    {"code": "VEMP", "name": "Vestibular Evoked Myogenic Potential", "category": "vestibular",
     "description": "Evaluates otolith and vestibular pathway function."},
    {"code": "VNG", "name": "Videonystagmography", "category": "vestibular",
     "description": "Assesses balance system using eye-movement recordings."},
    {"code": "Posturography", "name": "Posturography", "category": "vestibular",
     "description": "Measures postural stability and balance control."},
    {"code": "Ear Evaluation (ENT)", "name": "Ear Evaluation (ENT)", "category": "basic",
     "description": "Clinical ear examination by an ENT specialist."},
    {"code": "Immittance Test", "name": "Immittance Test", "category": "basic",
     "description": "Battery of middle-ear tests including tympanometry and reflexes."},
    {"code": "ABR", "name": "Auditory Brainstem Response", "category": "special",
     "description": "Measures hearing nerve and brainstem pathway responses."},
    {"code": "MLR", "name": "Middle Latency Response", "category": "special",
     "description": "Evaluates middle-latency auditory evoked potentials."},
    {"code": "LLR", "name": "Late Latency Response", "category": "special",
     "description": "Assesses cortical auditory processing."},
    {"code": "P300", "name": "Cognitive Evoked Potential (P300)", "category": "special",
     "description": "Detects attention and cognitive hearing processing."},
    {"code": "P500", "name": "P500 Response", "category": "special",
     "description": "Evaluates higher-level auditory discrimination."},
    {"code": "SRT", "name": "Speech Reception Threshold", "category": "special",
     "description": "Lowest level at which speech is understood."},
    {"code": "WRS", "name": "Word Recognition Score", "category": "special",
     "description": "Tests clarity of word recognition at conversational levels."},
    {"code": "PB Tests", "name": "Phonetically Balanced Tests", "category": "special",
     "description": "Measures speech discrimination with phonetically balanced words."},
    {"code": "VRA", "name": "Visual Reinforcement Audiometry", "category": "paediatric",
     "description": "Behavioural hearing test for infants using visual rewards."},
    {"code": "BOA", "name": "Behavioural Observation Audiometry", "category": "paediatric",
     "description": "Observes infant responses to sound in a controlled setting."},
    {"code": "ASSR", "name": "Auditory Steady-State Response", "category": "special",
     "description": "Estimates hearing thresholds using steady-state evoked potentials."},
    {"code": "Play Audiometry", "name": "Play Audiometry", "category": "paediatric",
     "description": "Play-based hearing test suited for preschool children."},
    {"code": "Speech Detection Threshold", "name": "Speech Detection Threshold", "category": "paediatric",
     "description": "Lowest level at which speech is detected (not necessarily understood)."},
]

CHILD_OUTCOMES = [
    "Hearing Aid",
    "ENT Referral",
    "Cochlear Implant Evaluation",
    "Auditory Training",
    "Speech Therapy",
    "Parent Counselling",
    "Regular Follow-up",
]


def _signs(*items: tuple[str, str]) -> list[dict[str, str]]:
    return [{"key": k, "prompt": p} for k, p in items]


# ── Concern configs (adult Page 2 + child Page 3) ─────────────────────────────
# NOTE: prompt strings are placeholders — edit freely without touching engine code.

CONCERN_CONFIGS: list[dict[str, Any]] = [
    {
        "concern_type": "hearing_difficulty",
        "age_band": None,
        "common_signs": _signs(
            ("onset", "When did it start?"),
            ("laterality", "Both ears or one ear?"),
            ("sudden", "Sudden or gradual?"),
            ("noise_exposure", "Any noise exposure?"),
            ("previous_ear", "Previous ear problem?"),
        ),
        "recommended_tests": ["PTA", "Speech Audiometry", "Tympanometry", "OAE", "SPIN"],
        "what_it_helps": "Checks how well you hear and the type of hearing loss.",
        "outcome_options": None,
        "conditional_rules": [
            {
                "when": {"question_key": "sudden", "answer_contains": "sudden"},
                "add_tests": ["ABR"],
                "reason": "Sudden onset — ABR may help evaluate neural pathways",
            }
        ],
    },
    {
        "concern_type": "tinnitus",
        "age_band": None,
        "common_signs": _signs(
            ("laterality", "In which ear?"),
            ("pattern", "Constant or comes and goes?"),
            ("sleep", "Difficulty sleeping?"),
            ("noise_exposure", "Exposure to loud noise?"),
            ("stress", "Stress / Anxiety?"),
        ),
        "recommended_tests": ["PTA", "Tinnitus Assessment", "Tympanometry", "OAE", "SPIN"],
        "what_it_helps": "Finds the possible cause of ringing in your ears.",
        "outcome_options": None,
        "conditional_rules": None,
    },
    {
        "concern_type": "hyperacusis",
        "age_band": None,
        "common_signs": _signs(
            ("sensitivity", "Sensitivity to everyday sounds?"),
            ("discomfort", "Discomfort with normal sound levels?"),
            ("pain", "Pain or irritation with loud sounds?"),
            ("avoidance", "Avoids noisy places?"),
        ),
        "recommended_tests": ["LDL", "PTA", "Tympanometry", "SPIN"],
        "what_it_helps": "Identifies sound sensitivity and helps in management.",
        "outcome_options": None,
        "conditional_rules": None,
    },
    {
        "concern_type": "dizziness_balance",
        "age_band": None,
        "common_signs": _signs(
            ("timing", "When does it happen?"),
            ("sensation", "Spinning feeling or light headed?"),
            ("hearing_or_ringing", "Any hearing loss or ringing in ears?"),
            ("nausea", "Nausea / Vomiting?"),
            ("unsteady", "Unsteady while walking?"),
        ),
        "recommended_tests": ["VEMP", "VNG", "PTA"],
        "what_it_helps": "Checks balance system and inner ear function.",
        "outcome_options": None,
        "conditional_rules": [
            {
                "when": {"question_key": "unsteady", "answer_truthy": True},
                "add_tests": ["Posturography"],
                "reason": "Unsteady walking — posturography may be indicated",
            },
            {
                "when": {"question_key": "hearing_or_ringing", "answer_truthy": True},
                "add_tests": ["SPIN"],
                "reason": "Accompanying hearing/tinnitus symptoms — SPIN may help",
            },
        ],
    },
    {
        "concern_type": "ear_pain_discharge",
        "age_band": None,
        "common_signs": _signs(
            ("laterality", "In which ear?"),
            ("pain_or_discharge", "Pain, discharge or both?"),
            ("fever", "Fever or cold?"),
            ("recent_infection", "Recent ear infection?"),
            ("itching", "Itching in ear?"),
        ),
        "recommended_tests": ["Ear Evaluation (ENT)", "Tympanometry", "PTA", "Immittance Test", "OAE"],
        "what_it_helps": "Finds infection, fluid or other ear problems.",
        "outcome_options": None,
        "conditional_rules": None,
    },
    # child_concerns without age_band acts as a router entry; age-band rows hold pathways
    {
        "concern_type": "child_concerns",
        "age_band": None,
        "common_signs": _signs(
            ("age_band_pick", "Which age group is the child in? (newborn / infant_toddler / preschool / school_age)"),
        ),
        "recommended_tests": [],
        "what_it_helps": "Select an age band to see the paediatric hearing pathway.",
        "outcome_options": CHILD_OUTCOMES,
        "conditional_rules": None,
    },
    {
        "concern_type": "child_concerns",
        "age_band": "newborn",
        "common_signs": _signs(
            ("screening_done", "Was newborn hearing screening done?"),
            ("nicu", "Any NICU stay?"),
            ("not_responding", "Not responding to sounds?"),
            ("family_history", "Family history of hearing loss?"),
        ),
        "recommended_tests": ["OAE", "ABR", "BOA", "Tympanometry"],
        "what_it_helps": "Detects hearing loss early so intervention can begin before speech development.",
        "outcome_options": CHILD_OUTCOMES,
        "conditional_rules": [
            {
                "when": {"question_key": "nicu", "answer_truthy": True},
                "add_tests": ["ASSR"],
                "reason": "NICU history — ASSR may be considered",
            }
        ],
    },
    {
        "concern_type": "child_concerns",
        "age_band": "infant_toddler",
        "common_signs": _signs(
            ("responds", "Does the child respond to sounds?"),
            ("speech_delay", "Delayed speech?"),
            ("infections", "Frequent ear infections?"),
            ("attention", "Difficulty in feeding / attention?"),
        ),
        "recommended_tests": ["VRA", "OAE", "Tympanometry", "ABR"],
        "what_it_helps": "Identifies hearing issues that may delay speech and language milestones.",
        "outcome_options": CHILD_OUTCOMES,
        "conditional_rules": None,
    },
    {
        "concern_type": "child_concerns",
        "age_band": "preschool",
        "common_signs": _signs(
            ("speech_delay", "Speech delay?"),
            ("instructions", "Difficulty following instructions?"),
            ("inconsistent", "Doesn't respond consistently?"),
            ("learning", "Learning concerns?"),
        ),
        "recommended_tests": ["Play Audiometry", "OAE", "Speech Detection Threshold", "Tympanometry"],
        "what_it_helps": "Checks hearing ability through play-based tests suited for young children.",
        "outcome_options": CHILD_OUTCOMES,
        "conditional_rules": None,
    },
    {
        "concern_type": "child_concerns",
        "age_band": "school_age",
        "common_signs": _signs(
            ("classroom", "Difficulty hearing in class?"),
            ("repetition", "Frequently asking for repetition?"),
            ("academic", "Academic concerns?"),
        ),
        "recommended_tests": ["PTA", "Speech Audiometry", "OAE", "SPIN"],
        "what_it_helps": "Identifies hearing difficulties that affect learning and classroom performance.",
        "outcome_options": CHILD_OUTCOMES,
        "conditional_rules": [
            {
                "when": {"question_key": "academic", "answer_truthy": True},
                "add_tests": ["SRT", "WRS"],
                "reason": "Academic concerns — speech tests (SRT/WRS) may help",
            }
        ],
    },
]
