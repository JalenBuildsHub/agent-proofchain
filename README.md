# Agent ProofChain

Agent ProofChain is a provider-neutral safety and evidence layer for AI-agent systems.
It evaluates an agent's claimed identity and requested capability before work begins,
detects common instruction-injection combinations, and writes tamper-evident receipts
for every allow or deny decision.

The project is deliberately small. It does not execute agents, manage credentials, or
pretend that prompt scanning is authentication. Use it beside real process isolation,
short-lived credentials, scoped worktrees, and human-controlled enrollment.

## Why this exists

Multi-agent teams need answers to five ordinary questions:

1. Who requested the action?
2. Which model and runtime made the request?
3. Was that identity allowed to use the requested capability?
4. Did the request contain injection-shaped instructions?
5. Can the resulting record be verified later?

Agent ProofChain makes those answers portable and testable across OpenAI, Anthropic,
Google, local, and other model runtimes.

## Quick start

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
proofchain evaluate --policy examples/policy.json --request examples/safe-request.json --ledger proofchain.db
proofchain verify --ledger proofchain.db
proofchain eval --policy examples/policy.json --fixtures evals/synthetic-v0.2.json --output artifacts/eval-v0.2.json --markdown-output artifacts/eval-v0.2.md
proofchain tamper-eval --output artifacts/tamper-v0.2.json --markdown-output artifacts/tamper-v0.2.md
pytest
```

An injection-shaped example should be denied:

```bash
proofchain evaluate --policy examples/policy.json --request examples/injection-request.json --ledger proofchain.db
```

## Core guarantees

- Default-deny capability policy.
- Claimed actor family must match the authenticated runtime family supplied by the host.
- Model, runtime, actor, capability, action, source, and content are recorded as
  SHA-256 digests alongside the decision and safe reason codes.
- Caller-controlled request fields are not written to the ledger in plaintext.
- Receipt rows form a SHA-256 hash chain that can be verified independently.
- Synthetic evaluation fixtures cover spoofing, unauthorized mutation, injection, missing
  model attribution, reason-code contracts, threshold boundaries, and ledger tampering.

## v0.2 evaluation foundation

The portable evaluation pilot currently includes:

- a 40-case synthetic corpus grouped by identity, authorization, attribution, injection,
  threshold-boundary, benign-security-language, and compound-policy categories;
- allow and deny precision/recall, false-allow and false-deny rates, category summaries,
  reason-code assertions, and local process latency measurements;
- JSON and Markdown report output with a stable fixture digest;
- deterministic ledger mutation tests, including an explicit demonstration that final-row
  truncation cannot be detected without an external signed checkpoint;
- provider-neutral adapter contracts for OpenAI, Anthropic, Google, and local runtimes.

The named adapters are contracts, not provider SDK integrations. Hosts must authenticate
actor identity, runtime family, model attribution, source, and provider request identity
before constructing `AuthenticatedRuntimeContext`. Untrusted payloads may supply task intent,
not trusted identity.

Read [the v0.2 evaluation guide](docs/EVALUATION_V0_2.md) and
[adapter contract](docs/ADAPTER_CONTRACT.md) before extending the benchmark or integrating
a provider runtime.

## Non-goals

- Network authentication, credential issuance, or secret storage.
- Filesystem or container sandboxing.
- Guaranteed prompt-injection detection.
- Autonomous approval of unknown workers.
- Collection of private prompts or production incident transcripts.
- Security certification based on synthetic benchmark accuracy.

Read [the threat model](docs/THREAT_MODEL.md) and [limitations](docs/LIMITATIONS.md)
before integrating this into a production agent system.

The wider [studio open-source portfolio](docs/OPEN_SOURCE_PORTFOLIO.md) and
[program stack](docs/PROGRAM_STACK.md) explain how related tools can grow around the
provider-neutral core without exposing private studio infrastructure.

## Project status

`v0.1.0` is a local alpha foundation. The API may change before the first public release.
The v0.2 evaluation work remains a pre-release pilot until independent fixtures and external
review exist. See [ROADMAP.md](ROADMAP.md) and [GOVERNANCE.md](GOVERNANCE.md).
