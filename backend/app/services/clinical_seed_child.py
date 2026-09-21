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
    # 1. Language Development & Comprehension
    _q(
        "child-speech-language-issues",
        "fewer_words_shorter_sentences",
        "Compared with other children of the same age, does your child use fewer words or much shorter sentences?",
        1,
        is_entry=True,
    ),
    _q(
        "child-speech-language-issues",
        "trouble_following_directions",
        "Does your child have trouble following simple spoken directions unless you also use gestures?",
        2,
    ),
    _q(
        "child-speech-language-issues",
        "point_cry_pull_instead_of_words",
        "Does your child often point, cry, or pull someone's hand instead of using words to communicate?",
        3,
    ),
    _q(
        "child-speech-language-issues",
        "lost_words_or_skills",
        "Has your child lost words or communication skills that they used regularly before?",
        4,
    ),
    _q(
        "child-speech-language-issues",
        "difficulty_conversation",
        "Does your child have difficulty answering questions or keeping a short conversation going?",
        5,
    ),
    _q(
        "child-speech-language-issues",
        "leaves_out_grammar_words",
        "Does your child leave out small grammar words such as 'is' or 'the', or often use sentence grammar incorrectly?",
        6,
    ),
    _q(
        "child-speech-language-issues",
        "trouble_naming_objects",
        "Does your child have trouble naming familiar objects and often say things like 'that thing' instead?",
        7,
    ),
    # 2. Childhood Fluency & Stuttering
    _q(
        "child-stuttering-fluency",
        "repeats_sound_or_syllable",
        "Does your child repeat a sound or syllable several times, such as 'b-b-b-ball'?",
        1,
        is_entry=True,
    ),
    _q(
        "child-stuttering-fluency",
        "holds_sound_long",
        "Does your child hold a sound for a long time, such as 'ssss-snake'?",
        2,
    ),
    _q(
        "child-stuttering-fluency",
        "gets_stuck_no_sound",
        "Does your child sometimes get stuck while trying to speak, with no sound coming out?",
        3,
    ),
    _q(
        "child-stuttering-fluency",
        "eye_blink_facial_tension",
        "Do you notice eye blinking, facial tension, or other movements when your child is having difficulty speaking?",
        4,
    ),
    _q(
        "child-stuttering-fluency",
        "frustrated_or_avoids_talking",
        "Does your child become frustrated, cover their mouth, or avoid talking when speech is difficult?",
        5,
    ),
    _q(
        "child-stuttering-fluency",
        "speech_fast_uneven",
        "Does your child's speech sometimes sound very fast, uneven, or as though words run together?",
        6,
    ),
    # 3. Speech Sound Clarity & Articulation
    _q(
        "child-speech-clarity-issues",
        "others_hard_to_understand",
        "Do people who aren't used to your child's speech have trouble understanding what they say?",
        1,
        is_entry=True,
    ),
    _q(
        "child-speech-clarity-issues",
        "leave_out_or_replace_sounds",
        "Does your child leave out or replace sounds in familiar words, such as saying 'tat' instead of 'cat'?",
        2,
    ),
    _q(
        "child-speech-clarity-issues",
        "family_repeats_what_child_says",
        "Do you or other family members often need to repeat what your child says or explain it to others?",
        3,
    ),
    _q(
        "child-speech-clarity-issues",
        "leaves_out_syllables",
        "Does your child leave out syllables in longer words, such as saying 'nana' for 'banana'?",
        4,
    ),
    _q(
        "child-speech-clarity-issues",
        "searching_mouth_position",
        "When repeating a word, does your child appear to search for the right mouth position or make unusual mouth movements?",
        5,
    ),
    _q(
        "child-speech-clarity-issues",
        "late_babbling_or_first_words",
        "Did your child begin babbling or using first words later than expected for their age?",
        6,
    ),
    # 4. Pediatric Voice & Resonance
    _q(
        "child-voice-issues",
        "voice_hoarse_rough_breathy",
        "Does your child's voice regularly sound hoarse, rough, or breathy?",
        1,
        is_entry=True,
    ),
    _q(
        "child-voice-issues",
        "voice_weak_after_talking",
        "Does your child's voice become weak, strained, or disappear after talking or crying for a while?",
        2,
    ),
    _q(
        "child-voice-issues",
        "throat_sore_after_speaking",
        "Does your child complain that their throat feels sore, tight, or uncomfortable after speaking?",
        3,
    ),
    _q(
        "child-voice-issues",
        "shouts_or_harsh_sounds",
        "Does your child frequently shout, scream, or make harsh sounds while playing?",
        4,
    ),
    _q(
        "child-voice-issues",
        "unusual_voice_over_2_weeks",
        "Has the unusual voice quality continued for more than two weeks?",
        5,
    ),
    _q(
        "child-voice-issues",
        "unusually_nasal_when_well",
        "When your child isn't sick, do they still sound unusually nasal or as though their nose is blocked?",
        6,
    ),
    # 5. Pediatric Feeding, Swallowing & Hearing Responsiveness
    _q(
        "child-feeding-swallowing-issues",
        "cough_choke_gag_eating",
        "Does your child cough, choke, or gag while eating or drinking, especially with liquids?",
        1,
        is_entry=True,
    ),
    _q(
        "child-feeding-swallowing-issues",
        "food_spill_lips_or_nose",
        "Does food or liquid spill from your child's lips or come through the nose while swallowing?",
        2,
    ),
    _q(
        "child-feeding-swallowing-issues",
        "meals_over_30_40_minutes",
        "Do your child's usual meals often take more than 30 to 40 minutes to finish?",
        3,
    ),
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

_CHILD_SPEECH_LANGUAGE_TESTS = [
    {
        "test_code": "ALD",
        "test_name": "Assessment of Language Development (ALD)",
        "reason_text": "Checks understanding and use of language against age-expected milestones.",
        "display_order": 1,
    },
    {
        "test_code": "REELS",
        "test_name": "Receptive-Expressive Emergent Language Scale (REELS)",
        "reason_text": "Assesses early receptive and expressive language in infants and toddlers.",
        "display_order": 2,
    },
    {
        "test_code": "COMDEALL",
        "test_name": "COMDEALL Developmental Checklist",
        "reason_text": "Screens broader developmental and communication milestones, often used when Autism Spectrum concerns are suspected.",
        "display_order": 3,
    },
    {
        "test_code": "LPT",
        "test_name": "Linguistic Profile Test (LPT)",
        "reason_text": "Profiles language across sounds, word forms, sentence structure, and meaning; used with older children as well.",
        "display_order": 4,
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
        "Language development assessments used for child speech and language concerns.",
        _CHILD_SPEECH_LANGUAGE_TESTS,
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
