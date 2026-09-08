import pytest

from proofchain import (
    AdapterContractError,
    AnthropicAdapter,
    AuthenticatedRuntimeContext,
    GoogleAdapter,
    LocalRuntimeAdapter,
    MappingRuntimeAdapter,
    OpenAIAdapter,
)
from proofchain.adapters import RuntimeAdapter


def context(provider="openai", **overrides):
    values = {
        "provider": provider,
        "claimed_actor": "authenticated-builder",
        "actor_family": "builder",
        "runtime_family": "builder",
        "model": "trusted-model",
        "source": "trusted-runtime",
        "provider_request_id": "req-test",
    }
    values.update(overrides)
    return AuthenticatedRuntimeContext(**values)


def test_mapping_adapter_uses_trusted_identity_and_runtime_context():
    adapter = MappingRuntimeAdapter(provider="openai")
    normalized = adapter.normalize(
        {
            "claimed_actor": "spoofed-actor",
            "actor_family": "reviewer",
            "runtime_family": "spoofed-family",
            "model": "spoofed-model",
            "source": "spoofed-source",
            "capability": "read",
            "action": "inspect",
            "content": "Review the fixture.",
        },
        context(),
    )

    assert isinstance(adapter, RuntimeAdapter)
    assert normalized.request.claimed_actor == "authenticated-builder"
    assert normalized.request.actor_family == "builder"
    assert normalized.request.runtime_family == "builder"
    assert normalized.request.model == "trusted-model"
    assert normalized.request.source == "trusted-runtime"
    assert normalized.provider_request_id == "req-test"


@pytest.mark.parametrize(
    ("adapter", "provider"),
    [
        (OpenAIAdapter(), "openai"),
        (AnthropicAdapter(), "anthropic"),
        (GoogleAdapter(), "google"),
        (LocalRuntimeAdapter(), "local"),
    ],
)
def test_named_adapters_bind_provider(adapter, provider):
    normalized = adapter.normalize(
        {"capability": "read", "action": "inspect"},
        context(provider=provider),
    )
    assert normalized.provider == provider


def test_adapter_rejects_provider_context_mismatch():
    adapter = AnthropicAdapter()
    with pytest.raises(AdapterContractError, match="does not match context provider"):
        adapter.normalize({}, context(provider="openai"))


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"capability": "read"},
        {"action": "inspect"},
        {"capability": ["read"], "action": "inspect"},
        {"capability": "read", "action": {"name": "inspect"}},
        {"capability": " read ", "action": "inspect"},
    ],
)
def test_adapter_rejects_missing_or_ambiguous_task_intent(payload):
    with pytest.raises(AdapterContractError):
        OpenAIAdapter().normalize(payload, context())


@pytest.mark.parametrize(
    "field",
    ["provider", "claimed_actor", "actor_family", "runtime_family", "source"],
)
def test_context_requires_nonempty_trusted_fields(field):
    values = {
        "provider": "local",
        "claimed_actor": "builder",
        "actor_family": "builder",
        "runtime_family": "builder",
        "model": "local-model",
        "source": "local-runtime",
    }
    values[field] = " "
    with pytest.raises(AdapterContractError):
        AuthenticatedRuntimeContext(**values)


def test_context_rejects_surrounding_whitespace_and_non_string_values():
    with pytest.raises(AdapterContractError):
        context(source=" trusted-runtime ")
    with pytest.raises(AdapterContractError):
        context(claimed_actor=123)
