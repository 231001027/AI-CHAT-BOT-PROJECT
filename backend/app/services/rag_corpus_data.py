"""
Bundled NIEPMD knowledge for the public assistant RAG corpus.

Indexed into Qdrant by ``scripts/seed_rag_corpus.py``.
"""

from __future__ import annotations

RAG_CORPUS_DOCUMENTS: list[dict[str, object]] = [
    {
        "slug": "hearing_loss_adults",
        "title": "Adult hearing concerns — patient guidance",
        "category": "guideline",
        "test_tags": ["PTA", "SPEECH", "HEARING"],
        "content": """\
NIEPMD Audiology and Speech Department — Adult hearing guidance

When to seek help
Difficulty hearing in quiet or noisy places, asking people to repeat, turning the \
television up, or missing parts of conversations may indicate a hearing change. A \
Pure Tone Audiometry (PTA) test is the first step to measure hearing thresholds \
accurately. Speech audiometry may follow to see how well speech is understood.

What happens at assessment
The audiologist tests each ear separately in a sound-treated room using headphones. \
The appointment usually takes about thirty minutes. No fasting is required. Tell \
staff if you have ear pain, discharge, or a cold on the day of testing.

Noise and tinnitus
Ringing or buzzing (tinnitus) and sensitivity to loud sounds are common reasons to \
book an assessment. An audiologist can discuss management and whether further \
vestibular testing is needed for dizziness or balance problems.

Next steps
You can start the Take Test pathway on this website for guided questions, or call \
the department to book an appointment. Only a qualified audiologist or doctor can \
diagnose a condition after examining you and reviewing test results.
""",
    },
    {
        "slug": "child_hearing_speech",
        "title": "Child hearing and speech — early signs",
        "category": "guideline",
        "test_tags": ["OAE", "ABR", "BOA", "VRA", "SPEECH"],
        "content": """\
NIEPMD Audiology and Speech Department — Child hearing and speech guidance

Early signs in infants and young children
Not startling to loud sounds, not turning toward voices, delayed babbling, limited \
response when called from another room, or delayed first words may relate to hearing \
or communication development. Early identification supports speech and language growth.

Recommended assessments by age
Newborns and infants may have Otoacoustic Emissions (OAE) and Auditory Brainstem \
Response (ABR) screening. Behavioural Observation Audiometry (BOA) is used for very \
young infants. Visual Reinforcement Audiometry (VRA) suits toddlers and preschool \
children. School-age children typically have Pure Tone Audiometry and speech \
audiometry.

Speech and language delay
Speech delay does not always mean hearing loss, but hearing should be checked first. \
A combined audiology and speech-language assessment helps identify whether the \
concern is hearing-related, language development, or both.

Parent guidance
Respond calmly and book a paediatric hearing assessment rather than waiting. Share \
concerns about responsiveness, ear infections, or family history of hearing loss \
with the clinician. Guardian consent is required when registering a child for care.
""",
    },
    {
        "slug": "tinnitus_balance",
        "title": "Tinnitus, dizziness and balance",
        "category": "guideline",
        "test_tags": ["VNG", "VEMP", "PTA"],
        "content": """\
NIEPMD Audiology and Speech Department — Tinnitus and balance guidance

Tinnitus
Persistent ringing, buzzing, or hissing in the ears is called tinnitus. Common \
contributors include noise exposure, stress, and inner-ear changes. An audiologist \
can assess severity and discuss sound therapy, counselling, and safe listening habits.

Dizziness and vertigo
A spinning sensation, unsteadiness, or balance problems may relate to the inner ear. \
Videonystagmography (VNG) and vestibular evoked myogenic potentials (VEMP) help \
evaluate vestibular function when recommended by the clinical team. Sudden severe \
dizziness with hearing change warrants urgent medical review.

Management approach
Assessment begins with hearing tests such as PTA. The audiologist explains which \
further tests apply and coordinates referral to ENT when needed. Avoid loud \
environments without ear protection.

Important
This guidance is educational only. It is not a diagnosis. Personal advice requires \
examination by a qualified audiologist or doctor.
""",
    },
    {
        "slug": "speech_language_voice",
        "title": "Speech, language and voice concerns",
        "category": "guideline",
        "test_tags": ["SPEECH", "PTA"],
        "content": """\
NIEPMD Audiology and Speech Department — Speech and language guidance

Common concerns
Delayed talking, unclear speech, stuttering, voice strain, swallowing difficulty, \
or regression in communication skills may need a speech-language assessment. Hearing \
should be checked because undetected hearing loss can affect speech development.

Assessment pathway
A speech-language pathologist evaluates articulation, language comprehension, voice \
quality, and fluency. When hearing involvement is possible, audiology testing is \
arranged in parallel. For school-age children, teachers may notice listening \
difficulty in class — a hearing test can clarify whether hearing contributes to \
learning challenges.

Support and therapy
Therapy plans depend on the assessment findings. Early intervention is recommended \
for young children. Families receive practical strategies for home and school \
communication.

Booking
Use the Take Test flow on this website or contact the department to schedule a \
combined hearing and speech evaluation.
""",
    },
    {
        "slug": "test_catalog_reference",
        "title": "Hearing and speech tests — department reference",
        "category": "sop",
        "test_tags": ["PTA", "OAE", "ABR", "TYMP", "SPEECH", "VNG"],
        "content": """\
NIEPMD Audiology and Speech Department — Test reference for patients

Pure Tone Audiometry (PTA)
Measures hearing thresholds at different pitches using tones presented through \
headphones. Used from about five years of age upward. Takes roughly thirty minutes.

Speech Audiometry
Measures ability to detect and understand speech. Complements PTA for functional \
hearing assessment.

Otoacoustic Emissions (OAE)
Records sounds produced by the inner ear in response to stimulation. Used for \
newborn screening and cochlear checks at all ages. Quick and non-invasive.

Auditory Brainstem Response (ABR)
Measures electrical responses from the auditory nerve and brainstem. Often used \
when behavioural testing is difficult, including infants. Performed while resting.

Tympanometry
Objective test of middle-ear function and eardrum mobility. Helpful when ear \
infections, fluid, or blockage are suspected.

Tympanometry and immittance testing support decisions about medical referral.

General preparation
Inform staff about ear pain, discharge, recent cold, or prior ear surgery. No \
fasting is usually required for standard hearing tests. The audiologist explains \
each test on the day and answers questions specific to your situation.
""",
    },
]
