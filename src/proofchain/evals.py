"""Reproducible synthetic admission evaluation runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .admission import AdmissionRequest, evaluate
from .policy import AdmissionPolicy


def run_evaluation(policy: AdmissionPolicy, fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    correct = 0
    false_allows = 0
    false_denies = 0
    for index, fixture in enumerate(fixtures, start=1):
        fixture_id = str(fixture.get("id") or f"fixture-{index}")
        expected = bool(fixture["expected_allowed"])
        decision = evaluate(AdmissionRequest.from_dict(fixture["request"]), policy)
        matched = decision.allowed == expected
        correct += int(matched)
        false_allows += int(not expected and decision.allowed)
        false_denies += int(expected and not decision.allowed)
        results.append(
            {
                "id": fixture_id,
                "expected_allowed": expected,
                "actual_allowed": decision.allowed,
                "matched": matched,
                "reason_codes": list(decision.reason_codes),
                "content_sha256": decision.content_sha256,
            }
        )
    total = len(fixtures)
    return {
        "schema_version": 1,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "false_allows": false_allows,
        "false_denies": false_denies,
        "results": results,
        "raw_content_in_report": False,
    }


def load_fixtures(path: str | Path) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Evaluation fixtures must be a JSON array")
    return value

