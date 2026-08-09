"""
Seed content for the assistant suite.

IMPORTANT — this is starting content, not clinically signed off. Every entry here
is written to be safe and generic, and is expected to be reviewed and replaced by
the Audiology, SLP and Early Intervention teams via the admin screens. The
assistants can only ever repeat what lives in these tables, so the quality of the
department's answers is exactly the quality of this content.

Structure mirrors the ORM models so scripts/seed.py can insert rows directly.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import AgeBand, AgentType, TherapyDomain, Vertical

# ---------------------------------------------------------------------------
# Bookable services
# ---------------------------------------------------------------------------

SERVICES: list[dict[str, Any]] = [
    {
        "code": "AUD_ASSESSMENT",
        "name": "Comprehensive Audiological Assessment",
        "vertical": Vertical.AUDIOLOGY.value,
        "duration_minutes": 60,
        "description": (
            "Full hearing evaluation for adults and older children, usually combining "
            "pure tone audiometry, speech audiometry and middle-ear testing."
        ),
        "preparation": (
            "Avoid loud noise exposure for 16 hours before the test. Bring any previous "
            "hearing reports. Let us know if you have a cold or blocked ear on the day."
        ),
        "documents_required": ["Photo ID (Aadhaar or equivalent)", "Previous audiogram if any", "Referral letter if you have one"],
        "report_turnaround": "Same day for the audiogram; detailed report within 3 working days",
    },
    {
        "code": "PAED_HEARING",
        "name": "Paediatric Hearing Assessment",
        "vertical": Vertical.AUDIOLOGY.value,
        "duration_minutes": 75,
        "description": (
            "Age-appropriate hearing testing for infants and young children using "
            "behavioural and objective methods."
        ),
        "preparation": (
            "Try to keep the child awake on the journey so they settle for testing. For "
            "infants, feeding just before the appointment helps. Bring a favourite toy."
        ),
        "documents_required": ["Child's birth certificate", "Immunisation card", "Newborn screening result if available"],
        "report_turnaround": "Within 3 working days",
    },
    {
        "code": "NEWBORN_SCREEN",
        "name": "Newborn Hearing Screening",
        "vertical": Vertical.AUDIOLOGY.value,
        "duration_minutes": 30,
        "description": (
            "Quick, painless screening for newborns and young infants using otoacoustic "
            "emissions, with automated brainstem response if needed."
        ),
        "preparation": "Best done when the baby is asleep or calm, ideally just after a feed.",
        "documents_required": ["Birth certificate or hospital discharge summary"],
        "report_turnaround": "Result explained on the day",
    },
    {
        "code": "HEARING_AID_TRIAL",
        "name": "Hearing Aid Trial and Fitting",
        "vertical": Vertical.AUDIOLOGY.value,
        "duration_minutes": 90,
        "description": (
            "Selection, fitting and real-ear verification of hearing aids, including "
            "counselling on daily use and care."
        ),
        "preparation": "Bring a recent audiogram (within 6 months) and a family member if possible.",
        "documents_required": ["Recent audiogram", "Photo ID", "Disability certificate if you have one"],
        "report_turnaround": "Fitting summary issued on the day",
    },
    {
        "code": "VESTIBULAR",
        "name": "Balance and Vestibular Assessment",
        "vertical": Vertical.AUDIOLOGY.value,
        "duration_minutes": 90,
        "description": "Assessment of dizziness and balance difficulty using vestibular test batteries.",
        "preparation": (
            "Avoid a heavy meal for 2 hours before. Do not wear eye make-up. Check with "
            "your doctor before stopping any medication — do not stop on your own."
        ),
        "documents_required": ["Photo ID", "List of current medications", "Referral letter if you have one"],
        "report_turnaround": "Within 5 working days",
    },
    {
        "code": "SLP_ASSESSMENT",
        "name": "Speech and Language Assessment",
        "vertical": Vertical.SLP.value,
        "duration_minutes": 60,
        "description": (
            "Evaluation of speech sounds, language understanding and expression, fluency "
            "and voice, leading to a therapy plan."
        ),
        "preparation": (
            "Note down examples of what the person says and any words that are hard to "
            "follow. A short home video of them talking is very useful."
        ),
        "documents_required": ["Photo ID", "School or previous therapy reports if any"],
        "report_turnaround": "Within 5 working days",
    },
    {
        "code": "SLP_THERAPY",
        "name": "Speech-Language Therapy Session",
        "vertical": Vertical.SLP.value,
        "duration_minutes": 45,
        "description": "Individual therapy session following an assessment and agreed therapy plan.",
        "preparation": "Bring the home practice diary and any materials your therapist gave you.",
        "documents_required": ["Therapy card"],
        "report_turnaround": "Progress reviewed every 10 sessions",
    },
    {
        "code": "SWALLOW_ASSESSMENT",
        "name": "Feeding and Swallowing Assessment",
        "vertical": Vertical.SLP.value,
        "duration_minutes": 60,
        "description": (
            "Assessment of feeding and swallowing difficulty, including positioning, "
            "consistency tolerance and safety."
        ),
        "preparation": (
            "Do not feed for about an hour before so the person is ready to eat. Bring the "
            "foods and the cup or bottle normally used at home."
        ),
        "documents_required": ["Photo ID", "Recent weight record", "Relevant medical reports"],
        "report_turnaround": "Within 3 working days",
    },
    {
        "code": "EI_SESSION",
        "name": "Early Intervention Session",
        "vertical": Vertical.EARLY_INTERVENTION.value,
        "duration_minutes": 60,
        "description": (
            "Parent-and-child session building play-based communication, listening and "
            "developmental skills, with coaching for the caregiver."
        ),
        "preparation": "A parent or primary caregiver must attend the whole session.",
        "documents_required": ["Child's ID", "Previous assessment reports"],
        "report_turnaround": "Reviewed monthly",
    },
    {
        "code": "PARENT_COUNSELLING",
        "name": "Parent Counselling Session",
        "vertical": Vertical.EARLY_INTERVENTION.value,
        "duration_minutes": 45,
        "description": (
            "Structured counselling for parents and families after a diagnosis, covering "
            "what it means day to day and the options available."
        ),
        "preparation": "Bring your questions written down — it is easy to forget them in the room.",
        "documents_required": ["Child's assessment report"],
        "report_turnaround": "Summary shared on request",
    },
    {
        "code": "AVT_SESSION",
        "name": "Auditory-Verbal Therapy Session",
        "vertical": Vertical.EARLY_INTERVENTION.value,
        "duration_minutes": 45,
        "description": (
            "Listening and spoken-language therapy for children using hearing aids or "
            "cochlear implants, coaching the parent as the main teacher."
        ),
        "preparation": "Bring the child's hearing devices fully charged, with spare batteries.",
        "documents_required": ["Device details", "Recent audiogram"],
        "report_turnaround": "Reviewed every 3 months",
    },
]


# ---------------------------------------------------------------------------
# Clinicians (placeholder roster — replace with the real department list)
# ---------------------------------------------------------------------------

CLINICIANS: list[dict[str, Any]] = [
    {"name": "Dr. A. Raghavan", "designation": "Senior Audiologist", "vertical": Vertical.AUDIOLOGY.value},
    {"name": "Ms. S. Kalpana", "designation": "Audiologist", "vertical": Vertical.AUDIOLOGY.value},
    {"name": "Mr. T. Venkatesh", "designation": "Speech-Language Pathologist", "vertical": Vertical.SLP.value},
    {"name": "Ms. R. Divya", "designation": "Speech-Language Pathologist", "vertical": Vertical.SLP.value},
    {"name": "Ms. P. Meenakshi", "designation": "Early Intervention Specialist", "vertical": Vertical.EARLY_INTERVENTION.value},
]

# Which services each clinician covers, used to generate slots.
CLINICIAN_SERVICES: dict[str, list[str]] = {
    "Dr. A. Raghavan": ["AUD_ASSESSMENT", "VESTIBULAR", "HEARING_AID_TRIAL"],
    "Ms. S. Kalpana": ["NEWBORN_SCREEN", "PAED_HEARING", "AUD_ASSESSMENT"],
    "Mr. T. Venkatesh": ["SLP_ASSESSMENT", "SLP_THERAPY", "SWALLOW_ASSESSMENT"],
    "Ms. R. Divya": ["SLP_ASSESSMENT", "SLP_THERAPY"],
    "Ms. P. Meenakshi": ["EI_SESSION", "PARENT_COUNSELLING", "AVT_SESSION"],
}

DEFAULT_LOCATION = "Audiology Block, NIEPMD, Muttukadu"

# Slot generation window and daily start times (department local time).
SLOT_GENERATION_DAYS = 28
SLOT_START_HOURS: tuple[int, ...] = (9, 10, 11, 14, 15, 16)


# ---------------------------------------------------------------------------
# Knowledge base — the enquiry assistant's entire vocabulary of facts
# ---------------------------------------------------------------------------

_ALL_AGENTS: list[str] = []  # empty agent_types = visible to every assistant

KNOWLEDGE_ENTRIES: list[dict[str, Any]] = [
    {
        "slug": "working-hours",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Working hours",
        "question": "What are the department's working hours?",
        "answer": (
            "The Department of Speech, Hearing and Communication is open Monday to "
            "Friday, 9:00 AM to 5:00 PM. We are closed on Saturdays, Sundays and "
            "government holidays. Registration for walk-in enquiries closes at 3:30 PM, "
            "so please arrive before then if you do not have an appointment."
        ),
        "keywords": ["timing", "timings", "hours", "open", "close", "closed", "saturday", "sunday", "holiday", "walk in"],
        "priority": 10,
    },
    {
        "slug": "location-directions",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Location and how to reach us",
        "question": "Where is NIEPMD and how do I reach the department?",
        "answer": (
            "NIEPMD is at East Coast Road, Muttukadu, Kovalam Post, Chennai 603112, about "
            "30 km south of Chennai city on the ECR. Government and private buses towards "
            "Mahabalipuram stop at Muttukadu. The Department of Speech, Hearing and "
            "Communication is in the Audiology Block; the reception desk at the main gate "
            "will direct you. Free parking is available inside the campus."
        ),
        "keywords": ["location", "address", "reach", "directions", "bus", "parking", "where", "map", "ecr", "muttukadu"],
        "priority": 9,
    },
    {
        "slug": "registration-process",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Registration process",
        "question": "How do I register as a new patient?",
        "answer": (
            "New patients register at the front desk of the Audiology Block. You will need "
            "one photo ID (Aadhaar or equivalent) and, for a child, the birth certificate. "
            "Registration takes about 15 minutes and you will be given a patient card that "
            "you should bring to every visit. Booking an appointment in advance is "
            "recommended, as walk-in slots depend on availability that day."
        ),
        "keywords": ["register", "registration", "new patient", "first visit", "patient card", "enrol"],
        "priority": 8,
    },
    {
        "slug": "fees-concessions",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Fees and concessions",
        "question": "What are the charges for assessments and therapy?",
        "answer": (
            "NIEPMD is a national institute under the Government of India and charges are "
            "kept nominal. Concessions and exemptions apply for persons with a disability "
            "certificate and for families below the poverty line. Because fee schedules are "
            "revised periodically, please confirm the current amount with the front desk on "
            "044-2452-0639 before your visit — I do not hold live fee figures."
        ),
        "keywords": ["fee", "fees", "cost", "charge", "charges", "price", "payment", "free", "concession", "bpl", "money"],
        "priority": 8,
    },
    {
        "slug": "documents-to-bring",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Documents to bring",
        "question": "What documents should I bring for my appointment?",
        "answer": (
            "For every visit bring your patient card and one photo ID. For a child's first "
            "visit also bring the birth certificate and immunisation card. If you have any "
            "of the following, bring them too: previous hearing or speech reports, newborn "
            "screening results, a referral letter, a disability certificate, and a list of "
            "current medications. Specific tests may need extra documents — ask me about "
            "the particular service and I can tell you."
        ),
        "keywords": ["document", "documents", "bring", "papers", "id", "proof", "aadhaar", "certificate", "carry"],
        "priority": 9,
    },
    {
        "slug": "report-turnaround",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "When reports are ready",
        "question": "How long does it take to get my report?",
        "answer": (
            "Timelines depend on the test. A basic audiogram is usually explained to you on "
            "the same day, with the detailed report ready within 3 working days. Speech and "
            "language assessment reports take up to 5 working days, and balance assessment "
            "reports up to 5 working days. Reports can be collected from the department or, "
            "on request, sent to your registered email."
        ),
        "keywords": ["report", "reports", "result", "results", "audiogram", "how long", "ready", "collect", "email"],
        "priority": 7,
    },
    {
        "slug": "first-visit-duration",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "How long a visit takes",
        "question": "How much time should I set aside for the first visit?",
        "answer": (
            "Plan for about half a day for a first visit. Registration takes around 15 "
            "minutes, and the assessment itself runs from 30 minutes for a newborn "
            "screening to 90 minutes for a balance or hearing-aid appointment. Waiting time "
            "varies with the day's load, so arriving 15 minutes before your slot helps."
        ),
        "keywords": ["how long", "duration", "time", "wait", "waiting", "half day", "first visit"],
        "priority": 5,
    },
    {
        "slug": "referral-needed",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Whether a referral is needed",
        "question": "Do I need a doctor's referral to come here?",
        "answer": (
            "A referral is not compulsory — you can approach the department directly. If you "
            "already have a referral letter from an ENT surgeon, paediatrician or another "
            "hospital, bring it, because it helps us plan the right tests on the first "
            "visit. Some specialised investigations may still need an ENT opinion, which we "
            "can arrange internally."
        ),
        "keywords": ["referral", "refer", "letter", "doctor", "ent", "need", "compulsory", "directly"],
        "priority": 6,
    },
    {
        "slug": "hearing-aid-provision",
        "vertical": Vertical.AUDIOLOGY.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Hearing aid provision",
        "question": "Can I get a hearing aid here and is it subsidised?",
        "answer": (
            "Yes. After a hearing assessment confirms that an aid is appropriate, the "
            "department carries out selection, trial, fitting and verification. Subsidised "
            "and free aids may be available through government schemes such as ADIP for "
            "eligible applicants, which usually requires a disability certificate and an "
            "income certificate. Eligibility is confirmed case by case, so please discuss it "
            "at your fitting appointment."
        ),
        "keywords": ["hearing aid", "aid", "aids", "machine", "device", "subsidy", "adip", "free", "scheme", "fitting"],
        "priority": 7,
    },
    {
        "slug": "cochlear-implant-pathway",
        "vertical": Vertical.AUDIOLOGY.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Cochlear implant pathway",
        "question": "Does the department do cochlear implant assessment?",
        "answer": (
            "The department carries out the audiological part of cochlear implant candidacy "
            "evaluation and provides the pre- and post-implant therapy that is essential to "
            "the outcome, including auditory-verbal therapy. The surgery itself is done at a "
            "partner hospital. Whether an implant is suitable for a particular person is a "
            "team decision made after a full evaluation — it cannot be judged from symptoms "
            "or a single test."
        ),
        "keywords": ["cochlear", "implant", "ci", "surgery", "candidacy", "mapping", "switch on"],
        "priority": 6,
    },
    {
        "slug": "therapy-frequency-general",
        "vertical": Vertical.SLP.value,
        "agent_types": _ALL_AGENTS,
        "topic": "How often therapy sessions run",
        "question": "How often will we need to come for speech therapy?",
        "answer": (
            "Most families attend once or twice a week to begin with, and each session runs "
            "about 45 minutes. The actual frequency is decided by the treating therapist "
            "after assessment, based on the person's needs and how much practice is "
            "happening at home. Home practice between sessions matters as much as the "
            "sessions themselves."
        ),
        "keywords": ["how often", "frequency", "weekly", "sessions", "therapy", "many", "week", "duration"],
        "priority": 6,
    },
    {
        "slug": "teletherapy-availability",
        "vertical": Vertical.SLP.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Online and follow-up options",
        "question": "Can therapy or follow-up happen online?",
        "answer": (
            "Some follow-up and parent-guidance sessions can be conducted online for "
            "families who live far away, once an in-person assessment has been completed. "
            "First assessments need to be in person. Ask your therapist whether online "
            "follow-up is suitable in your case, and confirm availability with the front "
            "desk."
        ),
        "keywords": ["online", "teletherapy", "video", "remote", "distance", "far", "travel", "follow up"],
        "priority": 4,
    },
    {
        "slug": "early-intervention-programme",
        "vertical": Vertical.EARLY_INTERVENTION.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Early Intervention programme",
        "question": "What does the Early Intervention programme involve?",
        "answer": (
            "Early Intervention works with children in the first years of life and, "
            "crucially, with their parents. Sessions are play-based and build listening, "
            "communication and developmental skills, while coaching the caregiver to carry "
            "the same activities into daily routines at home. A parent or primary caregiver "
            "is expected to attend the whole session, because most of the child's learning "
            "happens at home between visits."
        ),
        "keywords": ["early intervention", "programme", "program", "ei", "play", "parent", "caregiver", "toddler"],
        "priority": 6,
    },
    {
        "slug": "school-support-letter",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "School and examination support",
        "question": "Can you provide a letter for my child's school or exams?",
        "answer": (
            "Yes. Once an assessment is complete, the department can issue a report "
            "describing the child's hearing or communication needs and the classroom "
            "accommodations that would help, such as preferential seating or extra time. "
            "Requests for examination concessions usually need a recent assessment, so book "
            "a review if the last one was more than a year ago."
        ),
        "keywords": ["school", "exam", "exams", "letter", "classroom", "concession", "accommodation", "teacher", "board"],
        "priority": 5,
    },
    {
        "slug": "disability-certificate",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Disability certificate and UDID",
        "question": "How do I get a disability certificate for hearing loss?",
        "answer": (
            "A disability certificate is issued by a designated government medical board, "
            "not by this department directly. What we provide is the audiological evaluation "
            "the board relies on. The certificate and UDID card are what make you eligible "
            "for scheme benefits such as subsidised hearing aids and travel concessions. "
            "Our staff can explain the current process for your district — call "
            "044-2452-0639."
        ),
        "keywords": ["disability", "certificate", "udid", "percentage", "board", "benefits", "scheme", "concession"],
        "priority": 6,
    },
    {
        "slug": "interpreter-language-support",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Language support",
        "question": "Which languages can I be seen in?",
        "answer": (
            "Staff in the department speak Tamil, English and Hindi. If you are more "
            "comfortable in another language, mention it when booking and we will try to "
            "arrange support. You are also welcome to bring a family member to help with "
            "interpretation."
        ),
        "keywords": ["language", "tamil", "english", "hindi", "interpreter", "translate", "sign language"],
        "priority": 4,
    },
    {
        "slug": "accessibility-campus",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Campus accessibility",
        "question": "Is the campus wheelchair accessible?",
        "answer": (
            "Yes. NIEPMD is designed for accessibility, with ramps, accessible toilets and "
            "lift access in the clinical blocks, and wheelchairs available at reception on "
            "request. If the person attending has significant mobility or multiple "
            "disabilities, tell us when booking so we can allocate a ground-floor room and "
            "extra time."
        ),
        "keywords": ["wheelchair", "accessible", "accessibility", "ramp", "lift", "disabled", "mobility", "toilet"],
        "priority": 5,
    },
    {
        "slug": "emergency-contact",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Urgent problems outside working hours",
        "question": "What do I do if there is an urgent problem at night or on a holiday?",
        "answer": (
            "The department is an outpatient service and is not staffed outside working "
            "hours. For sudden hearing loss, heavy bleeding or discharge from the ear, "
            "severe pain, or any breathing or swallowing emergency, go to the nearest "
            "hospital emergency department or ENT casualty immediately rather than waiting "
            "for us to open. Call us on 044-2452-0639 during working hours for follow-up."
        ),
        "keywords": ["emergency", "urgent", "night", "holiday", "sudden", "bleeding", "severe", "casualty", "after hours"],
        "priority": 10,
    },
    {
        "slug": "appointment-change-policy",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": [AgentType.SCHEDULING.value, AgentType.ENQUIRY.value],
        "topic": "Changing or missing an appointment",
        "question": "What happens if I need to change or I miss my appointment?",
        "answer": (
            "You can reschedule or cancel free of charge, and doing it early frees the slot "
            "for another family. Have your booking reference ready and I can move it for "
            "you. If you miss a slot without cancelling, the appointment lapses and you will "
            "need to book again — there is no penalty, but the next available date may be "
            "later."
        ),
        "keywords": ["reschedule", "cancel", "miss", "missed", "change", "late", "postpone", "no show", "penalty"],
        "priority": 7,
    },
    {
        "slug": "who-should-attend",
        "vertical": Vertical.DEPARTMENT.value,
        "agent_types": _ALL_AGENTS,
        "topic": "Who should come along",
        "question": "Should someone come with me or with my child?",
        "answer": (
            "For a child, a parent or primary caregiver must attend — much of the session "
            "involves coaching you, not only testing the child. For adults, bringing a "
            "family member is helpful, especially for hearing-aid appointments, because a "
            "familiar voice is used during fitting and there is a lot to remember "
            "afterwards."
        ),
        "keywords": ["who", "attend", "accompany", "parent", "family", "alone", "come with", "caregiver"],
        "priority": 5,
    },
]


# ---------------------------------------------------------------------------
# Hearing screening protocols (Audiology) — one per age band
# ---------------------------------------------------------------------------

SCREENING_PROTOCOLS: list[dict[str, Any]] = [
    {
        "age_band": AgeBand.NEWBORN.value,
        "name": "Newborn Hearing Screening (0–6 months)",
        "summary": (
            "A quick, painless check done while the baby is settled or asleep. A soft probe "
            "in the ear canal plays gentle sounds and measures the ear's response. Nothing "
            "is inserted deeply and the baby feels no discomfort. Screening tells us which "
            "babies need a fuller assessment — it is not a diagnosis."
        ),
        "test_codes": ["OAE", "ABR", "Tympanometry"],
        "referral_criteria": [
            "No clear otoacoustic emission response in one or both ears on repeat screening",
            "Automated brainstem response result marked 'refer' in either ear",
            "Any stay in neonatal intensive care of more than 48 hours",
            "Family history of permanent childhood hearing loss",
            "Birth weight under 1500 g, jaundice needing exchange transfusion, or infection such as meningitis",
            "Craniofacial differences involving the ear, or a syndrome associated with hearing loss",
        ],
        "timeline": (
            "Ideally screened before 1 month of age, diagnostic assessment completed by 3 "
            "months if referred, and intervention begun by 6 months. A 'refer' result on "
            "the first screen is repeated before any further step."
        ),
        "preparation": (
            "Bring the baby when they are likely to sleep — just after a feed works best. "
            "Feed and change the baby before the appointment. Allow about 30 minutes."
        ),
    },
    {
        "age_band": AgeBand.INFANT_TODDLER.value,
        "name": "Infant and Toddler Hearing Assessment (6 months–2.5 years)",
        "summary": (
            "At this age hearing is checked by watching how the child responds to sound. In "
            "visual reinforcement audiometry the child learns that turning towards a sound "
            "makes a toy light up, which lets us map the softest sounds they respond to. "
            "Objective tests are added when behavioural testing is not conclusive."
        ),
        "test_codes": ["VRA", "OAE", "Tympanometry", "ABR"],
        "referral_criteria": [
            "No response at expected sound levels on visual reinforcement audiometry",
            "Not turning to name or to everyday sounds by 9 months",
            "No babbling by 9 months, or babbling that has stopped",
            "Repeated middle-ear fluid or ear infections",
            "Parental concern about hearing, which on its own is grounds for full assessment",
        ],
        "timeline": (
            "Assessment within 4 weeks of concern being raised. If middle-ear fluid is "
            "found, hearing is rechecked after 6 to 12 weeks before any conclusion is drawn."
        ),
        "preparation": (
            "Schedule around the child's nap so they are alert but calm. Bring a favourite "
            "toy and a snack. Allow about 75 minutes; testing is done in short bursts."
        ),
    },
    {
        "age_band": AgeBand.PRESCHOOL.value,
        "name": "Preschool Hearing Assessment (2.5–5 years)",
        "summary": (
            "Hearing is tested as a game — the child puts a block in a bucket or presses a "
            "button each time they hear a sound. This play-based approach gives ear-specific "
            "results in most children of this age, and is combined with middle-ear testing."
        ),
        "test_codes": ["Play Audiometry", "OAE", "Speech Detection Threshold", "Tympanometry"],
        "referral_criteria": [
            "No reliable response at screening levels in either ear",
            "Speech that is much less clear than expected for the child's age",
            "Frequent requests for repetition, or turning up the television",
            "Delay in following simple spoken instructions without gestures",
            "Recurrent ear infections or persistent middle-ear fluid",
        ],
        "timeline": (
            "Assessment within 4 weeks of concern. Where speech delay is also present, a "
            "speech-language assessment is arranged alongside rather than after."
        ),
        "preparation": (
            "Explain at home that it is a listening game, not an injection or anything that "
            "hurts. A well-rested child tests far better. Allow about 60 minutes."
        ),
    },
    {
        "age_band": AgeBand.SCHOOL_AGE.value,
        "name": "School-Age Hearing Assessment (5 years and above)",
        "summary": (
            "From about five years, children can usually do standard adult-style testing: "
            "raising a hand or pressing a button to tones through headphones, plus repeating "
            "words to check how well speech is understood. Listening in background noise is "
            "added when classroom difficulty is the main concern."
        ),
        "test_codes": ["PTA", "Speech Audiometry", "OAE", "SPIN", "Tympanometry"],
        "referral_criteria": [
            "Hearing thresholds outside the normal range in either ear",
            "Difficulty following the teacher despite normal thresholds, which may indicate a listening difficulty needing further testing",
            "A drop in academic performance or reported inattention in class",
            "Persistent ringing in the ears, or ear pain and discharge",
            "Any sudden change in hearing, which is treated as urgent",
        ],
        "timeline": (
            "Routine assessment within 4 weeks. Any sudden hearing change is seen "
            "urgently — the same day where possible — rather than through routine booking."
        ),
        "preparation": (
            "Avoid loud noise such as headphones at high volume for 16 hours before. Bring "
            "previous reports and any school observations. Allow about 60 minutes."
        ),
    },
]


# ---------------------------------------------------------------------------
# Speech-Language Pathology guidelines
# ---------------------------------------------------------------------------

THERAPY_GUIDELINES: list[dict[str, Any]] = [
    {
        "domain": TherapyDomain.LANGUAGE_DELAY.value,
        "age_band": AgeBand.INFANT_TODDLER.value,
        "title": "Early language development (6 months–2.5 years)",
        "summary": (
            "In the second year most children move from babble to single words and then to "
            "joining two words together. Understanding usually runs ahead of speaking, so a "
            "child who follows instructions but says little is a different picture from one "
            "who does neither."
        ),
        "milestones": [
            "By 9 months: babbles strings of sounds, turns to their name",
            "By 12 months: uses one or two words meaningfully, points to ask for things",
            "By 18 months: uses 10 to 20 words, follows a simple instruction without gestures",
            "By 24 months: uses around 50 words and starts joining two words, e.g. 'more milk'",
            "By 30 months: uses short phrases, is understood by familiar adults much of the time",
        ],
        "home_activities": [
            "Narrate what you are doing during routines — bathing, cooking, dressing — in short, clear phrases",
            "Pause and wait after you ask something, giving a full five seconds for a response before helping",
            "Copy and slightly extend what the child says: if they say 'car', reply 'big car' or 'car going'",
            "Share picture books daily, naming what you both point at rather than reading every word",
            "Reduce background television and radio, which makes speech much harder to pick out",
        ],
        "red_flags": [
            "No babbling by 9 months, or babbling that has stopped",
            "No single words by 18 months",
            "Loss of words or skills the child previously had",
            "Not responding to their name or to everyday sounds",
            "Little interest in interacting with familiar people",
        ],
        "typical_frequency": "Usually once or twice weekly initially, with heavy emphasis on parent-led home practice",
    },
    {
        "domain": TherapyDomain.LANGUAGE_DELAY.value,
        "age_band": AgeBand.PRESCHOOL.value,
        "title": "Preschool language development (2.5–5 years)",
        "summary": (
            "Between two and five, sentences lengthen, grammar fills in, and children begin "
            "to use language to explain, ask and tell stories. Speech becomes clear enough "
            "for people outside the family to understand."
        ),
        "milestones": [
            "By 3 years: uses three- to four-word sentences, is understood by unfamiliar adults about three quarters of the time",
            "By 3 years: answers simple 'what' and 'where' questions",
            "By 4 years: tells a short story about something that happened, uses 'because' and 'and'",
            "By 4 years: follows two-step instructions",
            "By 5 years: speech is clear, grammar is largely adult-like, can retell a story in order",
        ],
        "home_activities": [
            "Ask open questions that need more than yes or no — 'what happened next?' rather than 'did you like it?'",
            "Play pretend games with a sequence, such as shopping or doctor, which pushes longer sentences",
            "Recast rather than correct: if the child says 'him goed', reply 'yes, he went to school'",
            "Sort and name things into groups — animals, food, clothes — to build vocabulary networks",
            "Read the same favourite book repeatedly and leave gaps for the child to fill in the line",
        ],
        "red_flags": [
            "Still using mostly single words at 3 years",
            "Unfamiliar adults cannot understand the child at 4 years",
            "Cannot follow a simple two-step instruction at 4 years",
            "Frustration or behaviour difficulty that appears to stem from not being understood",
            "Any loss of previously acquired language",
        ],
        "typical_frequency": "Usually once or twice weekly, reviewed every 10 sessions",
    },
    {
        "domain": TherapyDomain.ARTICULATION.value,
        "age_band": None,
        "title": "Speech sound development and clarity",
        "summary": (
            "Speech sounds arrive in a broadly predictable order, and some are simply late "
            "to develop. 'R', 'S', 'L', 'TH' and blends often settle only by six or seven "
            "years, so a five-year-old mispronouncing 'r' is usually within normal range "
            "while one whose speech cannot be understood at all is not."
        ),
        "milestones": [
            "By 3 years: p, b, m, n, t, d, w, h are generally accurate",
            "By 4 years: k, g, f, y are generally accurate; speech mostly intelligible to strangers",
            "By 5 years: sh, ch, j, v and most blends are developing",
            "By 6–7 years: r, s, z, l, th are typically mastered",
        ],
        "home_activities": [
            "Model the correct sound clearly rather than asking the child to repeat it many times",
            "Emphasise the target sound in ordinary conversation — a slight stretch, not a lecture",
            "Play listening games first: can the child hear the difference between the two sounds when you say them?",
            "Practise in short bursts, five to ten minutes, rather than long sessions",
            "Never mock or let siblings imitate the error; it reliably reduces how much the child talks",
        ],
        "red_flags": [
            "Speech cannot be understood by people outside the family at 4 years",
            "Sounds are left off the ends of words consistently beyond 3 years",
            "The child is aware of and distressed by their speech",
            "Speech is markedly harder to follow than that of same-age peers",
            "Any sudden deterioration in speech clarity",
        ],
        "typical_frequency": "Usually weekly, with short daily home practice",
    },
    {
        "domain": TherapyDomain.FLUENCY.value,
        "age_band": None,
        "title": "Stammering and fluency",
        "summary": (
            "Many children pass through a phase of bumpy speech between two and five years "
            "as language develops quickly, and it often resolves. Stammering that persists "
            "beyond six months, runs in the family, or is accompanied by visible effort or "
            "avoidance is worth assessing early — early therapy works well."
        ),
        "milestones": [
            "Brief, occasional repetition of whole words between 2 and 4 years is common and usually passes",
            "By 5 years most children speak fluently most of the time",
            "Persisting beyond 6 months from onset makes spontaneous resolution less likely",
        ],
        "home_activities": [
            "Slow your own speech rate slightly and add pauses — this helps far more than telling the child to slow down",
            "Never say 'slow down', 'take a breath' or 'start again'; it increases the effort and the fear",
            "Keep natural eye contact and respond to what the child said, not how they said it",
            "Protect a few minutes of unhurried one-to-one talking time each day with no competing siblings",
            "Reduce time pressure and rapid-fire questioning at mealtimes",
        ],
        "red_flags": [
            "Stammering that has continued for more than 6 months",
            "Visible physical tension, facial grimacing or struggle to get words out",
            "The child avoids words, situations or speaking altogether",
            "The child shows frustration or distress about their speech",
            "A family history of stammering",
        ],
        "typical_frequency": "Usually weekly, often with a parent-focused programme for younger children",
    },
    {
        "domain": TherapyDomain.VOICE.value,
        "age_band": None,
        "title": "Voice care and hoarseness",
        "summary": (
            "A hoarse, breathy or strained voice can follow vocal overuse, frequent "
            "shouting, or throat irritation. Persistent hoarseness in a child or adult "
            "always needs an ENT examination of the vocal folds before voice therapy starts, "
            "because therapy depends on knowing what is causing it."
        ),
        "milestones": [
            "A child's voice should be clear and comfortable, not routinely hoarse",
            "Hoarseness after a cold should settle within about two weeks",
            "Voice should not tire or fade over the course of a day",
        ],
        "home_activities": [
            "Drink water regularly through the day so the throat is not dry",
            "Reduce shouting, screaming and talking over noise — move closer instead of raising volume",
            "Avoid throat clearing and hard coughing, which irritate the vocal folds; sip water instead",
            "Build in short voice rest periods, particularly after sport or a noisy day",
            "Avoid smoke exposure entirely",
        ],
        "red_flags": [
            "Hoarseness lasting more than 2 to 3 weeks without a cold",
            "Any difficulty breathing, or noisy breathing alongside voice change",
            "Pain on speaking or swallowing",
            "Complete loss of voice",
            "A lump in the neck, or coughing up blood — needs urgent medical review",
        ],
        "typical_frequency": "Weekly voice therapy after ENT examination confirms it is appropriate",
    },
    {
        "domain": TherapyDomain.FEEDING_SWALLOWING.value,
        "age_band": None,
        "title": "Feeding and swallowing support",
        "summary": (
            "Feeding difficulty ranges from fussy eating to unsafe swallowing where food or "
            "liquid enters the airway. Because the risks include chest infection and poor "
            "weight gain, anything suggesting unsafe swallowing needs assessment quickly "
            "rather than home strategies."
        ),
        "milestones": [
            "By 6 months: begins taking smooth pureed food from a spoon",
            "By 9 months: manages soft lumps and finger foods",
            "By 12 months: drinks from a cup, eats a range of textures",
            "By 18–24 months: chews and manages most family foods",
        ],
        "home_activities": [
            "Seat the person upright with feet supported and head in a neutral position, never reclined",
            "Keep mealtimes calm and free of distraction, and allow enough time without rushing",
            "Offer small mouthfuls and check the mouth is empty before the next one",
            "Follow only the textures and consistencies your therapist has advised — do not experiment",
            "Keep the person upright for 20 to 30 minutes after eating",
        ],
        "red_flags": [
            "Coughing, choking or a wet, gurgly voice during or after eating and drinking",
            "Recurrent chest infections or unexplained fever",
            "Poor weight gain or weight loss",
            "Mealtimes routinely taking more than 30 to 40 minutes, or severe distress",
            "Any colour change or breathing difficulty while feeding — seek emergency care immediately",
        ],
        "typical_frequency": "Assessment first, then a plan reviewed frequently; urgent cases are prioritised",
    },
    {
        "domain": TherapyDomain.AUDITORY_VERBAL.value,
        "age_band": None,
        "title": "Listening and spoken language with hearing devices",
        "summary": (
            "For a child using hearing aids or a cochlear implant, consistent device use and "
            "rich everyday talk are what drive spoken-language progress. Auditory-verbal "
            "therapy coaches the parent to build listening into ordinary routines, because "
            "the parent, not the therapist, provides most of the child's input."
        ),
        "milestones": [
            "Device worn during all waking hours — this is the single strongest predictor of progress",
            "Within weeks of fitting: begins to notice and turn towards everyday sounds",
            "Progresses from detecting sound, to telling sounds apart, to identifying, to understanding",
            "Spoken language grows from the point of consistent device use, not from the child's birth date",
        ],
        "home_activities": [
            "Do a listening check on the device every morning and keep spare batteries ready",
            "Sit close and on the same level, on the side of the better-hearing ear",
            "Talk through routines constantly, giving the child something to listen to all day",
            "Use sound-rich play — animal noises, vehicles, instruments — and pair each sound with its name",
            "Cut background noise during talking and reading; competing noise is especially costly for these children",
        ],
        "red_flags": [
            "The child refuses the device or removes it repeatedly",
            "Whistling, no sound, or intermittent sound from the device — get it checked promptly",
            "No progress in listening responses over several weeks of consistent use",
            "A sudden change in how the child responds to sound",
            "Ear discharge or pain around a mould or implant site",
        ],
        "typical_frequency": "Usually weekly parent-and-child sessions, reviewed every 3 months",
    },
]


# ---------------------------------------------------------------------------
# Parent counselling resources (Early Intervention)
# ---------------------------------------------------------------------------

COUNSELLING_RESOURCES: list[dict[str, Any]] = [
    {
        "slug": "new-diagnosis",
        "topic": "Coming to terms with a new diagnosis",
        "age_band": None,
        "summary": (
            "Hearing that your child has a hearing or communication difficulty is hard news, "
            "and most parents describe shock, grief and a stretch of not knowing what to do "
            "first. Those reactions are normal and they do not make you a poor parent. What "
            "helps most in the early weeks is doing a few concrete things rather than trying "
            "to absorb everything at once."
        ),
        "talking_points": [
            "A diagnosis names something that was already there — it does not make the child different from who they were yesterday",
            "You do not have to understand the whole road now; the next appointment is enough to aim for",
            "Both parents may react very differently and at different speeds, and that mismatch is common rather than a problem",
            "Children pick up on tension more than on words, so looking after yourself is part of looking after them",
        ],
        "reassurance": [
            "Early support makes a real difference, and you are already acting early by asking",
            "You are not expected to become an expert; the team's job is to guide you step by step",
            "Many families have stood exactly where you are and gone on to manage well",
        ],
        "next_steps": [
            "Write down your questions as they occur to you and bring the list to the next appointment",
            "Ask for a parent counselling session — it is a scheduled appointment, not a favour",
            "Ask to be connected to a parent support group; hearing from another family helps in a way clinical advice cannot",
        ],
        "keywords": ["diagnosed", "diagnosis", "just found out", "shock", "lost", "grief", "news", "cope", "coping", "accept", "overwhelmed"],
    },
    {
        "slug": "parental-guilt",
        "topic": "Guilt and self-blame",
        "age_band": None,
        "summary": (
            "Almost every parent asks whether they caused this or missed it earlier. Most "
            "childhood hearing loss has causes entirely outside a parent's control — genetic "
            "factors, infections, events around birth — and in a good number of cases no "
            "cause is ever identified. Blaming yourself is understandable, and it is also not "
            "supported by the facts."
        ),
        "talking_points": [
            "Noticing a concern and acting on it is the opposite of neglect",
            "Hearing difficulties are often not visible early, which is exactly why screening programmes exist",
            "A cause is not always found, and not knowing the cause does not change what helps the child",
            "Guilt tends to drain the energy the child actually needs from you",
        ],
        "reassurance": [
            "This is not a punishment and it is not your fault",
            "You brought your child for help, which is the thing that changes outcomes",
            "Questions about cause are worth asking a clinician directly rather than carrying alone",
        ],
        "next_steps": [
            "Ask the audiologist what is and is not known about the cause in your child's case",
            "Book a parent counselling session if the guilt is persistent or affecting your sleep",
            "Tell the team if you feel low most days — support for you is part of the child's care",
        ],
        "keywords": ["guilt", "guilty", "blame", "my fault", "did i", "punishment", "should have", "missed", "cause", "why"],
    },
    {
        "slug": "explaining-to-family",
        "topic": "Explaining to family and dealing with advice",
        "age_band": None,
        "summary": (
            "Relatives and neighbours often mean well and still say unhelpful things, from "
            "'he will grow out of it' to suggestions of unproven remedies. A short, confident "
            "explanation that you repeat consistently works better than trying to win every "
            "argument."
        ),
        "talking_points": [
            "One or two clear sentences are enough: what the child needs and what helps",
            "Explain the device in practical terms — it helps them hear so they can learn to talk",
            "Children copy the attitude around them; treating the device as ordinary makes them treat it as ordinary",
            "You are allowed to decline advice politely without justifying your decisions",
        ],
        "reassurance": [
            "You do not owe anyone a detailed medical explanation of your child",
            "Family resistance usually softens once they see the child making progress",
            "Disagreement between relatives is common and does not mean you are handling it badly",
        ],
        "next_steps": [
            "Ask the team for a simple written explanation you can share with relatives and teachers",
            "Bring a sceptical family member to an appointment so they hear it from the clinician",
            "Agree one consistent line with your partner so the family hears the same message",
        ],
        "keywords": ["family", "relatives", "explain", "in laws", "neighbours", "advice", "stigma", "grow out", "remedy", "school", "teacher"],
    },
    {
        "slug": "device-acceptance",
        "topic": "When a child resists a hearing device",
        "age_band": AgeBand.INFANT_TODDLER.value,
        "summary": (
            "Young children very commonly pull out hearing aids in the first weeks. This is "
            "usually about novelty, fit or comfort rather than refusal, and it almost always "
            "improves with a consistent, low-drama routine. Consistent wearing matters a great "
            "deal, so it is worth persisting and asking for help early."
        ),
        "talking_points": [
            "Start with short, positive periods during a favourite activity and build up gradually",
            "Put the device on during something enjoyable, not during a struggle or a nappy change",
            "Stay calm and matter-of-fact when it comes out; a big reaction makes it a game",
            "Repeated pulling out can signal a poorly fitting mould or discomfort — that is fixable",
        ],
        "reassurance": [
            "Nearly every family goes through this phase, and most get past it within weeks",
            "It is not a sign the child dislikes hearing or that the device is wrong",
            "Small daily gains count; you are not failing if it is not all day yet",
        ],
        "next_steps": [
            "Keep a simple daily log of wearing time to discuss at the next visit",
            "Book a review if the mould looks tight, the ear is red, or there is whistling",
            "Ask about retention aids such as clips, caps or double-sided tape",
        ],
        "keywords": ["hearing aid", "removes", "pulls out", "refuses", "wont wear", "device", "mould", "uncomfortable", "whistling", "battery"],
    },
    {
        "slug": "worry-about-future",
        "topic": "Worries about school, speech and the future",
        "age_band": None,
        "summary": (
            "Parents almost always want to know whether their child will speak, study and "
            "live independently. No one can honestly predict an individual child's outcome, "
            "and anyone who offers a confident prediction should be treated with caution. What "
            "is known is that early, consistent support and involved parents are strongly "
            "associated with better outcomes."
        ),
        "talking_points": [
            "Outcomes vary widely and depend on many factors, several of which you can influence",
            "Consistent device use, therapy attendance and everyday talk at home are the levers in your hands",
            "Many children with hearing loss attend mainstream school with the right support in place",
            "Progress is better judged over months than week to week",
        ],
        "reassurance": [
            "Asking about the future is normal, not pessimistic",
            "You do not have to decide about schooling today",
            "The team will review progress regularly and adjust the plan as you go",
        ],
        "next_steps": [
            "Ask the therapist what specific goals are being worked on this term",
            "Ask about classroom accommodations and support letters when school approaches",
            "Book a review appointment to discuss educational options rather than deciding alone",
        ],
        "keywords": ["future", "will he", "will she", "school", "study", "normal", "speak", "talk", "independent", "job", "marriage", "worried", "prognosis"],
    },
    {
        "slug": "managing-therapy-load",
        "topic": "Managing appointments alongside everything else",
        "age_band": None,
        "summary": (
            "Therapy, travel, work and other children add up, and many families reach a point "
            "of exhaustion. Home practice does not need to be a separate lesson — the most "
            "effective practice is folded into routines you are already doing, which is also "
            "the only version that survives a busy week."
        ),
        "talking_points": [
            "Ten focused minutes daily beats an hour once a week",
            "Bath time, meals and the journey to school are all language practice without extra time cost",
            "Missing an occasional session does not undo progress — tell the team rather than dropping out",
            "Sharing the load between caregivers keeps it sustainable",
        ],
        "reassurance": [
            "Feeling stretched is not a sign you are failing your child",
            "Your therapist would rather adjust the plan than have you burn out",
            "Progress continues even in weeks where little formal practice happens",
        ],
        "next_steps": [
            "Tell your therapist honestly how much practice time is realistic and plan around that",
            "Ask whether some follow-up can be done online to cut travel",
            "Ask about grouping appointments on the same day where possible",
        ],
        "keywords": ["tired", "exhausted", "busy", "travel", "far", "distance", "work", "manage", "time", "expensive", "burnout", "siblings"],
    },
    {
        "slug": "newborn-refer-result",
        "topic": "When a newborn screening says 'refer'",
        "age_band": AgeBand.NEWBORN.value,
        "summary": (
            "A 'refer' result on newborn screening does not mean your baby has hearing loss. "
            "It means the screen did not get a clear response and needs repeating. Fluid or "
            "debris in the ear canal after birth, or a restless baby, are common and harmless "
            "reasons for an unclear result."
        ),
        "talking_points": [
            "'Refer' means 'test again', not 'diagnosed'",
            "Many babies who refer on the first screen pass on the repeat",
            "The repeat is just as quick and painless as the first",
            "If hearing loss is confirmed, starting support early is exactly why screening happens at birth",
        ],
        "reassurance": [
            "This is a routine next step, not an emergency",
            "You have not done anything wrong, and nothing you did caused this result",
            "Whatever the outcome, there is a clear pathway and you will not be left to work it out alone",
        ],
        "next_steps": [
            "Book the repeat screening within the timeframe the department gave you — do not let it slip",
            "Bring the baby when they are likely to sleep, ideally just after a feed",
            "Bring the discharge summary and any screening paperwork from the birth hospital",
        ],
        "keywords": ["refer", "referred", "failed", "newborn", "screening", "not pass", "baby", "birth", "repeat", "retest"],
    },
    {
        "slug": "sibling-and-self-care",
        "topic": "Siblings and looking after yourself",
        "age_band": None,
        "summary": (
            "When one child needs a lot of appointments, siblings often notice the imbalance "
            "and parents often put themselves last. Both matter to how the family copes over "
            "the long run, and both are legitimate things to raise with the team."
        ),
        "talking_points": [
            "Siblings cope better with a simple honest explanation than with being shielded",
            "Small amounts of protected one-to-one time with each child go a long way",
            "Siblings can be involved in play-based practice, which helps both children",
            "Your own low mood or sleep loss is a clinical matter worth mentioning, not a weakness",
        ],
        "reassurance": [
            "Attending to your own needs is not selfish; it is what makes the long haul possible",
            "Sibling jealousy is normal and does not mean the family is struggling",
            "You are allowed to ask for support for yourself, not only for the child",
        ],
        "next_steps": [
            "Tell the team if you are consistently low, anxious or not sleeping",
            "Ask about parent support groups where families share practical strategies",
            "Involve siblings in one home activity a week so they are part of it rather than outside it",
        ],
        "keywords": ["sibling", "siblings", "brother", "sister", "jealous", "myself", "self care", "depressed", "low", "anxious", "sleep", "alone", "support group"],
    },
]
