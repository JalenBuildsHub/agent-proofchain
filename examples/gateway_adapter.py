"""Minimal host-gateway example with authenticated context and a local receipt ledger.

This example does not authenticate a real provider. Replace ``authenticate_transport`` with a
transport-specific implementation that verifies credentials, signatures, or another trusted
runtime binding before constructing ``AuthenticatedRuntimeContext``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from proofchain import AuthenticatedRuntimeContext, OpenAIAdapter
from proofchain.admission import evaluate
from proofchain.ledger import ReceiptLedger
from proofchain.policy import AdmissionPolicy


def authenticate_transport(headers: dict[str, str]) -> AuthenticatedRuntimeContext:
    """Return trusted context after host authentication.

    The hard-coded values make this example runnable. They are not an authentication mechanism.
    """

    if headers.get("x-demo-auth") != "synthetic-valid-transport":
        raise PermissionError("transport authentication failed")
    return AuthenticatedRuntimeContext(
        provider="openai",
        claimed_actor="authenticated-demo-worker",
        actor_family="reviewer",
        runtime_family="reviewer",
        model="host-verified-model-id",
        source="example-agent-gateway",
        provider_request_id=headers.get("x-provider-request-id"),
    )


def admit(payload: dict[str, Any], headers: dict[str, str], ledger_path: str | Path) -> dict[str, Any]:
    context = authenticate_transport(headers)
    normalized = OpenAIAdapter().normalize(payload, context)
    policy = AdmissionPolicy.from_dict(
        {
            "actor_capabilities": {"reviewer": ["read", "advisory"]},
            "model_required": True,
            "injection_threshold": 2,
            "injection_indicators": [
                "ignore .*?(previous|system).*?(instructions|policy)",
                "bypass .*?(approval|audit|guardrail)",
                "do not (log|audit|report)",
            ],
        }
    )
    decision = evaluate(normalized.request, policy)
    receipt = ReceiptLedger(ledger_path).append(decision)
    return {
        "allowed": decision.allowed,
        "reason_codes": list(decision.reason_codes),
        "provider": normalized.provider,
        "provider_request_id": normalized.provider_request_id,
        "receipt_hash": receipt["receipt_hash"],
    }


if __name__ == "__main__":
    result = admit(
        {
            "capability": "read",
            "action": "inspect_repository",
            "content": {"paths": ["README.md"]},
            "claimed_actor": "payload-cannot-override-authenticated-context",
        },
        {
            "x-demo-auth": "synthetic-valid-transport",
            "x-provider-request-id": "synthetic-provider-request-1",
        },
        "gateway-example.db",
    )
    print(result)
