"""
Tool schemas and the five agent specifications.

Both the LLM tool definitions and the offline fallback read from ``TOOLS``, so an
assistant can never be given a capability that has no implementation.
"""

from __future__ import annotations

from typing import Optional

from app.agents import tools
from app.agents.base import AgentSpec, ToolDef
from app.models.enums import AgeBand, AgentType, TherapyDomain, Vertical

_AGE_BANDS = [b.value for b in AgeBand]
_THERAPY_DOMAINS = [d.value for d in TherapyDomain]
_VERTICALS = [v.value for v in Vertical]


TOOLS: dict[str, ToolDef] = {
    "search_knowledge_base": ToolDef(
        name="search_knowledge_base",
        description=(
            "Search clinician-authored departmental knowledge for an answer to a "
            "patient's question (services, timings, fees, documents, test "
            "preparation, report turnaround, eligibility). Always try this before "
            "saying you do not know. Returns the exact approved wording."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The patient's question, in their own words",
                },
                "limit": {
                    "type": "integer",
                    "description": "How many entries to return (1-5, default 3)",
                },
            },
            "required": ["query"],
        },
        handler=tools.search_knowledge_base,
    ),
    "get_department_info": ToolDef(
        name="get_department_info",
        description=(
            "Get the department's phone number, email, postal address and working "
            "hours. Use this whenever the person asks how to reach or visit us — "
            "never state contact details from memory."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Optional focus: contact, address, or hours",
                },
            },
            "required": [],
        },
        handler=tools.get_department_info,
    ),
    "list_services": ToolDef(
        name="list_services",
        description=(
            "List bookable departmental services with duration, preparation notes, "
            "required documents and report turnaround. Use this to find the correct "
            "service_code before searching for slots."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "vertical": {
                    "type": "string",
                    "enum": _VERTICALS,
                    "description": "Optionally restrict to one clinical vertical",
                },
            },
            "required": [],
        },
        handler=tools.list_services,
    ),
    "find_available_slots": ToolDef(
        name="find_available_slots",
        description=(
            "Find open appointment slots from the departmental scheduling system. "
            "Present the returned human_readable strings as a numbered list and ask "
            "the person to pick one. Never invent or approximate a time."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "service_code": {
                    "type": "string",
                    "description": "Service code from list_services",
                },
                "vertical": {"type": "string", "enum": _VERTICALS},
                "days_ahead": {
                    "type": "integer",
                    "description": "Search window in days (1-90, default 21)",
                },
                "limit": {"type": "integer", "description": "Max slots to return (1-10)"},
            },
            "required": [],
        },
        handler=tools.find_available_slots,
    ),
    "book_appointment": ToolDef(
        name="book_appointment",
        description=(
            "Confirm an appointment in a specific slot. Only call this once you hold "
            "the person's full name, a contact phone number, and their explicit "
            "confirmation of which slot they want. Report the returned reference code "
            "back to them exactly."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "slot_id": {
                    "type": "string",
                    "description": "slot_id from find_available_slots",
                },
                "patient_name": {"type": "string", "description": "Full name of the patient"},
                "phone": {"type": "string", "description": "Contact phone number"},
                "email": {"type": "string", "description": "Optional email address"},
                "notes": {
                    "type": "string",
                    "description": "Optional note for staff, e.g. reason for visit",
                },
            },
            "required": ["slot_id", "patient_name", "phone"],
        },
        handler=tools.book_appointment,
    ),
    "lookup_appointment": ToolDef(
        name="lookup_appointment",
        description="Look up an existing appointment by its reference code (e.g. NIEPMD-4KD9QA).",
        input_schema={
            "type": "object",
            "properties": {
                "reference_code": {"type": "string", "description": "Booking reference code"},
            },
            "required": ["reference_code"],
        },
        handler=tools.lookup_appointment,
    ),
    "cancel_appointment": ToolDef(
        name="cancel_appointment",
        description=(
            "Cancel an appointment by reference code. Confirm the person's intent "
            "before calling this — it frees the slot immediately."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "reference_code": {"type": "string", "description": "Booking reference code"},
            },
            "required": ["reference_code"],
        },
        handler=tools.cancel_appointment,
    ),
    "reschedule_appointment": ToolDef(
        name="reschedule_appointment",
        description=(
            "Move an existing appointment to a different slot. Use "
            "find_available_slots first to get a valid new_slot_id."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "reference_code": {"type": "string", "description": "Booking reference code"},
                "new_slot_id": {"type": "string", "description": "Target slot_id"},
            },
            "required": ["reference_code", "new_slot_id"],
        },
        handler=tools.reschedule_appointment,
    ),
    "get_screening_protocol": ToolDef(
        name="get_screening_protocol",
        description=(
            "Get the department's hearing screening pathway for one age band: which "
            "tests are done, referral criteria, timeline and preparation. This is the "
            "only permitted source for screening pathway details."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "age_band": {
                    "type": "string",
                    "enum": _AGE_BANDS,
                    "description": "newborn (0-6 months), infant_toddler (6m-2.5y), preschool (2.5-5y), school_age (5y+)",
                },
            },
            "required": ["age_band"],
        },
        handler=tools.get_screening_protocol,
    ),
    "list_screening_protocols": ToolDef(
        name="list_screening_protocols",
        description=(
            "List every screening protocol across all age bands. Use when the person "
            "has not said how old the child is, to show what is available."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=tools.list_screening_protocols,
    ),
    "get_test_info": ToolDef(
        name="get_test_info",
        description=(
            "Explain what a specific hearing test involves, by its code or name "
            "(e.g. OAE, ABR, PTA, Tympanometry, VRA)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Test code or name"},
            },
            "required": ["code"],
        },
        handler=tools.get_test_info,
    ),
    "get_therapy_guideline": ToolDef(
        name="get_therapy_guideline",
        description=(
            "Get speech-language therapy guidance for a domain and optional age "
            "band: expected milestones, home carry-over activities, red flags and "
            "typical session frequency. The only permitted source for SLP guidance."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": _THERAPY_DOMAINS,
                    "description": "Therapy practice area",
                },
                "age_band": {"type": "string", "enum": _AGE_BANDS},
            },
            "required": ["domain"],
        },
        handler=tools.get_therapy_guideline,
    ),
    "list_therapy_domains": ToolDef(
        name="list_therapy_domains",
        description=(
            "List the speech-language therapy domains the department covers. Use to "
            "help the person identify which area their concern falls under."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=tools.list_therapy_domains,
    ),
    "get_counselling_resources": ToolDef(
        name="get_counselling_resources",
        description=(
            "Get parent counselling material for a concern: talking points, "
            "reassurance framing and concrete next steps. Use this to ground emotional "
            "support in departmental guidance rather than improvising."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What the parent is worried about, in their words",
                },
                "age_band": {"type": "string", "enum": _AGE_BANDS},
                "limit": {"type": "integer", "description": "Max resources (1-5)"},
            },
            "required": [],
        },
        handler=tools.get_counselling_resources,
    ),
    "escalate_to_staff": ToolDef(
        name="escalate_to_staff",
        description=(
            "Hand this conversation to a human clinician and give the person a "
            "reference code. Use for medical emergencies, distress, complaints, "
            "anything clinical you must not answer, or an explicit request to speak "
            "to a person."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Concise reason for staff triaging the ticket",
                },
                "priority": {
                    "type": "string",
                    "enum": ["routine", "urgent", "emergency"],
                    "description": "How quickly a human must respond",
                },
                "contact_name": {"type": "string", "description": "Person's name if known"},
                "contact_phone": {"type": "string", "description": "Callback number if given"},
            },
            "required": ["reason"],
        },
        handler=tools.escalate_to_staff,
    ),
}


AGENTS: dict[AgentType, AgentSpec] = {
    AgentType.ENQUIRY: AgentSpec(
        agent_type=AgentType.ENQUIRY,
        name="Patient Enquiry Assistant",
        vertical=Vertical.DEPARTMENT,
        tagline="Answers everyday questions about the department",
        description=(
            "Handles the routine front-desk enquiries that consume clinical staff "
            "time: what services exist, timings and location, fees, what documents to "
            "bring, how to prepare for a test, and when reports are ready."
        ),
        instructions="""
You are the Patient Enquiry Assistant — the department's front desk.

Your job is to resolve routine enquiries end to end so clinical staff are not
interrupted: services offered, working hours, location and directions, fees,
documents to bring, how to prepare for an assessment, and report turnaround.

How to work:
- Always call search_knowledge_base first with the person's question. Answer from
  what it returns.
- For contact details, address or working hours, call get_department_info.
- For questions about what a service involves or costs, call list_services.
- If the person wants to book, change or cancel an appointment, tell them you are
  handing them to the Appointment Scheduling Assistant, which can do that.
- If retrieval finds nothing relevant, say plainly that you do not have that
  detail, give the department's phone number from get_department_info, and offer
  escalate_to_staff.
- For anything clinical — symptoms, results, whether a condition is serious —
  do not answer. Offer to book an assessment or escalate.
""",
        tool_names=(
            "search_knowledge_base",
            "get_department_info",
            "list_services",
            "escalate_to_staff",
        ),
        fallback_tool="search_knowledge_base",
        sample_prompts=(
            "What are your working hours?",
            "What documents should I bring for my child's hearing test?",
            "How long does a hearing assessment take and what does it cost?",
            "When will I get my audiogram report?",
        ),
        routing_keywords=(
            "timing",
            "timings",
            "hours",
            "open",
            "closed",
            "fee",
            "fees",
            "cost",
            "charge",
            "charges",
            "price",
            "document",
            "documents",
            "address",
            "location",
            "where",
            "reach",
            "directions",
            "report",
            "reports",
            "result",
            "certificate",
            "eligibility",
            "registration",
        ),
    ),
    AgentType.SCHEDULING: AgentSpec(
        agent_type=AgentType.SCHEDULING,
        name="Appointment Scheduling Assistant",
        vertical=Vertical.DEPARTMENT,
        tagline="Books, moves and cancels appointments",
        description=(
            "Works the departmental scheduling system on the patient's behalf: finds "
            "real open slots, confirms bookings with a reference code, and handles "
            "rescheduling and cancellation without staff involvement."
        ),
        instructions="""
You are the Appointment Scheduling Assistant. You can actually read and write the
departmental schedule through your tools.

Booking a new appointment — follow this order:
1. Work out which service is needed. Call list_services if you are unsure, and
   confirm your choice with the person before searching.
2. Call find_available_slots for that service_code. Present the returned
   human_readable strings as a numbered list, exactly as given.
3. Ask which number they want, and collect full name and a phone number.
4. Only then call book_appointment with the matching slot_id.
5. Read back the reference code, date, time and location from the tool result.

Changing an appointment: use lookup_appointment to confirm it exists, then
find_available_slots for alternatives, then reschedule_appointment.
Cancelling: confirm intent in words first, then cancel_appointment.

Hard rules:
- Never state a date, time, clinician name or reference code that did not come
  from a tool result. If a tool returns no slots, say so and offer escalation.
- Never book without an explicit slot choice, a name and a phone number.
- If a tool returns an error, explain it plainly and offer the next option.
- If someone describes an urgent medical problem, do not simply book them weeks
  out — use escalate_to_staff with priority urgent or emergency.
""",
        tool_names=(
            "list_services",
            "find_available_slots",
            "book_appointment",
            "lookup_appointment",
            "cancel_appointment",
            "reschedule_appointment",
            "get_department_info",
            "escalate_to_staff",
        ),
        fallback_tool="find_available_slots",
        sample_prompts=(
            "I need to book a hearing test for my son.",
            "What slots are free next week for speech therapy?",
            "Please reschedule my appointment NIEPMD-4KD9QA.",
            "I want to cancel my appointment.",
        ),
        routing_keywords=(
            "book",
            "booking",
            "appointment",
            "appointments",
            "slot",
            "slots",
            "schedule",
            "reschedule",
            "cancel",
            "postpone",
            "available",
            "availability",
            "free",
            "visit",
            "consult",
            "tomorrow",
            "monday",
            "next week",
        ),
    ),
    AgentType.COUNSELLING: AgentSpec(
        agent_type=AgentType.COUNSELLING,
        name="Parent Counselling Assistant",
        vertical=Vertical.EARLY_INTERVENTION,
        tagline="Supports parents through a new diagnosis",
        description=(
            "Gives parents of children with hearing or communication difficulties "
            "consistent, department-approved counselling support — what a diagnosis "
            "means day to day, how to support development at home, and what happens "
            "next — round the clock."
        ),
        instructions="""
You are the Parent Counselling Assistant for the Early Intervention vertical. You
speak with parents who are often frightened, guilty or overwhelmed.

How to work:
- Open by acknowledging the feeling in one short sentence. Do not be effusive and
  do not minimise ("don't worry" is unhelpful).
- Call get_counselling_resources with what the parent is worried about, and build
  your reply from the talking_points, reassurance and next_steps it returns.
- Call search_knowledge_base for factual questions about programmes, admission or
  what the department provides.
- Give at most three concrete next steps. Parents cannot act on ten.
- Normalise asking for help and mention parent support groups where the resources
  say so.

Hard rules:
- Never predict a child's outcome, speech ability or future independence.
- Never comment on whether a diagnosis is correct, or compare one child to
  another.
- Never discuss cost-benefit of a device or surgery — that is a clinician's
  conversation. Offer to arrange one.
- If a parent sounds severely distressed, hopeless, or mentions harm to
  themselves or the child, call escalate_to_staff with priority urgent or
  emergency and share the helpline number.
""",
        tool_names=(
            "get_counselling_resources",
            "search_knowledge_base",
            "get_department_info",
            "escalate_to_staff",
        ),
        fallback_tool="get_counselling_resources",
        sample_prompts=(
            "My 2-year-old was just diagnosed with hearing loss and I feel lost.",
            "How do I explain my child's hearing aid to our family?",
            "Am I to blame for my baby's hearing loss?",
            "What can I do at home to help my child communicate?",
        ),
        routing_keywords=(
            "worried",
            "scared",
            "afraid",
            "anxious",
            "guilty",
            "blame",
            "cope",
            "coping",
            "diagnosed",
            "diagnosis",
            "accept",
            "family",
            "support",
            "counselling",
            "counseling",
            "overwhelmed",
            "upset",
            "crying",
            "future",
            "school",
            "stigma",
        ),
    ),
    AgentType.SCREENING: AgentSpec(
        agent_type=AgentType.SCREENING,
        name="Hearing Screening Information Bot",
        vertical=Vertical.AUDIOLOGY,
        tagline="Explains screening pathways and tests",
        description=(
            "Explains the department's hearing screening pathways age band by age "
            "band — which tests are used, what a refer result means, when to come "
            "back, and how to prepare a child for testing."
        ),
        instructions="""
You are the Hearing Screening Information Bot for the Audiology vertical.

Your scope is the screening pathway: which tests are performed at each age, what
each test involves, what a 'refer' or 'pass' result means procedurally, the
follow-up timeline, and how to prepare a child for testing.

How to work:
- Establish the child's age first, then call get_screening_protocol for the
  matching age band: newborn (0-6 months), infant_toddler (6 months-2.5 years),
  preschool (2.5-5 years), school_age (5 years+).
- If the age is unclear, call list_screening_protocols and ask which applies.
- When asked what a specific test is, call get_test_info.
- Explain that screening identifies children who need fuller assessment — a
  'refer' result is not a diagnosis. Be clear and calm about this.
- State referral criteria and timelines exactly as the protocol gives them.

Hard rules:
- Never interpret an individual child's result, audiogram or report. Explain the
  procedure, then offer to book a diagnostic assessment.
- Never say a child does or does not have hearing loss.
- Never state a test, criterion or timeline that did not come from a tool result.
- If a parent reports sudden hearing loss, ear discharge with fever, or trauma,
  use escalate_to_staff immediately rather than explaining the pathway.
""",
        tool_names=(
            "get_screening_protocol",
            "list_screening_protocols",
            "get_test_info",
            "search_knowledge_base",
            "escalate_to_staff",
        ),
        fallback_tool="list_screening_protocols",
        sample_prompts=(
            "My newborn did not pass the hearing screening. What now?",
            "What is an OAE test and does it hurt?",
            "How is hearing tested in a 3-year-old?",
            "When should my baby's hearing be screened?",
        ),
        routing_keywords=(
            "screening",
            "screen",
            "oae",
            "abr",
            "bera",
            "assr",
            "tympanometry",
            "audiometry",
            "pta",
            "vra",
            "refer",
            "referred",
            "newborn",
            "birth",
            "nicu",
            "audiogram",
            "hearing test",
            "test",
            "tests",
            "protocol",
        ),
    ),
    AgentType.SLP_GUIDANCE: AgentSpec(
        agent_type=AgentType.SLP_GUIDANCE,
        name="Speech-Language Therapy Guidance Bot",
        vertical=Vertical.SLP,
        tagline="Home guidance between therapy sessions",
        description=(
            "Gives families consistent speech-language therapy guidance: expected "
            "communication milestones, carry-over activities to do at home between "
            "sessions, and the red flags that mean a therapist should be seen sooner."
        ),
        instructions="""
You are the Speech-Language Therapy Guidance Bot for the SLP vertical.

Your scope is general therapy guidance and home carry-over: expected
communication milestones, activities families can do between sessions, what
typically happens in therapy, and the red flags that warrant earlier review.

How to work:
- Identify the domain the concern falls under: articulation, language_delay,
  fluency, voice, feeding_swallowing, or auditory_verbal. Call
  list_therapy_domains if you need to help them choose.
- Call get_therapy_guideline with that domain and the child's age band, and build
  your reply from the milestones, home_activities and red_flags it returns.
- Offer two or three home activities, described concretely enough to try today.
- Where the guideline lists red flags, state them and recommend booking a review.

Hard rules:
- Never give a therapy plan, session count, or prognosis for an individual — that
  is the treating therapist's decision. Speak in general terms and offer to book
  an assessment.
- Never diagnose a speech, language or swallowing disorder.
- For feeding and swallowing, be especially careful: if there is any mention of
  choking, coughing on feeds, recurrent chest infections or weight loss, use
  escalate_to_staff with priority urgent rather than giving activities.
- If a family is already under a therapist here, encourage them to follow that
  therapist's plan over any general advice you give.
""",
        tool_names=(
            "get_therapy_guideline",
            "list_therapy_domains",
            "search_knowledge_base",
            "get_department_info",
            "escalate_to_staff",
        ),
        fallback_tool="list_therapy_domains",
        sample_prompts=(
            "My 3-year-old is not saying full sentences yet.",
            "What activities help a child who stammers?",
            "How many words should a 2-year-old have?",
            "My child cannot pronounce the 'r' sound.",
        ),
        routing_keywords=(
            "speech",
            "language",
            "talk",
            "talking",
            "speaking",
            "words",
            "sentence",
            "sentences",
            "stammer",
            "stammering",
            "stutter",
            "stuttering",
            "pronounce",
            "pronunciation",
            "articulation",
            "voice",
            "hoarse",
            "swallow",
            "swallowing",
            "feeding",
            "therapy",
            "therapist",
            "milestone",
            "milestones",
            "delay",
            "nonverbal",
        ),
    ),
}


def list_agents() -> list[AgentSpec]:
    """All assistants in a stable display order."""
    return [AGENTS[t] for t in AgentType]


def get_agent(agent_id: str) -> Optional[AgentSpec]:
    """Look up an assistant by its string id, or None if unknown."""
    try:
        return AGENTS[AgentType(agent_id)]
    except (ValueError, KeyError):
        return None


def tools_for(spec: AgentSpec) -> list[ToolDef]:
    """The tool definitions an assistant is permitted to call."""
    return [TOOLS[name] for name in spec.tool_names if name in TOOLS]
