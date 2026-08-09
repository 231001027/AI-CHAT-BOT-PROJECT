#!/usr/bin/env python3
"""Smoke-test all HearConnect FastAPI endpoints."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any, Callable

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def req(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    with urllib.request.urlopen(request, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode())


def main() -> int:
    failures = 0
    print(f"Testing {BASE}", flush=True)

    checks: list[tuple[str, str, dict | None, Callable[[Any], bool]]] = [
        ("GET", "/health", None, lambda d: d.get("status") == "ok"),
        ("POST", "/api/chat", {"message": "I have tinnitus ringing"}, lambda d: "response" in d),
        ("GET", "/api/hearing-problems", None, lambda d: isinstance(d, list) and len(d) > 0),
        ("GET", "/api/adult-sections", None, lambda d: isinstance(d, list) and len(d) > 0),
        ("GET", "/api/special-tests", None, lambda d: isinstance(d, list) and len(d) > 0),
        ("GET", "/api/child-categories", None, lambda d: isinstance(d, list) and len(d) > 0),
        (
            "POST",
            "/api/assessments",
            {
                "full_name": "Test User",
                "district": "Chennai",
                "age": 32,
                "gender": "female",
                "audience": "myself",
                "routed_to": "adult-care",
            },
            lambda d: "id" in d,
        ),
        (
            "POST",
            "/api/contact",
            {
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Hello",
                "message": "Testing contact form",
            },
            lambda d: d.get("status") == "received",
        ),
    ]

    for method, path, body, ok in checks:
        try:
            status, data = req(method, path, body)
            passed = 200 <= status < 300 and ok(data)
            mark = "PASS" if passed else "FAIL"
            print(f"[{mark}] {method} {path} → {status}", flush=True)
            if not passed:
                failures += 1
                print("      ", data, flush=True)
        except urllib.error.URLError as exc:
            print(f"[FAIL] {method} {path} → {exc}", flush=True)
            failures += 1

    try:
        status, session = req(
            "POST",
            "/api/chat-sessions",
            {"topic_id": "tinnitus", "topic_title": "Ringing in Ears"},
        )
        assert 200 <= status < 300 and "id" in session
        session_id = session["id"]
        print(f"[PASS] POST /api/chat-sessions → {status} id={session_id}", flush=True)

        status, msg = req(
            "POST",
            "/api/chat-messages",
            {
                "session_id": session_id,
                "role": "user",
                "message": "It is constant",
                "question_index": 0,
            },
        )
        assert 200 <= status < 300 and "id" in msg
        print(f"[PASS] POST /api/chat-messages → {status}", flush=True)
    except Exception as exc:
        print(f"[FAIL] chat session flow → {exc}", flush=True)
        failures += 1

    print(flush=True)
    if failures:
        print(f"{failures} check(s) failed.", flush=True)
        return 1
    print("All checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
