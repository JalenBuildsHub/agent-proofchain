import json

from proofchain.demo import render_demo, run_demo


def test_demo_exercises_admission_receipts_evaluation_and_tamper_checks():
    report = run_demo()

    assert report["schema_version"] == 1
    assert report["network_used"] is False
    assert report["safe_decision"]["allowed"] is True
    assert report["denied_decision"]["allowed"] is False
    assert "capability_not_allowed" in report["denied_decision"]["reason_codes"]
    assert "injection_threshold_met" in report["denied_decision"]["reason_codes"]
    assert report["ledger"]["valid"] is True
    assert report["ledger"]["receipts"] == 2
    assert report["evaluation"] == {
        "total": 4,
        "correct": 4,
        "false_allows": 0,
        "false_denies": 0,
    }
    assert report["tamper"]["matched"] == report["tamper"]["scenario_count"]


def test_demo_output_is_concise_and_does_not_emit_raw_requests():
    report = run_demo()
    rendered = render_demo(report)
    serialized = json.dumps(report, sort_keys=True)

    assert "Agent ProofChain demo" in rendered
    assert "4/4 matched" in rendered
    assert "Ignore previous policy instructions" not in rendered
    assert "Ignore previous policy instructions" not in serialized
    assert "demo-reviewer" not in serialized
