import json

from proofchain.evals import (
    load_fixtures,
    render_evaluation_markdown,
    run_evaluation,
)
from proofchain.policy import AdmissionPolicy


def test_synthetic_v01_pilot_matches_expected_outcomes():
    policy = AdmissionPolicy.from_json("examples/policy.json")
    fixtures = load_fixtures("evals/synthetic-v0.1.json")
    result = run_evaluation(policy, fixtures)
    assert result["total"] == 20
    assert result["correct"] == 20
    assert result["false_allows"] == 0
    assert result["false_denies"] == 0
    assert result["raw_content_in_report"] is False


def test_v02_reports_confusion_metrics_categories_and_latency():
    policy = AdmissionPolicy.from_json("examples/policy.json")
    fixtures = load_fixtures("evals/synthetic-v0.2.json")
    result = run_evaluation(policy, fixtures)

    assert result["schema_version"] == 2
    assert result["summary"]["total"] == 40
    assert result["summary"]["correct"] == 40
    assert result["metrics"]["false_allow_rate"] == 0.0
    assert result["metrics"]["false_deny_rate"] == 0.0
    assert result["metrics"]["allow_precision"] == 1.0
    assert result["metrics"]["deny_recall"] == 1.0
    assert result["latency_ns"]["minimum"] >= 0
    assert result["latency_ns"]["p95"] >= result["latency_ns"]["minimum"]
    assert "threshold-boundary" in result["categories"]
    assert result["benchmark"]["fixture_sha256"]


def test_reason_code_assertions_fail_a_fixture_without_exposing_content():
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    fixtures = [
        {
            "id": "reason-contract",
            "category": "contract",
            "expected_allowed": True,
            "expected_reason_codes": ["not-present"],
            "request": {
                "claimed_actor": "builder",
                "actor_family": "builder",
                "runtime_family": "builder",
                "capability": "read",
                "action": "inspect",
                "model": "model-a",
                "content": "private prompt body",
            },
        }
    ]
    result = run_evaluation(policy, fixtures)
    assert result["correct"] == 0
    assert result["results"][0]["classification_matched"] is True
    assert result["results"][0]["missing_expected_reason_codes"] == ["not-present"]
    assert "private prompt body" not in json.dumps(result)


def test_markdown_report_is_human_readable_and_private():
    policy = AdmissionPolicy.from_json("examples/policy.json")
    result = run_evaluation(policy, load_fixtures("evals/synthetic-v0.2.json"))
    markdown = render_evaluation_markdown(result)
    assert "# Agent ProofChain evaluation report" in markdown
    assert "False allows: **0**" in markdown
    assert "private prompt" not in markdown


def test_evaluation_report_omits_request_metadata_plaintext():
    private_family = "C:/Users/private/runtime-family"
    private_capability = "token=private-capability"
    policy = AdmissionPolicy.from_dict(
        {"actor_capabilities": {private_family: [private_capability]}}
    )
    fixtures = [
        {
            "id": "private-metadata-proof",
            "expected_allowed": True,
            "request": {
                "claimed_actor": "secret-user@example.com",
                "actor_family": private_family,
                "runtime_family": private_family,
                "capability": private_capability,
                "action": "password=raw-secret",
                "model": "customer-private-model",
                "source": "C:/Users/private/customer-path",
                "content": "private prompt body",
            },
        }
    ]

    serialized = json.dumps(run_evaluation(policy, fixtures), sort_keys=True)

    for private_value in fixtures[0]["request"].values():
        assert private_value not in serialized


def test_load_fixtures_rejects_missing_contract(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('[{"id": "missing-request"}]', encoding="utf-8")
    try:
        load_fixtures(path)
    except ValueError as exc:
        assert "requires expected_allowed and request" in str(exc)
    else:
        raise AssertionError("invalid fixture should fail")


def test_load_fixtures_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text(
        json.dumps(
            [
                {"id": "same", "expected_allowed": True, "request": {}},
                {"id": "same", "expected_allowed": False, "request": {}},
            ]
        ),
        encoding="utf-8",
    )
    try:
        load_fixtures(path)
    except ValueError as exc:
        assert "Duplicate fixture id" in str(exc)
    else:
        raise AssertionError("duplicate fixture ids should fail")


def test_load_fixtures_rejects_nonboolean_expected_value(tmp_path):
    path = tmp_path / "bad-bool.json"
    path.write_text(
        json.dumps([{"id": "bad", "expected_allowed": "false", "request": {}}]),
        encoding="utf-8",
    )
    try:
        load_fixtures(path)
    except TypeError as exc:
        assert "must be a boolean" in str(exc)
    else:
        raise AssertionError("non-boolean expected_allowed should fail")
