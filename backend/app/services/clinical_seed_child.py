"""
Child pathway seed content — Part 1 Children.

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


CHILD_CATEGORIES: list[dict[str, Any]] = [
    # Section A — Speech and Language
    {
        "slug": "child-speech-language",
        "name": "Speech and Language Issues",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Speaking less than peers, following instructions, or conversation difficulty.",
        "display_order": 1,
    },
    {
        "slug": "child-stuttering",
        "name": "Stuttering (Fluency)",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Repeating sounds or words, getting stuck, or avoiding speaking.",
        "display_order": 2,
    },
    {
        "slug": "child-speech-clarity",
        "name": "Speech Clarity",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Hard for others to understand, missing sounds, or late talking.",
        "display_order": 3,
    },
    {
        "slug": "child-voice-problems",
        "name": "Voice Problems",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Hoarse, weak, or painful voice lasting more than two weeks.",
        "display_order": 4,
    },
    {
        "slug": "child-feeding-swallowing",
        "name": "Feeding and Swallowing",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.SPEECH_LANGUAGE.value,
        "description": "Coughing or choking with meals, long mealtimes, or refusing food.",
        "display_order": 5,
    },
    # Section B — Audiology (Hearing)
    {
        "slug": "child-hearing-difficulty",
        "name": "Hearing Difficulty",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Not responding when called, high TV volume, or family hearing loss.",
        "display_order": 6,
    },
    {
        "slug": "child-ringing-in-ears",
        "name": "Ringing in the Ears",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Ringing or buzzing that may disturb sleep or concentration.",
        "display_order": 7,
    },
    {
        "slug": "child-dizziness-balance",
        "name": "Dizziness / Balance",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Feeling dizzy or unsteady, falling, or difficulty walking in the dark.",
        "display_order": 8,
    },
    {
        "slug": "child-other-hearing",
        "name": "Other Hearing Issues",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Blocked ear, sound sensitivity, or loud earphone / noise exposure.",
        "display_order": 9,
    },
    {
        "slug": "child-ear-pain-discharge",
        "name": "Ear Pain / Discharge",
        "flow_type": FlowType.CHILD.value,
        "department": ClinicalDepartment.AUDIOLOGY.value,
        "description": "Ear pain, fluid or pus from the ear, fever, or recent cold.",
        "display_order": 10,
    },
]


CHILD_CONDITIONS: list[dict[str, Any]] = [
    {
        "slug": "child-speech-language-issues",
        "category_slug": "child-speech-language",
        "name": "Speech and language screening",
        "description": "Screening questions for speech and language concerns.",
        "display_order": 1,
    },
    {
        "slug": "child-stuttering-fluency",
        "category_slug": "child-stuttering",
        "name": "Stuttering / fluency screening",
        "description": "Screening questions for stuttering and fluency.",
        "display_order": 1,
    },
    {
        "slug": "child-speech-clarity-issues",
        "category_slug": "child-speech-clarity",
        "name": "Speech clarity screening",
        "description": "Screening questions for speech clarity.",
        "display_order": 1,
    },
    {
        "slug": "child-voice-issues",
        "category_slug": "child-voice-problems",
        "name": "Voice problem screening",
        "description": "Screening questions for voice problems.",
        "display_order": 1,
    },
    {
        "slug": "child-feeding-swallowing-issues",
        "category_slug": "child-feeding-swallowing",
        "name": "Feeding and swallowing screening",
        "description": "Screening questions for feeding and swallowing.",
        "display_order": 1,
    },
    {
        "slug": "child-hearing-difficulty-screen",
        "category_slug": "child-hearing-difficulty",
        "name": "Hearing difficulty screening",
        "description": "Screening questions for hearing difficulty.",
        "display_order": 1,
    },
    {
        "slug": "child-ringing-ears-screen",
        "category_slug": "child-ringing-in-ears",
        "name": "Ringing in ears screening",
        "description": "Screening questions for tinnitus / ringing.",
        "display_order": 1,
    },
    {
        "slug": "child-dizziness-balance-screen",
        "category_slug": "child-dizziness-balance",
        "name": "Dizziness / balance screening",
        "description": "Screening questions for dizziness and balance.",
        "display_order": 1,
    },
    {
        "slug": "child-other-hearing-screen",
        "category_slug": "child-other-hearing",
        "name": "Other hearing issues screening",
        "description": "Screening questions for other hearing concerns.",
        "display_order": 1,
    },
    {
        "slug": "child-ear-pain-discharge-screen",
        "category_slug": "child-ear-pain-discharge",
        "name": "Ear pain / discharge screening",
        "description": "Screening questions for ear pain or discharge.",
        "display_order": 1,
    },
]


CHILD_QUESTIONS: list[dict[str, Any]] = [
    # 1. Speech and Language Issues
    _q("child-speech-language-issues", "speaks_less_than_peers", "Does your child speak less than other children of the same age?", 1, is_entry=True),
    _q("child-speech-language-issues", "follows_simple_instructions", "Does your child follow simple instructions?", 2),
    _q("child-speech-language-issues", "points_instead_of_talking", "Does your child point or gesture instead of talking?", 3),
    _q("child-speech-language-issues", "stopped_using_words", "Has your child stopped using words they knew before?", 4),
    _q("child-speech-language-issues", "hard_to_hold_conversation", "Is it hard for your child to hold a conversation?", 5),
    # 2. Stuttering (Fluency)
    _q("child-stuttering-fluency", "repeats_sounds_words", "Does your child repeat sounds or words while speaking?", 1, is_entry=True),
    _q("child-stuttering-fluency", "gets_stuck_on_word", "Does your child get stuck on a word?", 2),
    _q("child-stuttering-fluency", "stretches_sounds", "Does your child stretch out sounds?", 3),
    _q("child-stuttering-fluency", "eye_blink_head_movements", "Any eye blinking or head movements while speaking?", 4),
    _q("child-stuttering-fluency", "avoids_speaking", "Does your child avoid speaking because of this?", 5),
    # 3. Speech Clarity
    _q("child-speech-clarity-issues", "outsiders_hard_to_understand", "Do outsiders find it hard to understand your child?", 1, is_entry=True),
    _q("child-speech-clarity-issues", "miss_or_mix_sounds", "Does your child miss or mix up sounds in words?", 2),
    _q("child-speech-clarity-issues", "must_repeat_what_child_said", "Do you have to repeat what your child said?", 3),
    _q("child-speech-clarity-issues", "speech_rate_mumbled", "Is your child’s speech too fast, slow or mumbled?", 4),
    _q("child-speech-clarity-issues", "started_speaking_late", "Did your child start speaking late?", 5),
    # 4. Voice Problems
    _q("child-voice-issues", "voice_hoarse_rough", "Is your child’s voice hoarse or rough?", 1, is_entry=True),
    _q("child-voice-issues", "voice_weak_after_talking", "Does the voice get weak after talking a while?", 2),
    _q("child-voice-issues", "throat_pain_while_speaking", "Does your child complain of throat pain while speaking?", 3),
    _q("child-voice-issues", "shouts_or_screams_often", "Does your child shout or scream often?", 4),
    _q("child-voice-issues", "voice_different_over_2_weeks", "Has the voice been different for over 2 weeks?", 5),
    # 5. Feeding and Swallowing
    _q("child-feeding-swallowing-issues", "cough_choke_eating", "Does your child cough or choke while eating or drinking?", 1, is_entry=True),
    _q("child-feeding-swallowing-issues", "food_out_nose_mouth", "Does food or liquid come out of the nose or mouth?", 2),
    _q("child-feeding-swallowing-issues", "meal_over_30_minutes", "Does a meal take more than 30 minutes?", 3),
    _q("child-feeding-swallowing-issues", "refuses_solids_liquids", "Does your child refuse solids or liquids?", 4),
    _q("child-feeding-swallowing-issues", "poor_weight_chest_infections", "Poor weight gain or repeated chest infections?", 5),
    # 1. Hearing Difficulty
    _q("child-hearing-difficulty-screen", "not_respond_called_behind", "Does your child not respond when called from behind?", 1, is_entry=True),
    _q("child-hearing-difficulty-screen", "asks_to_repeat_often", "Does your child ask you to repeat often?", 2),
    _q("child-hearing-difficulty-screen", "tv_volume_very_high", "Does your child keep the TV volume very high?", 3),
    _q("child-hearing-difficulty-screen", "harder_in_noisy_places", "Is hearing harder in noisy places?", 4),
    _q("child-hearing-difficulty-screen", "family_hearing_loss", "Any hearing loss in the family?", 5),
    # 2. Ringing in the Ears
    _q("child-ringing-ears-screen", "hears_ringing_buzzing", "Does your child hear ringing or buzzing in the ear?", 1, is_entry=True),
    _q("child-ringing-ears-screen", "present_in_quiet_room", "Is it present even in a quiet room?", 2),
    _q("child-ringing-ears-screen", "disturbs_sleep_concentration", "Does it disturb sleep or concentration?", 3),
    _q("child-ringing-ears-screen", "after_noise_infection_injury", "Did it start after loud noise, infection or injury?", 4),
    _q("child-ringing-ears-screen", "which_ear", "Which ear?", 5, options=EAR_SIDE),
    # 3. Dizziness / Balance
    _q("child-dizziness-balance-screen", "feels_dizzy_unsteady", "Does your child feel dizzy or unsteady?", 1, is_entry=True),
    _q("child-dizziness-balance-screen", "falls_or_bumps_often", "Does your child fall or bump into things often?", 2),
    _q("child-dizziness-balance-screen", "dizzy_with_head_movement", "Does dizziness start with sudden head movement?", 3),
    _q("child-dizziness-balance-screen", "vomiting_or_hearing_loss", "Any vomiting or hearing loss with it?", 4),
    _q("child-dizziness-balance-screen", "walking_harder_in_dark", "Is walking harder in the dark?", 5),
    # 4. Other Hearing Issues
    _q("child-other-hearing-screen", "ear_blocked_or_full", "Does your child feel the ear is blocked or full?", 1, is_entry=True),
    _q("child-other-hearing-screen", "upset_by_loud_sounds", "Is your child upset by loud everyday sounds?", 2),
    _q("child-other-hearing-screen", "hard_to_locate_sound", "Is it hard to tell where a sound comes from?", 3),
    _q("child-other-hearing-screen", "frequent_colds_allergy", "Frequent colds, allergy or blocked nose?", 4),
    _q("child-other-hearing-screen", "loud_earphones_noise", "Loud earphone use or noise exposure?", 5),
    # 5. Ear Pain / Discharge
    _q("child-ear-pain-discharge-screen", "ear_pain_or_pulls_ear", "Does your child have ear pain or pull at the ear?", 1, is_entry=True),
    _q("child-ear-pain-discharge-screen", "fluid_pus_or_blood", "Any fluid, pus or blood from the ear?", 2),
    _q("child-ear-pain-discharge-screen", "fever_along_with_it", "Any fever along with it?", 3),
    _q("child-ear-pain-discharge-screen", "recent_cold_blocked_nose", "Any recent cold or blocked nose?", 4),
    _q("child-ear-pain-discharge-screen", "happened_past_year", "Has this happened before in the past year?", 5),
]


_SPEECH_TESTS = [
    {
        "test_code": "SLP_EVAL",
        "test_name": "Speech-Language Evaluation",
        "reason_text": "A speech-language assessment reviews how your child understands and uses language.",
        "display_order": 1,
    },
    {
        "test_code": "OAE",
        "test_name": "Otoacoustic Emissions",
        "reason_text": "Hearing is checked first, because hearing affects how speech develops.",
        "display_order": 2,
    },
]

_HEARING_TESTS = [
    {
        "test_code": "PTA",
        "test_name": "Pure Tone Audiometry / age-appropriate hearing test",
        "reason_text": "Measures how soft a sound your child can hear at different pitches.",
        "display_order": 1,
    },
    {
        "test_code": "TYMP",
        "test_name": "Tympanometry",
        "reason_text": "Checks the eardrum and middle ear, which often affect children’s hearing.",
        "display_order": 2,
    },
    {
        "test_code": "OAE",
        "test_name": "Otoacoustic Emissions",
        "reason_text": "A quick check of inner-ear response that suits children well.",
        "display_order": 3,
    },
]


CHILD_RULES: list[dict[str, Any]] = [
    _baseline(
        "child-speech-language-issues",
        "Baseline — child speech and language",
        "Standard speech-language screen with hearing check.",
        _SPEECH_TESTS,
    ),
    _baseline(
        "child-stuttering-fluency",
        "Baseline — child stuttering / fluency",
        "Fluency assessment with hearing screen.",
        [
            {
                "test_code": "FLUENCY_EVAL",
                "test_name": "Fluency Assessment",
                "reason_text": "Looks at how smoothly your child speaks and what helps them.",
                "display_order": 1,
            },
            _SPEECH_TESTS[1],
        ],
    ),
    _baseline(
        "child-speech-clarity-issues",
        "Baseline — child speech clarity",
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
        "child-voice-issues",
        "Baseline — child voice problems",
        "Voice assessment with hearing screen.",
        [
            {
                "test_code": "VOICE_EVAL",
                "test_name": "Voice Assessment",
                "reason_text": "Reviews voice quality, strain, and how the voice is used day to day.",
                "display_order": 1,
            },
            _SPEECH_TESTS[1],
        ],
    ),
    _baseline(
        "child-feeding-swallowing-issues",
        "Baseline — child feeding and swallowing",
        "Swallowing / feeding assessment.",
        [
            {
                "test_code": "SWALLOW_ASSESS",
                "test_name": "Feeding and Swallowing Assessment",
                "reason_text": "Checks safety and comfort when your child eats and drinks.",
                "display_order": 1,
            },
            {
                "test_code": "SLP_EVAL",
                "test_name": "Speech-Language Evaluation",
                "reason_text": "Feeding concerns are reviewed together with communication development.",
                "display_order": 2,
            },
        ],
    ),
    _baseline(
        "child-hearing-difficulty-screen",
        "Baseline — child hearing difficulty",
        "Standard paediatric hearing battery.",
        _HEARING_TESTS,
    ),
    _baseline(
        "child-ringing-ears-screen",
        "Baseline — child ringing in ears",
        "Hearing assessment for tinnitus concerns.",
        _HEARING_TESTS,
    ),
    _baseline(
        "child-dizziness-balance-screen",
        "Baseline — child dizziness / balance",
        "Hearing and balance-related assessment.",
        [
            *_HEARING_TESTS[:2],
            {
                "test_code": "BALANCE_FN",
                "test_name": "Balance Function Screening",
                "reason_text": "Looks at balance concerns that can share pathways with the ear.",
                "display_order": 3,
            },
        ],
    ),
    _baseline(
        "child-other-hearing-screen",
        "Baseline — child other hearing issues",
        "Hearing assessment for other ear-related concerns.",
        _HEARING_TESTS,
    ),
    _baseline(
        "child-ear-pain-discharge-screen",
        "Baseline — child ear pain / discharge",
        "Middle-ear focused assessment for pain or discharge.",
        [
            {
                "test_code": "TYMP",
                "test_name": "Tympanometry",
                "reason_text": "Checks middle-ear pressure and eardrum movement when pain or discharge is reported.",
                "display_order": 1,
            },
            {
                "test_code": "OTOSCOPY",
                "test_name": "Ear Examination",
                "reason_text": "The ear canal and eardrum are examined for infection or blockage.",
                "display_order": 2,
            },
            {
                "test_code": "PTA",
                "test_name": "Pure Tone Audiometry / age-appropriate hearing test",
                "reason_text": "Documents hearing while ear symptoms are present.",
                "display_order": 3,
            },
        ],
    ),
]

# Old child category / condition slugs to remove when reseeding.
LEGACY_CHILD_CATEGORY_SLUGS = {
    "newborn-screening",
    "child-hearing-concern",
    "child-speech-delay",
    "child-device-support",
}
LEGACY_CHILD_CONDITION_SLUGS = {
    "newborn-screening-followup",
    "child-not-responding",
    "child-late-talking",
    "child-device-followup",
}
