"""Deterministic receipt-ledger tamper evaluation."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

from .admission import AdmissionRequest, evaluate
from .ledger import ReceiptLedger
from .policy import AdmissionPolicy


def _seed_ledger(path: Path, count: int = 3) -> ReceiptLedger:
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    ledger = ReceiptLedger(path)
    for index in range(count):
        request = AdmissionRequest(
            claimed_actor=f"synthetic-builder-{index}",
            actor_family="builder",
            runtime_family="builder",
            capability="read",
            action="inspect_synthetic_fixture",
            model="synthetic-model",
            content={"fixture": index},
            source="tamper-evaluation",
        )
        ledger.append(evaluate(request, policy))
    return ledger


def _run_scenario(name: str, mutation: str, expected_detected: bool) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="proofchain-tamper-") as directory:
        path = Path(directory) / "ledger.db"
        ledger = _seed_ledger(path)
        baseline = ledger.verify()
        with closing(sqlite3.connect(path)) as conn:
            conn.execute(mutation)
            conn.commit()
        verification = ledger.verify()
        detected = not bool(verification["valid"])
        return {
            "id": name,
            "expected_detected": expected_detected,
            "actual_detected": detected,
            "matched": detected == expected_detected,
            "baseline_valid": bool(baseline["valid"]),
            "verification": verification,
        }


def run_tamper_evaluation() -> dict[str, Any]:
    """Exercise mutations the local hash chain can and cannot detect.

    Deleting the final receipt is deliberately expected to remain undetected without an
    external signed checkpoint. Reporting that limitation is part of the benchmark.
    """

    scenarios = [
        _run_scenario(
            "payload-edit",
            "UPDATE receipts SET payload_json = '{}' WHERE sequence = 2",
            True,
        ),
        _run_scenario(
            "previous-hash-edit",
            "UPDATE receipts SET previous_hash = 'forged' WHERE sequence = 2",
            True,
        ),
        _run_scenario(
            "receipt-hash-edit",
            "UPDATE receipts SET receipt_hash = "
            "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' "
            "WHERE sequence = 2",
            True,
        ),
        _run_scenario(
            "middle-row-deletion",
            "DELETE FROM receipts WHERE sequence = 2",
            True,
        ),
        _run_scenario(
            "final-row-truncation",
            "DELETE FROM receipts WHERE sequence = 3",
            False,
        ),
    ]
    matched = sum(bool(item["matched"]) for item in scenarios)
    return {
        "schema_version": 1,
        "scenario_count": len(scenarios),
        "matched": matched,
        "all_expected_outcomes_matched": matched == len(scenarios),
        "scenarios": scenarios,
        "limitation": (
            "A local hash chain detects mutation and middle deletion but cannot prove that the "
            "latest receipt was not truncated without an external signed checkpoint."
        ),
    }


def render_tamper_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Agent ProofChain ledger tamper report",
        "",
        f"- Scenarios: **{report['scenario_count']}**",
        f"- Expected outcomes matched: **{report['matched']} / {report['scenario_count']}**",
        "",
        "| Scenario | Expected detected | Actual detected | Matched |",
        "|---|---:|---:|---:|",
    ]
    for scenario in report["scenarios"]:
        lines.append(
            f"| {scenario['id']} | {str(scenario['expected_detected']).lower()} | "
            f"{str(scenario['actual_detected']).lower()} | "
            f"{str(scenario['matched']).lower()} |"
        )
    lines.extend(["", f"**Known limitation:** {report['limitation']}", ""])
    return "\n".join(lines)


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
