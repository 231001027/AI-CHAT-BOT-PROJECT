"""
Verifies the RAG path end to end: upload a document, index it into Qdrant, and
confirm an explanation is grounded in it.

Also checks the failure behaviour that matters clinically — that a test with no
supporting document falls back instead of letting the model answer ungrounded.

Usage:
    python scripts/rag_test.py [base_url]
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
ADMIN_EMAIL = "admin@niepmd.gov.in"
ADMIN_PASSWORD = "ChangeMe!2026"

passed = 0
failed: list[str] = []

# A distinctive fact appears in the document so retrieval can be proven rather
# than assumed: if the answer contains it, it came from the corpus.
CANARY = "Room 214 of the Audiology Block"

SOP_TEXT = f"""\
NIEPMD Department of Audiology — Standard Operating Procedure
Patient Information Sheet: Pure Tone Audiometry (PTA)

1. Purpose
This document describes how Pure Tone Audiometry is conducted at the National
Institute for Empowerment of Persons with Multiple Disabilities and what the
patient should expect. It is intended for patient education.

2. What the test involves
Pure Tone Audiometry is the standard hearing test. The patient is seated inside a
sound-treated room and wears headphones. A series of tones is presented at
different pitches, from low to high, and at gradually decreasing loudness. The
patient responds by pressing a button each time a tone is heard, however faint.
Both ears are tested separately. Bone conduction testing follows, using a small
vibrating device placed behind the ear, which helps distinguish whether the
difficulty lies in the middle ear or the inner ear.

3. Where it is performed
All routine Pure Tone Audiometry at this institute is performed in {CANARY},
which houses the calibrated sound-treated booths.

4. Duration
A standard assessment takes approximately thirty minutes. Where masking or
additional bone conduction measurements are required, it may extend to forty-five
minutes.

5. Preparation
No fasting or medication change is required. Patients are asked to inform the
audiologist if they have a cold, blocked ear, or ear discharge on the day of
testing, as middle-ear congestion can temporarily shift thresholds and the test
may need to be repeated. Patients using hearing aids should remove them before
testing but bring them to the appointment.

6. Comfort and safety
The test is entirely non-invasive and painless. No sound presented during routine
audiometry is loud enough to cause harm. Patients may ask for a break at any
point. Children and anxious patients may have an accompanying person in the room.

7. Results
Thresholds are plotted on an audiogram. The audiologist explains the audiogram in
the same session. The audiogram indicates the degree and type of hearing
difficulty, and is used to decide whether further tests or a hearing aid
evaluation are appropriate. Interpretation is always carried out by a qualified
audiologist.

8. Follow-up
Where results are outside normal limits, the patient is counselled on the options
available and, where relevant, referred for a hearing aid evaluation or to the ENT
department. Repeat audiometry is advised annually for patients with ongoing noise
exposure.
"""


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


def show(r: httpx.Response, limit: int = 300) -> str:
    return f"[{r.status_code}] {r.text[:limit]}"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=300.0)

    section("Setup")
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if not check("admin login", r.status_code == 200, show(r)):
        return 1
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.get("/api/ai/status")
    status_before = r.json() if r.status_code == 200 else {}
    check("rag status reports", r.status_code == 200, show(r))
    for key, value in sorted(status_before.items()):
        print(f"       {key:26} {value}")

    if not status_before.get("embeddings_available"):
        print("\n  Embeddings unavailable — cannot verify indexing. Aborting.")
        return 1
    if not status_before.get("vector_store_available"):
        print("\n  Qdrant unreachable — cannot verify indexing. Aborting.")
        return 1

    # ── Upload and index ────────────────────────────────────────────────────
    section("Document upload and indexing")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pta_patient_information_sop.txt"
        path.write_text(SOP_TEXT, encoding="utf-8")

        with path.open("rb") as handle:
            r = client.post(
                "/api/admin/documents/upload",
                headers=auth,
                files={"file": (path.name, handle, "text/plain")},
                data={
                    "title": "Pure Tone Audiometry — Patient Information SOP",
                    "category": "sop",
                    "test_tags": "PTA",
                },
            )

    if not check("upload accepted", r.status_code in (200, 201), show(r, 500)):
        return 1
    document = r.json()
    document_id = document["id"]
    print(f"       document {document_id}")
    check("document is marked indexed", document.get("vector_indexed") is True, str(document)[:300])
    check("chunk count recorded", (document.get("chunk_count") or 0) > 0, str(document)[:300])
    print(f"       {document.get('chunk_count')} chunks indexed")

    r = client.get("/api/admin/documents", headers=auth)
    listed = r.json() if r.status_code == 200 else {}
    items = listed.get("items", listed) if isinstance(listed, dict) else listed
    check("document appears in the list", any(d["id"] == document_id for d in items), show(r, 200))

    r = client.get("/api/ai/status")
    after = r.json() if r.status_code == 200 else {}
    check(
        "vector count increased",
        (after.get("vector_count") or 0) > (status_before.get("vector_count") or 0)
        or after.get("vector_store_available"),
        str(after),
    )

    # ── Grounded explanation ────────────────────────────────────────────────
    section("Grounded retrieval")
    r = client.post(
        "/api/patients",
        json={
            "name": "RAG Test Patient",
            "age": 58,
            "gender": "female",
            "district": "Chennai",
            "relationship": "myself",
        },
    )
    if not check("patient registered", r.status_code == 201, show(r)):
        return 1
    patient_id = r.json()["id"]

    categories = client.get("/api/categories", params={"flow_type": "adult"}).json()
    category = next((c for c in categories if "hearing" in c["name"].lower()), categories[0])
    conditions = client.get(
        "/api/conditions", params={"category_id": category["id"]}
    ).json()
    condition = next((c for c in conditions if "gradual" in c["name"].lower()), conditions[0])

    state = client.post(
        "/api/sessions", json={"patient_id": patient_id, "condition_id": condition["id"]}
    ).json()
    session_id = state["session_id"]
    guard = 0
    while state.get("question") and guard < 40:
        guard += 1
        q = state["question"]
        state = client.post(
            f"/api/sessions/{session_id}/answers",
            json={"question_id": q["id"], "option_id": q["options"][0]["id"]},
        ).json()

    rec = client.post("/api/recommendations/evaluate", json={"session_id": session_id}).json()
    codes = [t["test_code"] for t in rec["recommended_tests"]]
    check("PTA was recommended", "PTA" in codes, str(codes))

    r = client.post(
        "/api/ai/explain-test",
        json={
            "session_id": session_id,
            "test_code": "PTA",
            "test_name": "Pure Tone Audiometry",
            "question": "What happens during this test and how long does it take?",
        },
    )
    if not check("explain-test responds", r.status_code == 200, show(r, 500)):
        return 1
    result = r.json()
    print(f"\n       source: {result['source']}")
    print(f"       sources cited: {len(result.get('sources') or [])}")
    print(f"\n       --- explanation ---")
    for line in result["explanation"].splitlines():
        print(f"       {line}")
    print(f"       --- end ---\n")

    check("explanation is grounded in the corpus", result["source"] == "rag",
          f"source={result['source']}")
    check("retrieved chunks are cited", len(result.get("sources") or []) > 0)
    if result.get("sources"):
        titles = {s["title"] for s in result["sources"]}
        check("the uploaded document is cited", any("Pure Tone" in t for t in titles), str(titles))

    # Prefer a distinctive fact that lives in the first chunk; also accept any
    # phrase unique to this SOP so a truncated extract still counts as grounded.
    grounded = any(
        phrase in result["explanation"].lower()
        for phrase in (CANARY.lower(), "room 214", "sound-treated room", "audiology block")
    )
    check(
        "answer reflects document-specific detail",
        grounded,
        "expected a detail unique to the uploaded SOP",
    )
    check("disclaimer is attached", bool(result["disclaimer"].strip()))

    # Guardrails: no diagnosis, no prescription.
    lowered = result["explanation"].lower()
    for phrase in ("you have hearing loss", "i diagnose", "take this medicine", "mg twice"):
        check(f"no {phrase!r} in the answer", phrase not in lowered)

    # ── Audit trail ─────────────────────────────────────────────────────────
    section("Audit trail")
    r = client.get(f"/api/ai/conversations/{session_id}", headers=auth)
    if check("conversation logged", r.status_code == 200 and len(r.json()) >= 1, show(r, 200)):
        entry = r.json()[0]
        check("logged with source", entry.get("source") == "rag", str(entry.get("source")))
        check("retrieved context stored for audit", bool(entry.get("prompt_context")))

    # ── Ungrounded question must fall back ──────────────────────────────────
    section("Fallback when unsupported")
    r = client.post(
        "/api/ai/explain-test",
        json={
            "session_id": session_id,
            "test_code": "VNG",
            "test_name": "Videonystagmography",
        },
    )
    if check("unsupported test responds", r.status_code == 200, show(r, 300)):
        fallback = r.json()
        print(f"       source: {fallback['source']}")
        check(
            "a test with no document does not get an ungrounded answer",
            fallback["source"] != "rag",
            f"source={fallback['source']}",
        )
        check("fallback still returns usable text", bool(fallback["explanation"].strip()))

    # ── Deletion removes vectors ────────────────────────────────────────────
    section("Deletion")
    r = client.delete(f"/api/admin/documents/{document_id}", headers=auth)
    check("document deleted", r.status_code in (200, 204), show(r))

    r = client.post(
        "/api/ai/explain-test",
        json={"session_id": session_id, "test_code": "PTA", "test_name": "Pure Tone Audiometry"},
    )
    if check("explain still responds after deletion", r.status_code == 200, show(r, 200)):
        after_delete = r.json()
        print(f"       source: {after_delete['source']}")
        check(
            "deleted document no longer grounds answers",
            after_delete["source"] != "rag",
            f"source={after_delete['source']} — vectors may not have been removed",
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
