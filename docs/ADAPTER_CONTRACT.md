# Runtime adapter contract

## Purpose

Agent ProofChain stays provider-neutral by separating provider event parsing from admission
policy. A runtime adapter translates an event into an `AdmissionRequest`; it does not authenticate
the caller, issue credentials, execute tools, or prove that a model identifier is genuine.

## Trust boundary

The host application must authenticate and supply:

- provider;
- claimed actor;
- actor family;
- runtime family;
- model identifier, when available;
- source;
- provider request identifier, when available.

Those values belong in `AuthenticatedRuntimeContext`. Caller-controlled payload fields cannot
override them.

The payload may supply task intent:

- requested capability;
- action;
- content to evaluate.

This distinction prevents a payload from declaring itself to be a trusted builder, changing its
runtime family, replacing model attribution, or forging the source recorded by the host.

## Reference use

```python
from proofchain import AuthenticatedRuntimeContext, OpenAIAdapter

adapter = OpenAIAdapter()
normalized = adapter.normalize(
    {
        "capability": "read",
        "action": "inspect_repository",
        "content": {"paths": ["README.md"]},
    },
    AuthenticatedRuntimeContext(
        provider="openai",
        claimed_actor="authenticated-worker-17",
        actor_family="reviewer",
        runtime_family="reviewer",
        model="host-verified-model-id",
        source="agent-gateway",
        provider_request_id="host-request-id",
    ),
)
```

Pass `normalized.request` to the ordinary admission evaluator. Store provider request identity
outside the ProofChain receipt only when the surrounding system has an approved privacy and
retention policy.

## Named adapters

The package exposes mapping contracts for:

- `OpenAIAdapter`;
- `AnthropicAdapter`;
- `GoogleAdapter`;
- `LocalRuntimeAdapter`.

These classes do not import or call provider SDKs. They establish a consistent integration
boundary so provider-specific packages can normalize events without weakening the core.

## Provider integration requirements

A provider integration must:

1. authenticate the runtime outside Agent ProofChain;
2. derive trusted context from transport or host evidence rather than message content;
3. reject provider/context mismatches;
4. avoid copying raw private prompts into logs or receipts;
5. preserve default-deny behavior;
6. test that payload identity fields cannot override host context;
7. document which context fields are cryptographically verified, transport-authenticated,
   configuration-bound, or merely asserted by the host;
8. record model-version and adapter-version information in external evaluation evidence.

## Non-goals

The adapter contract does not provide:

- OAuth or API-key validation;
- signed provider receipts;
- nonce or replay protection;
- tool execution;
- filesystem or container isolation;
- provider endorsement or compatibility certification.

Those controls remain the responsibility of the integrating runtime and are planned separately
from the v0.2 evaluation foundation.
