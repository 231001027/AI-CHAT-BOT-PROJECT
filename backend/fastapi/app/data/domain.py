"""
Static domain data for HearConnect (mirrors frontend TypeScript data files).
Icons stay on the frontend; the API returns content fields only.
"""

from __future__ import annotations

HEARING_PROBLEMS: list[dict] = [
    {
        "id": "hearing-difficulty",
        "title": "Hearing Difficulty",
        "accent": "blue",
        "symptoms": ["Cannot hear properly", "Muffled sounds", "Asking people to repeat"],
        "route": "/adult-care#hearing-difficulty",
    },
    {
        "id": "tinnitus",
        "title": "Ringing in Ears (Tinnitus)",
        "accent": "purple",
        "symptoms": ["Ringing", "Buzzing", "Hissing"],
        "route": "/adult-care#tinnitus",
    },
    {
        "id": "dizziness",
        "title": "Dizziness / Balance",
        "accent": "green",
        "symptoms": ["Feeling dizzy", "Room spinning", "Difficulty walking"],
        "route": "/adult-care#balance-problems",
    },
    {
        "id": "ear-pain",
        "title": "Ear Pain / Discharge",
        "accent": "blue",
        "symptoms": ["Ear pain", "Fluid", "Infection"],
        "route": "/adult-care#ear-pain",
    },
    {
        "id": "child-concerns",
        "title": "Child Hearing Concerns",
        "accent": "purple",
        "symptoms": ["Delayed speech", "Doesn't respond to sounds", "Frequent ear infections"],
        "route": "/child-care",
    },
]

ADULT_SECTIONS: list[dict] = [
    {
        "id": "hearing-difficulty",
        "title": "Hearing Difficulty",
        "accent": "blue",
        "questions": [
            "When did it start?",
            "One ear or both?",
            "Sudden or gradual?",
            "Noise exposure?",
            "Previous ear problems?",
        ],
        "tests": ["PTA", "Speech Audiometry", "Tympanometry", "OAE", "SPIN"],
    },
    {
        "id": "tinnitus",
        "title": "Ringing in Ear",
        "accent": "purple",
        "questions": ["Which ear?", "Constant?", "Sleeping difficulty?", "Stress?"],
        "tests": ["PTA", "Tinnitus Assessment", "OAE", "SPIN"],
    },
    {
        "id": "hyperacusis",
        "title": "Hyperacusis",
        "accent": "green",
        "questions": ["Sensitive to sounds?", "Pain?", "Avoid loud places?"],
        "tests": ["LDL", "Audiometry", "Tympanometry", "SPIN"],
    },
    {
        "id": "balance-problems",
        "title": "Balance Problems",
        "accent": "blue",
        "questions": ["Spinning sensation?", "Vomiting?", "Walking issues?"],
        "tests": ["VEMP", "VNG", "PTA", "SPIN"],
    },
    {
        "id": "ear-pain",
        "title": "Ear Pain",
        "accent": "purple",
        "questions": ["Pain?", "Discharge?", "Fever?", "Recent infection?"],
        "tests": ["ENT Evaluation", "Tympanometry", "OAE"],
    },
    {
        "id": "other-hearing-problems",
        "title": "Other Hearing Problems",
        "accent": "green",
        "questions": ["Ear blockage?", "Speech understanding?", "Previous surgery?"],
        "tests": ["PTA", "Speech Audiometry", "Tympanometry"],
    },
]

SPECIAL_TESTS: list[dict] = [
    {
        "code": "ABR",
        "name": "Auditory Brainstem Response",
        "description": "Measures hearing nerve and brain pathway responses.",
    },
    {
        "code": "MLR",
        "name": "Middle Latency Response",
        "description": "Evaluates middle-latency auditory evoked potentials.",
    },
    {
        "code": "LLR",
        "name": "Late Latency Response",
        "description": "Assesses cortical auditory processing.",
    },
    {
        "code": "P300",
        "name": "Cognitive Evoked Potential",
        "description": "Detects attention and cognitive hearing processing.",
    },
    {
        "code": "P500",
        "name": "P500 Response",
        "description": "Evaluates higher-level auditory discrimination.",
    },
    {
        "code": "SRT",
        "name": "Speech Reception Threshold",
        "description": "Lowest level at which speech is understood.",
    },
    {
        "code": "WRS",
        "name": "Word Recognition Score",
        "description": "Tests clarity of word recognition at conversational levels.",
    },
    {
        "code": "PB Test",
        "name": "Phonetically Balanced Test",
        "description": "Measures speech discrimination with balanced words.",
    },
    {
        "code": "SPIN",
        "name": "Speech in Noise Test",
        "description": "Assesses understanding of speech in background noise.",
    },
]

CHILD_CATEGORIES: list[dict] = [
    {
        "id": "newborn",
        "title": "Newborn",
        "ageRange": "0-6 Months",
        "accent": "blue",
        "questions": ["NICU stay?", "Responding to sounds?", "Family history?"],
        "tests": ["OAE", "ABR", "BOA", "Tympanometry"],
    },
    {
        "id": "infant",
        "title": "Infant",
        "ageRange": "6 Months-2.5 Years",
        "accent": "purple",
        "questions": ["Responds to sounds?", "Delayed speech?", "Ear infections?"],
        "tests": ["VRA", "OAE", "Tympanometry", "ABR"],
    },
    {
        "id": "preschool",
        "title": "Preschool Child",
        "ageRange": "3-5 Years",
        "accent": "green",
        "questions": ["Speech delay?", "Instructions?", "Learning concerns?"],
        "tests": ["Play Audiometry", "OAE", "Speech Detection"],
    },
    {
        "id": "school-age",
        "title": "School Age Child",
        "ageRange": "6+ Years",
        "accent": "blue",
        "questions": ["Difficulty hearing?", "Academic concerns?"],
        "tests": ["PTA", "Speech Audiometry", "OAE", "Special Tests"],
    },
]
