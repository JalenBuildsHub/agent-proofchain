import json

from proofchain.evals import load_fixtures, run_evaluation
from proofchain.policy import AdmissionPolicy


def test_synthetic_pilot_matches_expected_outcomes():
    policy = AdmissionPolicy.from_json("examples/policy.json")
    fixtures = load_fixtures("evals/synthetic-v0.1.json")
    result = run_evaluation(policy, fixtures)
    assert result["total"] == 20
    assert result["correct"] == 20
    assert result["false_allows"] == 0
    assert result["false_denies"] == 0
    assert result["raw_content_in_report"] is False


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
