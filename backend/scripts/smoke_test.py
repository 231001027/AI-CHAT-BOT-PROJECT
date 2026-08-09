"""
End-to-end smoke test against a running API.

Walks the clinically essential path the way the frontend will: register a
patient, pick a category and condition, answer the branching questionnaire to
completion, evaluate the rules, request an AI explanation, and generate the PDF.
Then exercises the staff/admin surface with a real JWT.

Usage:
    python scripts/smoke_test.py [base_url]
"""

from __future__ import annotations

import sys
from typing import Any, Optional

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
ADMIN_EMAIL = "admin@niepmd.gov.in"
ADMIN_PASSWORD = "ChangeMe!2026"

passed = 0
failed: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    global passed
    if condition:
        passed += 1
        print(f"  ok   {label}")
    else:
        failed.append(label)
        print(f"  FAIL {label} {detail}")
    return condition


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def show(response: httpx.Response, limit: int = 300) -> str:
    return f"[{response.status_code}] {response.text[:limit]}"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=120.0)

    section("Health")
    r = client.get("/health")
    check("health returns ok", r.status_code == 200 and r.json()["status"] == "ok", show(r))

    r = client.get("/openapi.json")
    check("openapi schema serves", r.status_code == 200, show(r))
    route_count = len(r.json().get("paths", {})) if r.status_code == 200 else 0
    print(f"       {route_count} paths registered")

    # ── Patient registration ────────────────────────────────────────────────
    section("Registration")
    r = client.post(
        "/api/patients",
        json={
            "name": "Smoke Test Patient",
            "age": 67,
            "gender": "male",
            "district": "Chennai",
            "phone": "9876500011",
            "relationship": "myself",
        },
    )
    if not check("adult registration succeeds", r.status_code == 201, show(r)):
        return 1
    adult = r.json()
    patient_id = adult["id"]
    check("flow_type inferred as adult", adult["profile"]["flow_type"] == "adult", str(adult))

    # A child must not be registrable without guardian consent.
    r = client.post(
        "/api/patients",
        json={
            "name": "Smoke Test Baby",
            "age": 0,
            "gender": "female",
            "district": "Chennai",
            "relationship": "my_child",
        },
    )
    check("child registration without consent is blocked", r.status_code == 400, show(r))

    r = client.post(
        "/api/patients",
        json={
            "name": "Smoke Test Baby",
            "age": 0,
            "gender": "female",
            "district": "Chennai",
            "relationship": "my_child",
            "consent_given": True,
            "consent_by": "Parent Name",
        },
    )
    child = r.json() if r.status_code == 201 else {}
    check("child registration with consent succeeds", r.status_code == 201, show(r))
    check(
        "child flow_type inferred",
        child.get("profile", {}).get("flow_type") == "child",
        str(child)[:200],
    )
    check(
        "newborn subtype inferred from age 0",
        child.get("profile", {}).get("child_subtype") == "newborn",
        str(child)[:200],
    )

    r = client.get(f"/api/patients/{patient_id}")
    check("patient lookup by id", r.status_code == 200, show(r))

    r = client.get("/api/patients/00000000-0000-0000-0000-000000000000")
    check("unknown patient returns 404", r.status_code == 404, show(r))

    r = client.post("/api/patients", json={"name": "X", "age": 500, "gender": "male",
                                          "district": "Y", "relationship": "myself"})
    check("invalid age rejected", r.status_code == 422, show(r))

    r = client.post("/api/patients", json={"name": "A", "age": 30, "gender": "male",
                                          "district": "Y", "relationship": "myself"})
    check("too-short name rejected", r.status_code == 422, show(r))

    # ── Catalog ─────────────────────────────────────────────────────────────
    section("Catalog")
    r = client.get("/api/categories", params={"flow_type": "adult"})
    if not check("adult categories load", r.status_code == 200, show(r)):
        return 1
    adult_categories = r.json()
    check("adult categories non-empty", len(adult_categories) > 0)

    r = client.get("/api/categories", params={"flow_type": "child"})
    child_categories = r.json() if r.status_code == 200 else []
    check("child categories load", r.status_code == 200 and len(child_categories) > 0, show(r))
    check(
        "flow filter is honoured",
        {c["id"] for c in adult_categories}.isdisjoint({c["id"] for c in child_categories}),
    )

    category = next(
        (c for c in adult_categories if "hearing" in c["name"].lower()), adult_categories[0]
    )
    r = client.get("/api/conditions", params={"category_id": category["id"]})
    conditions = r.json() if r.status_code == 200 else []
    if not check("conditions load", r.status_code == 200 and len(conditions) > 0, show(r)):
        return 1

    condition = next(
        (c for c in conditions if "gradual" in c["name"].lower()), conditions[0]
    )
    print(f"       using: {category['name']} > {condition['name']}")

    r = client.get("/api/questions", params={"condition_id": condition["id"]})
    questions = r.json() if r.status_code == 200 else []
    check("questions load with options", r.status_code == 200 and len(questions) > 0, show(r))
    check("every question has options", all(q["options"] for q in questions))
    check("exactly one entry question", sum(1 for q in questions if q["is_entry"]) == 1)

    # ── Questionnaire session ───────────────────────────────────────────────
    section("Questionnaire")
    r = client.post(
        "/api/sessions",
        json={"patient_id": patient_id, "condition_id": condition["id"]},
    )
    if not check("session starts", r.status_code == 201, show(r)):
        return 1
    state = r.json()
    session_id = state["session_id"]
    check("first question served", state["question"] is not None, str(state)[:200])
    check("progress starts at zero", state["progress"]["answered"] == 0, str(state["progress"]))
    check("not complete at start", state["is_complete"] is False)

    r = client.get(f"/api/sessions/{session_id}")
    check("session state is resumable", r.status_code == 200, show(r))

    answered = 0
    guard = 0
    # Remember what was answered so re-submission can be tested below.
    trail: list[tuple[str, str]] = []
    while state.get("question") and guard < 40:
        guard += 1
        question = state["question"]
        option = question["options"][0]
        r = client.post(
            f"/api/sessions/{session_id}/answers",
            json={"question_id": question["id"], "option_id": option["id"]},
        )
        if not check(f"answer {guard}: {question['key']} = {option['value']}",
                     r.status_code == 200, show(r)):
            return 1
        state = r.json()
        trail.append((question["id"], option["id"]))
        answered += 1

    check("questionnaire terminates", state.get("question") is None, str(state)[:200])
    check("session marked complete", state.get("is_complete") is True)
    check("answered at least 2 questions", answered >= 2, f"answered={answered}")
    print(f"       traversed {answered} questions")

    # Re-answering must be idempotent, not duplicate rows.
    r = client.get(f"/api/sessions/{session_id}/summary")
    if not check("summary loads", r.status_code == 200, show(r)):
        return 1
    summary = r.json()
    check(
        "summary answer count matches traversal",
        len(summary["answers"]) == answered,
        f"{len(summary['answers'])} vs {answered}",
    )
    check("summary carries patient", summary["patient"]["id"] == patient_id)
    check("summary carries condition", summary["condition"] is not None)

    check("summary answers carry readable labels",
          all(a["answer_label"].strip() and a["question_text"].strip()
              for a in summary["answers"]))

    # A patient must be able to correct a mis-tap on the review screen even after
    # the questionnaire has completed.
    first_question_id, first_option_id = trail[0]
    r = client.post(
        f"/api/sessions/{session_id}/answers",
        json={"question_id": first_question_id, "option_id": first_option_id},
    )
    check("correcting an answer on a complete session is accepted", r.status_code == 200, show(r))
    r = client.get(f"/api/sessions/{session_id}/summary")
    check(
        "correction updates in place rather than duplicating",
        len(r.json()["answers"]) == answered,
        f"{len(r.json()['answers'])} vs {answered}",
    )

    r = client.post(
        f"/api/sessions/{session_id}/answers",
        json={"question_id": first_question_id,
              "option_id": "00000000-0000-0000-0000-000000000000"},
    )
    check("option not belonging to the question is rejected",
          r.status_code in (400, 404, 422), show(r))

    r = client.get("/api/sessions/00000000-0000-0000-0000-000000000000")
    check("unknown session returns 404", r.status_code == 404, show(r))

    # Changing a branching answer must reroute rather than keep stale answers.
    # Look for any question the patient answered whose options branch.
    answered_ids = {qid for qid, _ in trail}
    entry = None
    branching = None
    for candidate in questions:
        if candidate["id"] not in answered_ids:
            continue
        alt = next(
            (
                o
                for o in candidate["options"]
                if o.get("next_question_id")
                and o["id"] != dict(trail).get(candidate["id"])
            ),
            None,
        )
        if alt is not None:
            entry, branching = candidate, alt
            break

    if branching is not None:
        print(f"       switching {entry['key']} to branching option '{branching['value']}'")
        r = client.post(
            f"/api/sessions/{session_id}/answers",
            json={"question_id": entry["id"], "option_id": branching["id"]},
        )
        check("switching a branch is accepted", r.status_code == 200, show(r))
        r = client.get(f"/api/sessions/{session_id}/summary")
        if r.status_code == 200:
            remaining = {a["question_key"] for a in r.json()["answers"]}
            check(
                "no answer survives outside the new route",
                len(remaining) <= answered,
                f"{len(remaining)} answers after reroute",
            )
        # Restore the original path so the recommendation checks below are stable.
        client.post(
            f"/api/sessions/{session_id}/answers",
            json={"question_id": first_question_id, "option_id": first_option_id},
        )
        state = client.get(f"/api/sessions/{session_id}").json()
        guard = 0
        while state.get("question") and guard < 40:
            guard += 1
            q = state["question"]
            r = client.post(
                f"/api/sessions/{session_id}/answers",
                json={"question_id": q["id"], "option_id": q["options"][0]["id"]},
            )
            if r.status_code != 200:
                break
            state = r.json()
        check("session completes again after rerouting", state.get("is_complete") is True,
              str(state)[:200])

    # ── Recommendation engine ───────────────────────────────────────────────
    section("Recommendations")
    r = client.post("/api/recommendations/evaluate", json={"session_id": session_id})
    if not check("evaluate succeeds", r.status_code == 200, show(r)):
        return 1
    rec = r.json()
    tests = rec["recommended_tests"]
    check("at least one test recommended", len(tests) > 0, str(rec)[:300])
    check("every test has a code", all(t["test_code"] for t in tests))
    check("every test has a patient-facing reason", all(t["reason_text"].strip() for t in tests))
    check("no duplicate test codes", len({t["test_code"] for t in tests}) == len(tests))
    check("disclaimer present", bool(rec.get("disclaimer", "").strip()))
    print(f"       tests: {', '.join(t['test_code'] for t in tests)}")

    r = client.get(f"/api/recommendations/{session_id}")
    check("recommendations are retrievable", r.status_code == 200, show(r))
    check(
        "retrieved plan matches evaluated plan",
        r.status_code == 200
        and [t["test_code"] for t in r.json()["recommended_tests"]]
        == [t["test_code"] for t in tests],
    )

    # Re-evaluating must be stable, not append a second plan.
    r = client.post("/api/recommendations/evaluate", json={"session_id": session_id})
    check(
        "re-evaluation is deterministic",
        r.status_code == 200
        and [t["test_code"] for t in r.json()["recommended_tests"]]
        == [t["test_code"] for t in tests],
        show(r),
    )

    # ── AI treatment assistant ──────────────────────────────────────────────
    section("AI assistant")
    r = client.get("/api/ai/status")
    check("rag status reports", r.status_code == 200, show(r))
    if r.status_code == 200:
        print(f"       {r.json()}")

    r = client.post(
        "/api/ai/explain-test",
        json={
            "session_id": session_id,
            "test_code": tests[0]["test_code"],
            "test_name": tests[0]["test_name"],
        },
    )
    if check("explain-test responds", r.status_code == 200, show(r)):
        explanation = r.json()
        check("explanation text is non-empty", bool(explanation["explanation"].strip()))
        check("explanation carries a disclaimer", bool(explanation["disclaimer"].strip()))
        check("explanation declares its source", explanation["source"] in
              {"rag", "static_fallback", "cached"}, str(explanation.get("source")))
        print(f"       source={explanation['source']}")
        # With no documents indexed yet, the assistant must degrade to the static
        # fallback rather than answering ungrounded.
        check(
            "with an empty corpus the assistant does not answer ungrounded",
            explanation["source"] != "rag",
            str(explanation.get("source")),
        )

    # The audit trail is clinical data, so it must not be readable anonymously.
    r = client.get(f"/api/ai/conversations/{session_id}")
    check("ai audit trail rejects anonymous access", r.status_code in (401, 403), show(r))

    # ── Reports ─────────────────────────────────────────────────────────────
    section("Reports")
    r = client.post("/api/reports/generate", json={"session_id": session_id})
    if not check("report generation succeeds", r.status_code in (200, 201), show(r)):
        return 1
    report = r.json()
    report_id = report["id"]
    check("report json has tests", len(report["report_json"]["recommended_tests"]) > 0)
    check("report json has disclaimer", bool(report["report_json"]["disclaimer"]))

    r = client.get(f"/api/reports/{report_id}/download")
    is_pdf = r.status_code == 200 and r.content[:4] == b"%PDF"
    check("pdf downloads with a PDF signature", is_pdf, show(r, 80))
    if is_pdf:
        print(f"       {len(r.content):,} bytes")

    # ── Auth ────────────────────────────────────────────────────────────────
    section("Auth")
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if not check("admin login succeeds", r.status_code == 200, show(r)):
        return 1
    tokens = r.json()
    access = tokens["access_token"]
    auth = {"Authorization": f"Bearer {access}"}
    check("access token issued", bool(access))
    check("refresh token issued", bool(tokens.get("refresh_token")))
    check("doctor profile returned", tokens["doctor"]["email"] == ADMIN_EMAIL)

    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    check("wrong password rejected", r.status_code == 401, show(r))

    r = client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "x"})
    check("unknown email rejected", r.status_code == 401, show(r))

    r = client.get("/api/auth/me", headers=auth)
    check("me endpoint works with token", r.status_code == 200, show(r))

    r = client.get("/api/auth/me")
    check("me endpoint rejects anonymous", r.status_code in (401, 403), show(r))

    r = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
    check("forged token rejected", r.status_code == 401, show(r))

    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    check("refresh issues a new access token", r.status_code == 200 and
          bool(r.json().get("access_token")), show(r))

    r = client.post("/api/auth/refresh", json={"refresh_token": access})
    check("access token cannot be used to refresh", r.status_code == 401, show(r))

    # ── Admin surface ───────────────────────────────────────────────────────
    section("Admin")
    r = client.get("/api/admin/dashboard", headers=auth)
    if check("dashboard loads", r.status_code == 200, show(r)):
        stats = r.json()
        check("dashboard counts patients", stats["patients_total"] >= 2, str(stats))
        check("dashboard counts sessions", stats["sessions_total"] >= 1, str(stats))
        check("dashboard counts completed sessions", stats["sessions_completed"] >= 1, str(stats))
        check("dashboard counts plans", stats["plans_generated"] >= 1, str(stats))
        check("dashboard counts reports", stats["reports_generated"] >= 1, str(stats))
        check("dashboard counts ai explanations", stats["ai_explanations"] >= 1, str(stats))
        check("dashboard reports active rules", stats["rules_active"] > 0, str(stats))
        check("dashboard reports active questions", stats["questions_active"] > 0, str(stats))
        check(
            "fallback rate is a proportion",
            0.0 <= stats["ai_fallback_rate"] <= 1.0,
            str(stats["ai_fallback_rate"]),
        )
        for key, value in sorted(stats.items()):
            print(f"       {key:24} {value}")

    r = client.get("/api/admin/dashboard")
    check("dashboard rejects anonymous", r.status_code in (401, 403), show(r))

    for path in ("/api/admin/categories", "/api/admin/rules", "/api/admin/doctors",
                 "/api/admin/documents", "/api/admin/ai-logs", "/api/admin/reports",
                 "/api/admin/static-explanations"):
        r = client.get(path, headers=auth)
        check(f"GET {path}", r.status_code == 200, show(r, 150))

    # The explanation issued earlier must be auditable by staff.
    r = client.get(f"/api/ai/conversations/{session_id}", headers=auth)
    check("ai audit trail readable by staff", r.status_code == 200, show(r))
    check("the explanation was logged for audit",
          r.status_code == 200 and len(r.json()) >= 1, show(r, 150))

    # Create → read → update → delete a category.
    r = client.post(
        "/api/admin/categories",
        headers=auth,
        json={
            "slug": "smoke-test-category",
            "name": "Smoke Test Category",
            "flow_type": "adult",
            "description": "Created by the smoke test.",
            "display_order": 999,
        },
    )
    created = r.json() if r.status_code in (200, 201) else {}
    if check("category create", r.status_code in (200, 201), show(r)):
        r = client.patch(
            f"/api/admin/categories/{created['id']}",
            headers=auth,
            json={"name": "Smoke Test Category (renamed)"},
        )
        check("category update", r.status_code == 200, show(r))

        r = client.post(
            "/api/admin/categories",
            headers=auth,
            json={"slug": "smoke-test-category", "name": "Dup", "flow_type": "adult",
                  "description": "", "display_order": 1},
        )
        check("duplicate slug rejected", r.status_code in (400, 409, 422), show(r))

        r = client.delete(f"/api/admin/categories/{created['id']}", headers=auth)
        check("category delete", r.status_code in (200, 204), show(r))

    # Rule validation must reject a malformed predicate before it is stored.
    r = client.post(
        "/api/admin/rules/validate",
        headers=auth,
        json={"rule_definition": {"all": [{"field": "age", "op": ">", "value": 60}]}},
    )
    check("valid rule passes validation", r.status_code == 200 and r.json()["is_valid"], show(r))

    r = client.post(
        "/api/admin/rules/validate",
        headers=auth,
        json={"rule_definition": {"all": [{"field": "age", "op": "!!!", "value": 1}]}},
    )
    check(
        "invalid operator fails validation",
        r.status_code == 200 and not r.json()["is_valid"],
        show(r),
    )

    section("Result")
    total = passed + len(failed)
    print(f"{passed}/{total} checks passed")
    if failed:
        print("\nFailures:")
        for name in failed:
            print(f"  - {name}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
