import json
import sqlite3

import pytest

from proofchain.cli import main


def _write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_evaluate_and_verify_round_trip(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    request = tmp_path / "request.json"
    ledger = tmp_path / "ledger.db"
    _write_json(
        policy,
        {
            "actor_capabilities": {"builder": ["read"]},
            "injection_indicators": [],
        },
    )
    _write_json(
        request,
        {
            "claimed_actor": "synthetic-builder",
            "actor_family": "builder",
            "runtime_family": "builder",
            "capability": "read",
            "action": "inspect",
            "model": "synthetic-model",
            "source": "unit-test",
            "content": "Inspect a synthetic fixture.",
        },
    )

    assert (
        main(
            [
                "evaluate",
                "--policy",
                str(policy),
                "--request",
                str(request),
                "--ledger",
                str(ledger),
            ]
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["allowed"] is True

    assert main(["verify", "--ledger", str(ledger)]) == 0
    verification = json.loads(capsys.readouterr().out)
    assert verification["valid"] is True
    assert verification["receipts"] == 1


def test_denied_evaluation_returns_two_and_still_records_receipt(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    request = tmp_path / "request.json"
    ledger = tmp_path / "ledger.db"
    _write_json(policy, {"actor_capabilities": {"reviewer": ["read"]}})
    _write_json(
        request,
        {
            "claimed_actor": "synthetic-reviewer",
            "actor_family": "reviewer",
            "runtime_family": "reviewer",
            "capability": "mutation",
            "action": "edit",
            "model": "synthetic-model",
            "source": "unit-test",
        },
    )

    assert (
        main(
            [
                "evaluate",
                "--policy",
                str(policy),
                "--request",
                str(request),
                "--ledger",
                str(ledger),
            ]
        )
        == 2
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["allowed"] is False
    assert "capability_not_allowed" in receipt["reason_codes"]


def test_eval_and_tamper_commands_write_requested_reports(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    fixtures = tmp_path / "fixtures.json"
    evaluation_json = tmp_path / "evaluation.json"
    evaluation_md = tmp_path / "evaluation.md"
    tamper_json = tmp_path / "tamper.json"
    tamper_md = tmp_path / "tamper.md"
    _write_json(policy, {"actor_capabilities": {"builder": ["read"]}})
    _write_json(
        fixtures,
        [
            {
                "id": "safe",
                "expected_allowed": True,
                "request": {
                    "claimed_actor": "synthetic-builder",
                    "actor_family": "builder",
                    "runtime_family": "builder",
                    "capability": "read",
                    "action": "inspect",
                    "model": "synthetic-model",
                },
            }
        ],
    )

    assert (
        main(
            [
                "eval",
                "--policy",
                str(policy),
                "--fixtures",
                str(fixtures),
                "--output",
                str(evaluation_json),
                "--markdown-output",
                str(evaluation_md),
            ]
        )
        == 0
    )
    assert json.loads(evaluation_json.read_text(encoding="utf-8"))["correct"] == 1
    assert evaluation_md.read_text(encoding="utf-8").startswith("# Agent ProofChain")
    capsys.readouterr()

    assert (
        main(
            [
                "tamper-eval",
                "--output",
                str(tamper_json),
                "--markdown-output",
                str(tamper_md),
            ]
        )
        == 0
    )
    assert json.loads(tamper_json.read_text(encoding="utf-8"))["all_expected_outcomes_matched"]
    assert tamper_md.read_text(encoding="utf-8").startswith("# Agent ProofChain")
    capsys.readouterr()


def test_verify_reports_invalid_ledger_without_recreating_table(tmp_path, capsys):
    path = tmp_path / "ledger.db"
    with sqlite3.connect(path):
        pass

    assert main(["verify", "--ledger", str(path)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["failure"] == "missing_receipts_table"
    with sqlite3.connect(path) as conn:
        assert (
            conn.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'receipts'"
            ).fetchone()
            is None
        )


@pytest.mark.parametrize(
    "argv",
    [
        ["evaluate", "--policy", "missing", "--request", "missing", "--ledger", "ledger"],
        ["eval", "--policy", "missing", "--fixtures", "missing"],
    ],
)
def test_expected_input_errors_are_generic_and_do_not_emit_tracebacks(argv, capsys):
    assert main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "proofchain: invalid input or unreadable ledger; no action was admitted\n"
    )
    assert "Traceback" not in captured.err
