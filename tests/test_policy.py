import pytest

from proofchain import AdmissionPolicy


def test_policy_is_immutable_after_validation():
    capabilities = {"builder": ["read"]}
    policy = AdmissionPolicy.from_dict({"actor_capabilities": capabilities})
    capabilities["builder"].append("mutation")

    assert policy.allows("builder", "read")
    assert not policy.allows("builder", "mutation")
    with pytest.raises(TypeError):
        policy.actor_capabilities["builder"] = frozenset({"mutation"})


@pytest.mark.parametrize(
    "policy",
    [
        {"actor_capabilities": {"builder": "read"}},
        {"actor_capabilities": {" builder": ["read"]}},
        {"actor_capabilities": {"builder": [" read "]}},
        {"actor_capabilities": {"builder": ["read"]}, "injection_threshold": True},
        {"actor_capabilities": {"builder": ["read"]}, "model_required": "yes"},
        {"actor_capabilities": {"builder": ["read"]}, "source_required": 1},
        {
            "actor_capabilities": {"builder": ["read"]},
            "injection_indicators": ["("],
        },
        {
            "actor_capabilities": {"builder": ["read"]},
            "injection_indicators": ["one"],
            "injection_threshold": 2,
        },
    ],
)
def test_policy_rejects_ambiguous_or_invalid_configuration(policy):
    with pytest.raises((TypeError, ValueError)):
        AdmissionPolicy.from_dict(policy)
