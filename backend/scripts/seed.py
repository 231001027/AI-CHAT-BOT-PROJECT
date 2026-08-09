#!/usr/bin/env python3
"""
Seed reference data for the whole backend. Idempotent — each section skips if
already populated, so it is safe to run on every deploy.

Covers the audiology triage tables plus the assistant suite: services,
clinicians, appointment slots, knowledge base, screening protocols, therapy
guidelines and counselling resources.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

# Allow `python scripts/seed.py` from any cwd / Docker entrypoint
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.security import hash_password
from app.models import (
    AppointmentSlot,
    ClinicalRule,
    Clinician,
    ConcernConfig,
    Condition,
    CounsellingResource,
    Doctor,
    KnowledgeEntry,
    Question,
    QuestionOption,
    RuleRecommendedTest,
    ScreeningProtocol,
    Service,
    StaticExplanation,
    TestCatalog,
    TherapyGuideline,
    TreatmentCategory,
    TreatmentPlan,
)
from app.models.enums import DoctorRole, SlotStatus
from app.services.clinical_seed_data import CATEGORIES, CONDITIONS, QUESTIONS, RULES
from app.services.clinical_seed_adult import (
    LEGACY_ADULT_CATEGORY_SLUGS,
    LEGACY_ADULT_CONDITION_SLUGS,
)
from app.services.clinical_seed_child import (
    LEGACY_CHILD_CATEGORY_SLUGS,
    LEGACY_CHILD_CONDITION_SLUGS,
)
from app.services.agent_seed_data import (
    CLINICIAN_SERVICES,
    CLINICIANS,
    COUNSELLING_RESOURCES,
    DEFAULT_LOCATION,
    KNOWLEDGE_ENTRIES,
    SCREENING_PROTOCOLS,
    SERVICES,
    SLOT_GENERATION_DAYS,
    SLOT_START_HOURS,
    THERAPY_GUIDELINES,
)
from app.services.seed_data import CONCERN_CONFIGS, TEST_CATALOG
from app.services.static_explanation_data import STATIC_TEST_EXPLANATIONS
from app.services.test_catalog_data import CLINICAL_TEST_CATALOG


async def seed_test_catalog(session: AsyncSession) -> None:
    """
    Upsert the test dictionary by code.

    Unlike the other seeders this one updates in place rather than skipping when
    rows exist, because the catalogue is reference content that gets corrected and
    extended over time. Nothing references these rows by id, so refreshing them is
    safe; patient recommendations snapshot their own test name and reason.
    """
    existing = {
        row.code.upper(): row
        for row in (await session.execute(select(TestCatalog))).scalars().all()
    }

    # The legacy triage catalogue first, then the clinical dictionary, so that
    # where a code appears in both the richer clinical entry wins.
    merged: dict[str, dict[str, Any]] = {}
    for item in (*TEST_CATALOG, *CLINICAL_TEST_CATALOG):
        merged[item["code"].upper()] = item

    created = 0
    updated = 0
    for code, item in merged.items():
        row = existing.get(code)
        if row is None:
            session.add(
                TestCatalog(
                    id=uuid.uuid4(),
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    description=item["description"],
                    preparation=item.get("preparation"),
                    duration_minutes=item.get("duration_minutes"),
                )
            )
            created += 1
            continue

        row.name = item["name"]
        row.category = item["category"]
        row.description = item["description"]
        row.preparation = item.get("preparation")
        row.duration_minutes = item.get("duration_minutes")
        updated += 1

    print(f"TestCatalog: {created} created, {updated} refreshed ({len(merged)} total)")


async def seed_static_explanations(session: AsyncSession) -> None:
    """
    Upsert department-authored definitions used by \"Explain this test\".

    Always refreshes text by test_code so definition updates ship with the next
    seed without needing --refresh-rules.
    """
    existing = {
        row.test_code.upper(): row
        for row in (await session.execute(select(StaticExplanation))).scalars().all()
    }
    created = 0
    updated = 0
    for item in STATIC_TEST_EXPLANATIONS:
        code = item["test_code"].upper()
        row = existing.get(code)
        if row is None:
            session.add(
                StaticExplanation(
                    id=uuid.uuid4(),
                    test_code=code,
                    test_name=item["test_name"],
                    explanation=item["explanation"],
                )
            )
            created += 1
            continue
        row.test_name = item["test_name"]
        row.explanation = item["explanation"]
        updated += 1
    await session.commit()
    print(f"StaticExplanation: {created} created, {updated} refreshed")


async def seed(session: AsyncSession) -> None:
    await seed_test_catalog(session)
    await seed_static_explanations(session)

    cfg_count = await session.scalar(select(func.count()).select_from(ConcernConfig))
    if not cfg_count:
        for item in CONCERN_CONFIGS:
            session.add(
                ConcernConfig(
                    id=uuid.uuid4(),
                    concern_type=item["concern_type"],
                    age_band=item.get("age_band"),
                    common_signs=item["common_signs"],
                    recommended_tests=item["recommended_tests"],
                    what_it_helps=item["what_it_helps"],
                    outcome_options=item.get("outcome_options"),
                    conditional_rules=item.get("conditional_rules"),
                )
            )
        print(f"Seeded {len(CONCERN_CONFIGS)} ConcernConfig rows")
    else:
        print(f"ConcernConfig already has {cfg_count} rows — skip")

    await session.commit()


async def seed_assistant_suite(session: AsyncSession) -> None:
    """Services, clinicians, slots and all clinician-authored assistant content."""
    service_ids: dict[str, uuid.UUID] = {}
    service_count = await session.scalar(select(func.count()).select_from(Service))
    if not service_count:
        for item in SERVICES:
            row = Service(
                id=uuid.uuid4(),
                code=item["code"],
                name=item["name"],
                vertical=item["vertical"],
                duration_minutes=item["duration_minutes"],
                description=item["description"],
                preparation=item.get("preparation"),
                documents_required=item.get("documents_required"),
                report_turnaround=item.get("report_turnaround"),
            )
            session.add(row)
            service_ids[row.code] = row.id
        print(f"Seeded {len(SERVICES)} Service rows")
    else:
        print(f"Service already has {service_count} rows — skip")
        for row in (await session.execute(select(Service))).scalars().all():
            service_ids[row.code] = row.id

    clinician_ids: dict[str, uuid.UUID] = {}
    clinician_count = await session.scalar(select(func.count()).select_from(Clinician))
    if not clinician_count:
        for item in CLINICIANS:
            row = Clinician(
                id=uuid.uuid4(),
                name=item["name"],
                designation=item["designation"],
                vertical=item["vertical"],
            )
            session.add(row)
            clinician_ids[row.name] = row.id
        print(f"Seeded {len(CLINICIANS)} Clinician rows")
    else:
        print(f"Clinician already has {clinician_count} rows — skip")
        for row in (await session.execute(select(Clinician))).scalars().all():
            clinician_ids[row.name] = row.id

    slot_count = await session.scalar(select(func.count()).select_from(AppointmentSlot))
    if not slot_count:
        created = _generate_slots(session, service_ids, clinician_ids)
        print(f"Seeded {created} AppointmentSlot rows")
    else:
        print(f"AppointmentSlot already has {slot_count} rows — skip")

    knowledge_count = await session.scalar(select(func.count()).select_from(KnowledgeEntry))
    if not knowledge_count:
        for item in KNOWLEDGE_ENTRIES:
            session.add(
                KnowledgeEntry(
                    id=uuid.uuid4(),
                    slug=item["slug"],
                    vertical=item["vertical"],
                    agent_types=item.get("agent_types") or [],
                    topic=item["topic"],
                    question=item["question"],
                    answer=item["answer"],
                    keywords=item.get("keywords") or [],
                    priority=item.get("priority", 0),
                )
            )
        print(f"Seeded {len(KNOWLEDGE_ENTRIES)} KnowledgeEntry rows")
    else:
        print(f"KnowledgeEntry already has {knowledge_count} rows — skip")

    protocol_count = await session.scalar(select(func.count()).select_from(ScreeningProtocol))
    if not protocol_count:
        for item in SCREENING_PROTOCOLS:
            session.add(
                ScreeningProtocol(
                    id=uuid.uuid4(),
                    age_band=item["age_band"],
                    name=item["name"],
                    summary=item["summary"],
                    test_codes=item["test_codes"],
                    referral_criteria=item["referral_criteria"],
                    timeline=item["timeline"],
                    preparation=item.get("preparation"),
                )
            )
        print(f"Seeded {len(SCREENING_PROTOCOLS)} ScreeningProtocol rows")
    else:
        print(f"ScreeningProtocol already has {protocol_count} rows — skip")

    guideline_count = await session.scalar(select(func.count()).select_from(TherapyGuideline))
    if not guideline_count:
        for item in THERAPY_GUIDELINES:
            session.add(
                TherapyGuideline(
                    id=uuid.uuid4(),
                    domain=item["domain"],
                    age_band=item.get("age_band"),
                    title=item["title"],
                    summary=item["summary"],
                    milestones=item["milestones"],
                    home_activities=item["home_activities"],
                    red_flags=item["red_flags"],
                    typical_frequency=item.get("typical_frequency"),
                )
            )
        print(f"Seeded {len(THERAPY_GUIDELINES)} TherapyGuideline rows")
    else:
        print(f"TherapyGuideline already has {guideline_count} rows — skip")

    resource_count = await session.scalar(select(func.count()).select_from(CounsellingResource))
    if not resource_count:
        for item in COUNSELLING_RESOURCES:
            session.add(
                CounsellingResource(
                    id=uuid.uuid4(),
                    slug=item["slug"],
                    topic=item["topic"],
                    age_band=item.get("age_band"),
                    summary=item["summary"],
                    talking_points=item["talking_points"],
                    reassurance=item["reassurance"],
                    next_steps=item["next_steps"],
                    keywords=item.get("keywords") or [],
                )
            )
        print(f"Seeded {len(COUNSELLING_RESOURCES)} CounsellingResource rows")
    else:
        print(f"CounsellingResource already has {resource_count} rows — skip")

    await session.commit()


def _generate_slots(
    session: AsyncSession,
    service_ids: dict[str, uuid.UUID],
    clinician_ids: dict[str, uuid.UUID],
) -> int:
    """
    Create weekday slots for the next few weeks so the scheduling assistant has
    real availability to offer out of the box.
    """
    today = datetime.now(timezone.utc).date()
    created = 0

    for day_offset in range(1, SLOT_GENERATION_DAYS + 1):
        day = today + timedelta(days=day_offset)
        if day.weekday() > 4:  # weekends closed
            continue

        for clinician_name, service_codes in CLINICIAN_SERVICES.items():
            clinician_id = clinician_ids.get(clinician_name)
            if clinician_id is None:
                continue

            for index, hour in enumerate(SLOT_START_HOURS):
                # Rotate which service each hour offers so availability is spread
                # across the clinician's whole caseload rather than one service.
                code = service_codes[(day_offset + index) % len(service_codes)]
                service_id = service_ids.get(code)
                if service_id is None:
                    continue

                duration = next(
                    (s["duration_minutes"] for s in SERVICES if s["code"] == code), 45
                )
                starts_at = datetime.combine(day, time(hour=hour), tzinfo=timezone.utc)
                session.add(
                    AppointmentSlot(
                        id=uuid.uuid4(),
                        service_id=service_id,
                        clinician_id=clinician_id,
                        starts_at=starts_at,
                        ends_at=starts_at + timedelta(minutes=duration),
                        capacity=1,
                        booked_count=0,
                        status=SlotStatus.OPEN.value,
                        location=DEFAULT_LOCATION,
                    )
                )
                created += 1

    return created


async def seed_clinical_flow(session: AsyncSession) -> None:
    """
    Categories, conditions, the branching question bank and clinical rules.

    Branch targets are declared by question key in the seed data and resolved to
    ids in a second pass, once every question row exists.

    Categories/conditions are synced on every run so label and pathway updates
    (for example splitting adult audiology concerns) appear without a wipe.
    """
    # Remove retired adult/child pathway content before syncing Part-1 / Part-2 screens.
    legacy_condition_slugs = LEGACY_CHILD_CONDITION_SLUGS | LEGACY_ADULT_CONDITION_SLUGS
    legacy_category_slugs = LEGACY_CHILD_CATEGORY_SLUGS | LEGACY_ADULT_CATEGORY_SLUGS

    legacy_conditions = (
        await session.execute(
            select(Condition).where(Condition.slug.in_(legacy_condition_slugs))
        )
    ).scalars().all()
    for cond in legacy_conditions:
        # Rules + recommended tests cascade from condition.
        for rule in (
            await session.execute(
                select(ClinicalRule).where(ClinicalRule.condition_id == cond.id)
            )
        ).scalars().all():
            await session.delete(rule)
        # Questions + options cascade from condition.
        for question in (
            await session.execute(
                select(Question).where(Question.condition_id == cond.id)
            )
        ).scalars().all():
            await session.delete(question)
        await session.delete(cond)
    if legacy_conditions:
        print(f"Removed {len(legacy_conditions)} legacy Condition rows")

    legacy_categories = (
        await session.execute(
            select(TreatmentCategory).where(
                TreatmentCategory.slug.in_(legacy_category_slugs)
            )
        )
    ).scalars().all()
    for cat in legacy_categories:
        await session.delete(cat)
    if legacy_categories:
        print(f"Removed {len(legacy_categories)} legacy TreatmentCategory rows")
    await session.flush()

    # Older category slugs renamed in place so existing FKs keep working.
    slug_renames = {
        "tinnitus-balance": "ringing-in-ears",
        "ear-symptoms": "ear-pain-discharge",
    }
    for old_slug, new_slug in slug_renames.items():
        row = await session.scalar(
            select(TreatmentCategory).where(TreatmentCategory.slug == old_slug)
        )
        if row is None:
            continue
        clash = await session.scalar(
            select(TreatmentCategory).where(TreatmentCategory.slug == new_slug)
        )
        if clash is None:
            row.slug = new_slug
            print(f"TreatmentCategory: renamed {old_slug} → {new_slug}")
        else:
            # Prefer the canonical slug; move conditions off the legacy row.
            for cond in (
                await session.execute(
                    select(Condition).where(Condition.category_id == row.id)
                )
            ).scalars().all():
                cond.category_id = clash.id
            await session.delete(row)
            print(f"TreatmentCategory: merged {old_slug} into {new_slug}")

    category_ids: dict[str, uuid.UUID] = {}
    existing_categories = {
        row.slug: row
        for row in (await session.execute(select(TreatmentCategory))).scalars().all()
    }
    created_categories = 0
    refreshed_categories = 0
    for item in CATEGORIES:
        row = existing_categories.get(item["slug"])
        if row is None:
            row = TreatmentCategory(
                id=uuid.uuid4(),
                slug=item["slug"],
                name=item["name"],
                flow_type=item["flow_type"],
                department=item.get("department", "audiology"),
                description=item["description"],
                display_order=item["display_order"],
            )
            session.add(row)
            created_categories += 1
        else:
            changed = False
            for field in ("name", "flow_type", "description", "display_order"):
                if getattr(row, field) != item[field]:
                    setattr(row, field, item[field])
                    changed = True
            dept = item.get("department", "audiology")
            if getattr(row, "department", None) != dept:
                row.department = dept
                changed = True
            if changed:
                refreshed_categories += 1
        category_ids[item["slug"]] = row.id
        existing_categories[item["slug"]] = row
    if created_categories:
        print(f"Seeded {created_categories} TreatmentCategory rows")
    if refreshed_categories:
        print(f"TreatmentCategory: refreshed {refreshed_categories} rows")
    if not created_categories and not refreshed_categories:
        print(f"TreatmentCategory already synced ({len(category_ids)} rows)")

    condition_ids: dict[str, uuid.UUID] = {}
    existing_conditions = {
        row.slug: row
        for row in (await session.execute(select(Condition))).scalars().all()
    }
    created_conditions = 0
    refreshed_conditions = 0
    for item in CONDITIONS:
        category_id = category_ids.get(item["category_slug"])
        if category_id is None:
            print(f"  ! skipping condition {item['slug']}: unknown category")
            continue
        row = existing_conditions.get(item["slug"])
        if row is None:
            row = Condition(
                id=uuid.uuid4(),
                category_id=category_id,
                slug=item["slug"],
                name=item["name"],
                description=item["description"],
                display_order=item["display_order"],
            )
            session.add(row)
            created_conditions += 1
        else:
            changed = False
            if row.category_id != category_id:
                row.category_id = category_id
                changed = True
            for field in ("name", "description", "display_order"):
                if getattr(row, field) != item[field]:
                    setattr(row, field, item[field])
                    changed = True
            if changed:
                refreshed_conditions += 1
        condition_ids[item["slug"]] = row.id
        existing_conditions[item["slug"]] = row
    if created_conditions:
        print(f"Seeded {created_conditions} Condition rows")
    if refreshed_conditions:
        print(f"Condition: refreshed {refreshed_conditions} rows")
    if not created_conditions and not refreshed_conditions:
        print(f"Condition already synced ({len(condition_ids)} rows)")

    question_count = await session.scalar(select(func.count()).select_from(Question))
    if not question_count:
        # (condition_slug, question_key) -> id, so branch keys resolve within
        # their own condition and cannot leak across flows.
        question_ids: dict[tuple[str, str], uuid.UUID] = {}
        pending_branches: list[tuple[QuestionOption, str, str]] = []
        options_created = 0

        for item in QUESTIONS:
            condition_slug = item["condition_slug"]
            condition_id = condition_ids.get(condition_slug)
            if condition_id is None:
                print(f"  ! skipping question {item['key']}: unknown condition {condition_slug}")
                continue

            question = Question(
                id=uuid.uuid4(),
                condition_id=condition_id,
                key=item["key"],
                text=item["text"],
                help_text=item.get("help_text"),
                display_order=item["display_order"],
                question_type=item.get("question_type", "single_select"),
                is_entry=item.get("is_entry", False),
            )
            session.add(question)
            question_ids[(condition_slug, question.key)] = question.id

            for order, option in enumerate(item.get("options", []), start=1):
                row = QuestionOption(
                    id=uuid.uuid4(),
                    question_id=question.id,
                    label=option["label"],
                    value=option["value"],
                    display_order=option.get("display_order", order),
                    is_terminal=option.get("terminal", False),
                )
                session.add(row)
                options_created += 1
                if branch := option.get("branch"):
                    pending_branches.append((row, condition_slug, branch))

        for option_row, condition_slug, target_key in pending_branches:
            target_id = question_ids.get((condition_slug, target_key))
            if target_id is None:
                print(
                    f"  ! branch target '{target_key}' not found in {condition_slug}; "
                    "option will fall through sequentially"
                )
                continue
            option_row.next_question_id = target_id

        print(
            f"Seeded {len(question_ids)} Question rows, {options_created} options, "
            f"{len(pending_branches)} branches"
        )
    else:
        print(f"Question already has {question_count} rows — skip bulk insert")
        # Fill in any new conditions added after the first seed (e.g. other-hearing).
        pending_branches: list[tuple[QuestionOption, str, str]] = []
        question_ids: dict[tuple[str, str], uuid.UUID] = {}
        added_questions = 0
        for item in QUESTIONS:
            condition_slug = item["condition_slug"]
            condition_id = condition_ids.get(condition_slug)
            if condition_id is None:
                continue
            existing = await session.scalar(
                select(Question).where(
                    Question.condition_id == condition_id,
                    Question.key == item["key"],
                )
            )
            if existing is not None:
                question_ids[(condition_slug, item["key"])] = existing.id
                continue
            question = Question(
                id=uuid.uuid4(),
                condition_id=condition_id,
                key=item["key"],
                text=item["text"],
                help_text=item.get("help_text"),
                display_order=item["display_order"],
                question_type=item.get("question_type", "single_select"),
                is_entry=item.get("is_entry", False),
            )
            session.add(question)
            question_ids[(condition_slug, question.key)] = question.id
            added_questions += 1
            for order, option in enumerate(item.get("options", []), start=1):
                row = QuestionOption(
                    id=uuid.uuid4(),
                    question_id=question.id,
                    label=option["label"],
                    value=option["value"],
                    display_order=option.get("display_order", order),
                    is_terminal=option.get("terminal", False),
                )
                session.add(row)
                if branch := option.get("branch"):
                    pending_branches.append((row, condition_slug, branch))
        for option_row, condition_slug, target_key in pending_branches:
            target_id = question_ids.get((condition_slug, target_key))
            if target_id is not None:
                option_row.next_question_id = target_id
        if added_questions:
            print(f"Question: added {added_questions} rows for new conditions")

    rule_count = await session.scalar(select(func.count()).select_from(ClinicalRule))
    if not rule_count:
        # Reload conditions so category_id is available for rule scoping.
        conditions_by_slug = {
            row.slug: row for row in (await session.execute(select(Condition))).scalars().all()
        }
        rules_created = 0
        tests_created = 0

        for item in RULES:
            condition = conditions_by_slug.get(item["condition_slug"])
            if condition is None:
                print(f"  ! skipping rule '{item['name']}': unknown condition")
                continue

            rule = ClinicalRule(
                id=uuid.uuid4(),
                category_id=condition.category_id,
                condition_id=condition.id,
                name=item["name"],
                description=item.get("description", ""),
                rule_definition=item.get("rule_definition") or {},
                priority=item.get("priority", 0),
                is_baseline=item.get("is_baseline", False),
            )
            session.add(rule)
            rules_created += 1

            for test in item.get("tests", []):
                session.add(
                    RuleRecommendedTest(
                        id=uuid.uuid4(),
                        rule_id=rule.id,
                        test_code=test["test_code"].upper(),
                        test_name=test["test_name"],
                        reason_text=test.get("reason_text", ""),
                        display_order=test.get("display_order", 0),
                    )
                )
                tests_created += 1

        print(f"Seeded {rules_created} ClinicalRule rows with {tests_created} test mappings")
    else:
        print(f"ClinicalRule already has {rule_count} rows — skip bulk insert")
        conditions_by_slug = {
            row.slug: row for row in (await session.execute(select(Condition))).scalars().all()
        }
        rules_added = 0
        for item in RULES:
            condition = conditions_by_slug.get(item["condition_slug"])
            if condition is None:
                continue
            existing = await session.scalar(
                select(ClinicalRule).where(
                    ClinicalRule.condition_id == condition.id,
                    ClinicalRule.name == item["name"],
                )
            )
            if existing is not None:
                # Keep category alignment if the condition moved.
                if existing.category_id != condition.category_id:
                    existing.category_id = condition.category_id
                continue
            rule = ClinicalRule(
                id=uuid.uuid4(),
                category_id=condition.category_id,
                condition_id=condition.id,
                name=item["name"],
                description=item.get("description", ""),
                rule_definition=item.get("rule_definition") or {},
                priority=item.get("priority", 0),
                is_baseline=item.get("is_baseline", False),
            )
            session.add(rule)
            rules_added += 1
            for test in item.get("tests", []):
                session.add(
                    RuleRecommendedTest(
                        id=uuid.uuid4(),
                        rule_id=rule.id,
                        test_code=test["test_code"].upper(),
                        test_name=test["test_name"],
                        reason_text=test.get("reason_text", ""),
                        display_order=test.get("display_order", 0),
                    )
                )
        if rules_added:
            print(f"ClinicalRule: added {rules_added} rows for new conditions")

    await session.commit()


async def seed_admin_account(session: AsyncSession) -> None:
    """
    Create a bootstrap admin so the admin screens are reachable on a fresh
    install. The password is a placeholder and must be changed on first sign-in.
    """
    doctor_count = await session.scalar(select(func.count()).select_from(Doctor))
    if doctor_count:
        print(f"Doctor already has {doctor_count} rows — skip")
        return

    # Must be a routable domain: EmailStr rejects reserved TLDs such as .local,
    # which would leave this bootstrap account unable to sign in.
    email = "admin@niepmd.gov.in"
    session.add(
        Doctor(
            id=uuid.uuid4(),
            name="Department Administrator",
            email=email,
            specialization="Administration",
            role=DoctorRole.ADMIN.value,
            password_hash=hash_password("ChangeMe!2026"),
        )
    )
    await session.commit()
    print(f"Seeded bootstrap admin {email} / ChangeMe!2026 — CHANGE THIS PASSWORD")


async def refresh_clinical_rules(session: AsyncSession) -> None:
    """
    Replace the rule set with the current seed definitions.

    Safe to run against a live database: ``treatment_plans`` stores its recommended
    tests as a JSONB snapshot taken at generation time, precisely so that a rule
    being edited or retired can never retroactively change what a patient was
    already told. Only the rule definitions themselves are replaced.

    Invoked explicitly with ``--refresh-rules`` because it is a write to authored
    clinical content, not idempotent reference seeding.
    """
    plan_count = await session.scalar(select(func.count()).select_from(TreatmentPlan))
    rule_count = await session.scalar(select(func.count()).select_from(ClinicalRule))
    print(
        f"Refreshing {rule_count} clinical rules. "
        f"{plan_count} existing patient plans keep their snapshots untouched."
    )

    await session.execute(delete(RuleRecommendedTest))
    await session.execute(delete(ClinicalRule))
    await session.commit()

    await seed_clinical_flow(session)


async def main() -> None:
    refresh_rules = "--refresh-rules" in sys.argv

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        await seed(session)
        await seed_assistant_suite(session)
        await seed_clinical_flow(session)
        await seed_admin_account(session)
        if refresh_rules:
            await refresh_clinical_rules(session)
    await engine.dispose()
    print("Seed complete.", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    asyncio.run(main())
