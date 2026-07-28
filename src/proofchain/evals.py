"""Reproducible synthetic admission evaluation runner."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from .admission import AdmissionRequest, evaluate
from .policy import AdmissionPolicy


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))
    return ordered[index]


def _fixture_digest(fixtures: list[dict[str, Any]]) -> str:
    canonical = json.dumps(fixtures, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _category_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(row)

    summary: dict[str, dict[str, Any]] = {}
    for category, items in sorted(grouped.items()):
        matched = sum(bool(item["matched"]) for item in items)
        summary[category] = {
            "total": len(items),
            "matched": matched,
            "accuracy": matched / len(items),
            "false_allows": sum(
                not item["expected_allowed"] and item["actual_allowed"] for item in items
            ),
            "false_denies": sum(
                item["expected_allowed"] and not item["actual_allowed"] for item in items
            ),
        }
    return summary


def run_evaluation(policy: AdmissionPolicy, fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    """Run deterministic decisions and produce a privacy-safe benchmark report.

    Timing data describes this process and machine only. It is not a service-level guarantee.
    The report never includes request content or caller-controlled identity metadata.
    """

    results: list[dict[str, Any]] = []
    latencies_ns: list[int] = []
    true_allows = true_denies = false_allows = false_denies = 0
    reason_counts: Counter[str] = Counter()

    for index, fixture in enumerate(fixtures, start=1):
        fixture_id = str(fixture.get("id") or f"fixture-{index}")
        category = str(fixture.get("category") or "uncategorized")
        expected = bool(fixture["expected_allowed"])
        started = perf_counter_ns()
        decision = evaluate(AdmissionRequest.from_dict(fixture["request"]), policy)
        latency_ns = perf_counter_ns() - started
        latencies_ns.append(latency_ns)

        classification_matched = decision.allowed == expected
        expected_reasons = {str(item) for item in fixture.get("expected_reason_codes", [])}
        forbidden_reasons = {str(item) for item in fixture.get("forbidden_reason_codes", [])}
        actual_reasons = set(decision.reason_codes)
        missing_expected = sorted(expected_reasons - actual_reasons)
        present_forbidden = sorted(forbidden_reasons & actual_reasons)
        assertions_matched = (
            classification_matched and not missing_expected and not present_forbidden
        )

        true_allows += int(expected and decision.allowed)
        true_denies += int(not expected and not decision.allowed)
        false_allows += int(not expected and decision.allowed)
        false_denies += int(expected and not decision.allowed)
        reason_counts.update(decision.reason_codes)

        results.append(
            {
                "id": fixture_id,
                "category": category,
                "expected_allowed": expected,
                "actual_allowed": decision.allowed,
                "matched": assertions_matched,
                "classification_matched": classification_matched,
                "missing_expected_reason_codes": missing_expected,
                "present_forbidden_reason_codes": present_forbidden,
                "reason_codes": list(decision.reason_codes),
                "injection_matches": list(decision.injection_matches),
                "content_sha256": decision.content_sha256,
                "latency_ns": latency_ns,
            }
        )

    total = len(fixtures)
    correct = sum(bool(row["matched"]) for row in results)
    predicted_allows = true_allows + false_allows
    predicted_denies = true_denies + false_denies
    expected_allows = true_allows + false_denies
    expected_denies = true_denies + false_allows

    return {
        "schema_version": 2,
        "benchmark": {
            "fixture_count": total,
            "fixture_sha256": _fixture_digest(fixtures),
            "raw_content_in_report": False,
            "positive_class_note": (
                "Both allow and deny metrics are reported; no single class is privileged."
            ),
        },
        "summary": {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total else 0.0,
            "true_allows": true_allows,
            "true_denies": true_denies,
            "false_allows": false_allows,
            "false_denies": false_denies,
        },
        "metrics": {
            "allow_precision": _ratio(true_allows, predicted_allows),
            "allow_recall": _ratio(true_allows, expected_allows),
            "deny_precision": _ratio(true_denies, predicted_denies),
            "deny_recall": _ratio(true_denies, expected_denies),
            "false_allow_rate": _ratio(false_allows, expected_denies),
            "false_deny_rate": _ratio(false_denies, expected_allows),
        },
        "latency_ns": {
            "minimum": min(latencies_ns, default=0),
            "median": _percentile(latencies_ns, 0.50),
            "p95": _percentile(latencies_ns, 0.95),
            "maximum": max(latencies_ns, default=0),
            "total": sum(latencies_ns),
            "measurement_note": (
                "Local process timing only; compare runs only on controlled hardware."
            ),
        },
        "categories": _category_summary(results),
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "results": results,
        "raw_content_in_report": False,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "false_allows": false_allows,
        "false_denies": false_denies,
    }


def render_evaluation_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    metrics = report["metrics"]
    latency = report["latency_ns"]

    def render_ratio(value: float | None) -> str:
        return "n/a" if value is None else f"{value:.3f}"

    lines = [
        "# Agent ProofChain evaluation report",
        "",
        f"- Fixture count: **{summary['total']}**",
        f"- Fixture SHA-256: `{report['benchmark']['fixture_sha256']}`",
        f"- Accuracy: **{summary['accuracy']:.3f}**",
        f"- False allows: **{summary['false_allows']}**",
        f"- False denies: **{summary['false_denies']}**",
        (
            f"- Allow precision / recall: **{render_ratio(metrics['allow_precision'])} / "
            f"{render_ratio(metrics['allow_recall'])}**"
        ),
        (
            f"- Deny precision / recall: **{render_ratio(metrics['deny_precision'])} / "
            f"{render_ratio(metrics['deny_recall'])}**"
        ),
        f"- Median / p95 latency: **{latency['median']} ns / {latency['p95']} ns**",
        "",
        "Timing is local process timing, not a service-level guarantee.",
        "No raw request content or caller-controlled identity metadata is included.",
        "",
        "## Category results",
        "",
        "| Category | Total | Matched | Accuracy | False allows | False denies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for category, item in report["categories"].items():
        lines.append(
            f"| {category} | {item['total']} | {item['matched']} | "
            f"{item['accuracy']:.3f} | {item['false_allows']} | {item['false_denies']} |"
        )

    mismatches = [row for row in report["results"] if not row["matched"]]
    lines.extend(["", "## Mismatches", ""])
    if not mismatches:
        lines.append("None.")
    else:
        for row in mismatches:
            lines.append(
                f"- `{row['id']}` expected allowed={row['expected_allowed']} but observed "
                f"allowed={row['actual_allowed']}; reasons={row['reason_codes']}"
            )
    return "\n".join(lines) + "\n"


def load_fixtures(path: str | Path) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError("Evaluation fixtures must be a JSON array")

    seen_ids: set[str] = set()
    for index, fixture in enumerate(value, start=1):
        if not isinstance(fixture, dict):
            raise TypeError(f"Fixture {index} must be an object")
        if "expected_allowed" not in fixture or "request" not in fixture:
            raise ValueError(f"Fixture {index} requires expected_allowed and request")
        if not isinstance(fixture["expected_allowed"], bool):
            raise TypeError(f"Fixture {index} expected_allowed must be a boolean")
        if not isinstance(fixture["request"], dict):
            raise TypeError(f"Fixture {index} request must be an object")

        fixture_id = str(fixture.get("id") or f"fixture-{index}")
        if fixture_id in seen_ids:
            raise ValueError(f"Duplicate fixture id: {fixture_id}")
        seen_ids.add(fixture_id)

        for field in ("expected_reason_codes", "forbidden_reason_codes"):
            codes = fixture.get(field, [])
            if not isinstance(codes, list) or not all(isinstance(item, str) for item in codes):
                raise TypeError(f"Fixture {fixture_id} {field} must be a string array")
    return value
