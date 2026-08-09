"""
Adult pathway seed content — Part 2 Adults.

SECTION A — Speech and Language (5 categories × 5 questions)
SECTION B — Audiology / Hearing (5 categories × 5 questions)

Answer set is Yes / No / Not sure unless a question specifies otherwise.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import ClinicalDepartment, FlowType

YNN: list[dict[str, str]] = [
    {"label": "Yes", "value": "yes"},
    {"label": "No", "value": "no"},
    {"label": "Not sure", "value": "not_sure"},
]

EAR_SIDE: list[dict[str, str]] = [
    {"label": "Right", "value": "right"},
    {"label": "Left", "value": "left"},
    {"label": "Both", "value": "both"},
    {"label": "Not sure", "value": "not_sure"},
]

EAR_COMPARE: list[dict[str, str]] = [
    {"label": "Right", "value": "right"},
    {"label": "Left", "value": "left"},
    {"label": "Both same", "value": "both_same"},
    {"label": "Not sure", "value": "not_sure"},
]

STUTTER_ONSET: list[dict[str, str]] = [
    {"label": "Since childhood", "value": "childhood"},
    {"label": "Recently", "value": "recently"},
    {"label": "Not sure", "value": "not_sure"},
]

CLARITY_ONSET: list[dict[str, str]] = [
    {"label": "Suddenly", "value": "suddenly"},
    {"label": "Gradually", "value": "gradually"},
    {"label": "Not sure", "value": "not_sure"},
]


def _q(
    condition_slug: str,
    key: str,
    text: str,
    display_order: int,
    *,
    options: list[dict[str, str]] | None = None,
    is_entry: bool = False,
) -> dict[str, Any]:
    return {
        "condition_slug": condition_slug,
        "key": key,
        "text": text,
        "display_order": display_order,
        "is_entry": is_entry,
        "options": list(options or YNN),
    }


def _baseline(
    condition_slug: str,
    name: str,
    description: str,
    tests: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "condition_slug": condition_slug,
        "name": name,
        "description": description,
        "is_baseline": True,
        "priority": 50,
        "rule_definition": {},
        "tests": tests,
    }


ADULT_CATEGORIES: list[dict[str, Any]] = [
    # Section A — Speech and Language
    {
        "slug": "adult-speech-language",
        "name": "Speech and Language Issues",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Word finding, understanding others, reading/writing, or post-stroke speech change.",
        "display_order": 1,
    },
    {
        "slug": "adult-stuttering",
        "name": "Stuttering (Fluency)",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Repeating sounds or words, getting stuck, or avoiding speaking situations.",
        "display_order": 2,
    },
    {
        "slug": "adult-speech-clarity",
        "name": "Speech Clarity",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Slurred or unclear speech, or people often asking you to repeat.",
        "display_order": 3,
    },
    {
        "slug": "adult-voice-problems",
        "name": "Voice Problems",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Hoarse, rough or weak voice lasting more than two weeks.",
        "display_order": 4,
    },
    {
        "slug": "adult-feeding-swallowing",
        "name": "Feeding and Swallowing",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Coughing or choking with meals, food sticking, or diet changes.",
        "display_order": 5,
    },
    # Section B — Audiology (Hearing)
    {
        "slug": "hearing-difficulty",
        "name": "Hearing Difficulty",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Hard to follow conversation, asking people to repeat, or loud TV volume.",
        "display_order": 6,
    },
    {
        "slug": "ringing-in-ears",
        "name": "Ringing in the Ears",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Ringing or buzzing others cannot hear that may disturb sleep or focus.",
        "display_order": 7,
    },
    {
        "slug": "dizziness-balance",
        "name": "Dizziness / Balance",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Dizzy, spinning or unsteady; worse with head turns or in the dark.",
        "display_order": 8,
    },
    {
        "slug": "other-hearing-related",
        "name": "Other Hearing Issues",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Blocked ear, sound sensitivity, medication, or hearing aid use.",
        "display_order": 9,
    },
    {
        "slug": "ear-pain-discharge",
        "name": "Ear Pain / Discharge",
        "flow_type": FlowType.ADULT.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Ear pain, fluid or pus from the ear, fever, or recent cold.",
        "display_order": 10,
    },
]


ADULT_CONDITIONS: list[dict[str, Any]] = [
    {
        "slug": "adult-speech-language-screen",
        "category_slug": "adult-speech-language",
        "name": "Speech and language screening",
        "description": "Screening questions for adult speech and language concerns.",
        "display_order": 1,
    },
    {
        "slug": "adult-stuttering-fluency",
        "category_slug": "adult-stuttering",
        "name": "Stuttering / fluency screening",
        "description": "Screening questions for stuttering and fluency.",
        "display_order": 1,
    },
    {
        "slug": "adult-speech-clarity-screen",
        "category_slug": "adult-speech-clarity",
        "name": "Speech clarity screening",
        "description": "Screening questions for speech clarity.",
        "display_order": 1,
    },
    {
        "slug": "adult-voice-screen",
        "category_slug": "adult-voice-problems",
        "name": "Voice problem screening",
        "description": "Screening questions for voice problems.",
        "display_order": 1,
    },
    {
        "slug": "adult-feeding-swallowing-screen",
        "category_slug": "adult-feeding-swallowing",
        "name": "Feeding and swallowing screening",
        "description": "Screening questions for feeding and swallowing.",
        "display_order": 1,
    },
    {
        "slug": "adult-hearing-difficulty-screen",
        "category_slug": "hearing-difficulty",
        "name": "Hearing difficulty screening",
        "description": "Screening questions for adult hearing difficulty.",
        "display_order": 1,
    },
    {
        "slug": "adult-ringing-ears-screen",
        "category_slug": "ringing-in-ears",
        "name": "Ringing in ears screening",
        "description": "Screening questions for tinnitus / ringing.",
        "display_order": 1,
    },
    {
        "slug": "adult-dizziness-balance-screen",
        "category_slug": "dizziness-balance",
        "name": "Dizziness / balance screening",
        "description": "Screening questions for dizziness and balance.",
        "display_order": 1,
    },
    {
        "slug": "adult-other-hearing-screen",
        "category_slug": "other-hearing-related",
        "name": "Other hearing issues screening",
        "description": "Screening questions for other hearing concerns.",
        "display_order": 1,
    },
    {
        "slug": "adult-ear-pain-discharge-screen",
        "category_slug": "ear-pain-discharge",
        "name": "Ear pain / discharge screening",
        "description": "Screening questions for ear pain or discharge.",
        "display_order": 1,
    },
]


ADULT_QUESTIONS: list[dict[str, Any]] = [
    # 1. Speech and Language Issues
    _q("adult-speech-language-screen", "struggle_find_word", "Do you struggle to find the right word?", 1, is_entry=True),
    _q("adult-speech-language-screen", "hard_understand_others", "Is it hard to understand what others say?", 2),
    _q("adult-speech-language-screen", "difficulty_reading_writing_numbers", "Any difficulty reading, writing or with numbers?", 3),
    _q("adult-speech-language-screen", "after_stroke_or_head_injury", "Did this start after a stroke or head injury?", 4),
    _q("adult-speech-language-screen", "affects_work_or_daily_life", "Does it affect your work or daily life?", 5),
    # 2. Stuttering (Fluency)
    _q("adult-stuttering-fluency", "repeats_sounds_words", "Do you repeat sounds or words while speaking?", 1, is_entry=True),
    _q("adult-stuttering-fluency", "gets_stuck_on_word", "Do you get stuck on a word?", 2),
    _q("adult-stuttering-fluency", "avoids_calls_speaking", "Do you avoid calls or speaking situations?", 3),
    _q("adult-stuttering-fluency", "tension_face_jaw", "Any tension in face or jaw while speaking?", 4),
    _q("adult-stuttering-fluency", "when_did_it_start", "When did it start?", 5, options=STUTTER_ONSET),
    # 3. Speech Clarity
    _q("adult-speech-clarity-screen", "people_ask_to_repeat", "Do people often ask you to repeat?", 1, is_entry=True),
    _q("adult-speech-clarity-screen", "speech_slurred_or_slow", "Does your speech sound slurred or slow?", 2),
    _q("adult-speech-clarity-screen", "worse_when_tired", "Does it get worse when you are tired?", 3),
    _q("adult-speech-clarity-screen", "weakness_face_lips_tongue", "Any weakness in face, lips or tongue?", 4),
    _q("adult-speech-clarity-screen", "how_did_it_start", "How did it start?", 5, options=CLARITY_ONSET),
    # 4. Voice Problems
    _q("adult-voice-screen", "voice_hoarse_rough_weak", "Is your voice hoarse, rough or weak?", 1, is_entry=True),
    _q("adult-voice-screen", "voice_tires_after_talking", "Does your voice tire out after talking?", 2),
    _q("adult-voice-screen", "throat_pain_or_tightness", "Any throat pain or tightness while speaking?", 3),
    _q("adult-voice-screen", "job_heavy_voice_use", "Does your job need heavy voice use?", 4),
    _q("adult-voice-screen", "voice_different_over_2_weeks", "Has your voice been different for over 2 weeks?", 5),
    # 5. Feeding and Swallowing
    _q("adult-feeding-swallowing-screen", "cough_choke_eating", "Do you cough or choke while eating or drinking?", 1, is_entry=True),
    _q("adult-feeding-swallowing-screen", "food_stuck_throat_chest", "Does food feel stuck in your throat or chest?", 2),
    _q("adult-feeding-swallowing-screen", "meals_take_longer", "Do meals take much longer than before?", 3),
    _q("adult-feeding-swallowing-screen", "changed_diet", "Have you changed your diet because of this?", 4),
    _q("adult-feeding-swallowing-screen", "weight_loss_chest_infections", "Any weight loss or repeated chest infections?", 5),
    # 1. Hearing Difficulty
    _q("adult-hearing-difficulty-screen", "hard_in_noisy_places", "Is it hard to follow conversation in noisy places?", 1, is_entry=True),
    _q("adult-hearing-difficulty-screen", "often_ask_to_repeat", "Do you often ask people to repeat?", 2),
    _q("adult-hearing-difficulty-screen", "tv_volume_too_loud", "Do others say your TV volume is too loud?", 3),
    _q("adult-hearing-difficulty-screen", "one_ear_worse", "Is one ear worse than the other?", 4, options=EAR_COMPARE),
    _q("adult-hearing-difficulty-screen", "long_term_noise_work", "Any long-term loud noise exposure at work?", 5),
    # 2. Ringing in the Ears
    _q("adult-ringing-ears-screen", "hears_ringing_others_cannot", "Do you hear ringing or buzzing others cannot?", 1, is_entry=True),
    _q("adult-ringing-ears-screen", "present_in_quiet_room", "Is it present even in a quiet room?", 2),
    _q("adult-ringing-ears-screen", "disturbs_sleep_or_focus", "Does it disturb your sleep or focus?", 3),
    _q("adult-ringing-ears-screen", "after_noise_infection_medicine", "Did it start after loud noise, infection or new medicine?", 4),
    _q("adult-ringing-ears-screen", "which_ear", "Which ear?", 5, options=EAR_SIDE),
    # 3. Dizziness / Balance
    _q("adult-dizziness-balance-screen", "dizzy_spinning_unsteady", "Do you feel dizzy, spinning or unsteady?", 1, is_entry=True),
    _q("adult-dizziness-balance-screen", "starts_head_turn_or_stand", "Does it start when you turn your head or stand up?", 2),
    _q("adult-dizziness-balance-screen", "vomiting_hearing_loss_fullness", "Any vomiting, hearing loss or ear fullness with it?", 3),
    _q("adult-dizziness-balance-screen", "fallen_or_nearly_fallen", "Have you fallen or nearly fallen because of it?", 4),
    _q("adult-dizziness-balance-screen", "walking_harder_in_dark", "Is walking harder in the dark?", 5),
    # 4. Other Hearing Issues
    _q("adult-other-hearing-screen", "ear_blocked_or_pressure", "Do you feel the ear is blocked or under pressure?", 1, is_entry=True),
    _q("adult-other-hearing-screen", "normal_sounds_too_loud", "Are normal sounds uncomfortably loud?", 2),
    _q("adult-other-hearing-screen", "hard_to_locate_sound", "Is it hard to tell where a sound comes from?", 3),
    _q("adult-other-hearing-screen", "long_term_medication", "Are you on any long-term medication?", 4),
    _q("adult-other-hearing-screen", "already_use_hearing_aid", "Do you already use a hearing aid?", 5),
    # 5. Ear Pain / Discharge
    _q("adult-ear-pain-discharge-screen", "pain_or_discomfort_ear", "Do you have pain or discomfort in the ear?", 1, is_entry=True),
    _q("adult-ear-pain-discharge-screen", "fluid_pus_or_blood", "Any fluid, pus or blood from the ear?", 2),
    _q("adult-ear-pain-discharge-screen", "fever_along_with_it", "Any fever along with it?", 3),
    _q("adult-ear-pain-discharge-screen", "recent_cold_cough_nose", "Any recent cold, cough or blocked nose?", 4),
    _q("adult-ear-pain-discharge-screen", "happened_past_year", "Has this happened before in the past year?", 5),
]


_SPEECH_TESTS = [
    {
        "test_code": "SLP_EVAL",
        "test_name": "Speech-Language Evaluation",
        "reason_text": "A speech-language assessment reviews how you understand and use language.",
        "display_order": 1,
    },
    {
        "test_code": "PTA",
        "test_name": "Pure Tone Audiometry",
        "reason_text": "Hearing is checked because it affects speech and communication.",
        "display_order": 2,
    },
]

_HEARING_TESTS = [
    {
        "test_code": "PTA",
        "test_name": "Pure Tone Audiometry",
        "reason_text": "Measures how soft a sound you can hear at different pitches.",
        "display_order": 1,
    },
    {
        "test_code": "TYMP",
        "test_name": "Tympanometry",
        "reason_text": "Checks the eardrum and middle ear.",
        "display_order": 2,
    },
    {
        "test_code": "SPEECH",
        "test_name": "Speech Audiometry",
        "reason_text": "Measures how clearly you understand speech.",
        "display_order": 3,
    },
]


ADULT_RULES: list[dict[str, Any]] = [
    _baseline(
        "adult-speech-language-screen",
        "Baseline — adult speech and language",
        "Standard speech-language screen with hearing check.",
        _SPEECH_TESTS,
    ),
    _baseline(
        "adult-stuttering-fluency",
        "Baseline — adult stuttering / fluency",
        "Fluency assessment with hearing screen.",
        [
            {
                "test_code": "FLUENCY_EVAL",
                "test_name": "Fluency Assessment",
                "reason_text": "Looks at how smoothly you speak and what support may help.",
                "display_order": 1,
            },
            _SPEECH_TESTS[1],
        ],
    ),
    _baseline(
        "adult-speech-clarity-screen",
        "Baseline — adult speech clarity",
        "Articulation / clarity assessment with hearing check.",
        [
            {
                "test_code": "ARTIC_EVAL",
                "test_name": "Speech Sound / Clarity Assessment",
                "reason_text": "Checks which speech sounds are clear and which need support.",
                "display_order": 1,
            },
            _SPEECH_TESTS[1],
        ],
    ),
    _baseline(
        "adult-voice-screen",
        "Baseline — adult voice problems",
        "Voice assessment with hearing screen.",
        [
            {
                "test_code": "VOICE_EVAL",
                "test_name": "Voice Assessment",
                "reason_text": "Reviews voice quality, strain, and day-to-day voice use.",
                "display_order": 1,
            },
            _SPEECH_TESTS[1],
        ],
    ),
    _baseline(
        "adult-feeding-swallowing-screen",
        "Baseline — adult feeding and swallowing",
        "Swallowing / feeding assessment.",
        [
            {
                "test_code": "SWALLOW_ASSESS",
                "test_name": "Clinical Swallowing Assessment",
                "reason_text": "Checks safety and comfort when you eat and drink.",
                "display_order": 1,
            },
            {
                "test_code": "SLP_EVAL",
                "test_name": "Speech-Language Evaluation",
                "reason_text": "Swallowing concerns are reviewed together with communication.",
                "display_order": 2,
            },
        ],
    ),
    _baseline(
        "adult-hearing-difficulty-screen",
        "Baseline — adult hearing difficulty",
        "Standard adult hearing battery.",
        _HEARING_TESTS,
    ),
    _baseline(
        "adult-ringing-ears-screen",
        "Baseline — adult ringing in ears",
        "Hearing assessment for tinnitus concerns.",
        [
            *_HEARING_TESTS[:2],
            {
                "test_code": "TINN_ASSESS",
                "test_name": "Tinnitus Assessment",
                "reason_text": "Assesses ringing concerns together with hearing levels.",
                "display_order": 3,
            },
        ],
    ),
    _baseline(
        "adult-dizziness-balance-screen",
        "Baseline — adult dizziness / balance",
        "Hearing and balance-related assessment.",
        [
            *_HEARING_TESTS[:2],
            {
                "test_code": "VNG",
                "test_name": "Videonystagmography / balance screening",
                "reason_text": "Looks at balance concerns that can share pathways with the ear.",
                "display_order": 3,
            },
        ],
    ),
    _baseline(
        "adult-other-hearing-screen",
        "Baseline — adult other hearing issues",
        "Hearing assessment for other ear-related concerns.",
        _HEARING_TESTS,
    ),
    _baseline(
        "adult-ear-pain-discharge-screen",
        "Baseline — adult ear pain / discharge",
        "Middle-ear focused assessment for pain or discharge.",
        [
            {
                "test_code": "OTOSCOPY",
                "test_name": "Ear Examination",
                "reason_text": "The ear canal and eardrum are examined for infection or blockage.",
                "display_order": 1,
            },
            {
                "test_code": "TYMP",
                "test_name": "Tympanometry",
                "reason_text": "Checks middle-ear pressure and eardrum movement.",
                "display_order": 2,
            },
            {
                "test_code": "PTA",
                "test_name": "Pure Tone Audiometry",
                "reason_text": "Documents hearing while ear symptoms are present.",
                "display_order": 3,
            },
        ],
    ),
]

# Old adult category / condition slugs to remove when reseeding.
LEGACY_ADULT_CATEGORY_SLUGS = {
    "speech-voice-adult",
}
LEGACY_ADULT_CONDITION_SLUGS = {
    "gradual-hearing-loss",
    "sudden-hearing-loss",
    "tinnitus",
    "dizziness-imbalance",
    "other-hearing-concern",
    "ear-pain-discharge",
    "adult-speech-voice",
}
