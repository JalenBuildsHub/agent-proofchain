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

