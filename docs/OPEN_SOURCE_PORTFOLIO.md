# Jalen Builds Studio open-source portfolio

The studio should build public traction through one coherent trust portfolio, not a
collection of unmaintained repository fragments.

## Flagship

**Agent ProofChain** is the umbrella project:

> Make autonomous-agent actions attributable, policy-checked, bounded, and independently verifiable.

Initial module path:

```text
agent-proofchain/
  src/proofchain/       provider-neutral policy and receipts
  contracts/            handoff, decision, stop, validation, and closeout types
  containment/          process, filesystem, network, and worktree assertions
  evals/                injection, spoofing, unauthorized-action, and tamper tests
  harness/              bounded self-improvement with immutable evaluators
  adapters/             thin MCP, OpenAI, Anthropic, Google, and local adapters
  fixtures/             synthetic identities, prompts, repositories, and incidents
```

Keep one repository through early adoption so users understand the system and maintainers
can enforce one security, release, and compatibility contract.

## Candidate modules

### First wave

1. Typed agent contracts: handoff, decision card, door classification, stop tuple, and return receipt.
2. Bounded self-improvement harness: immutable program/evaluator boundary with synthetic examples.
3. Agent safety evaluation kit: model-neutral spoofing, injection, unauthorized action, and audit tests.
4. Containment verifier: assertions for worktree, process, filesystem, and network boundaries.
5. One-writer worktree guard: portable collision detection for agent teams.

### Later adjacent packages

- `launchproof`: evidence-backed release and launch-readiness verifier.
- `proofchain-web`: seven-layer discoverability evidence schema and validator.
- Knowledge Hub engine: portable retrieval/indexing code with an entirely synthetic corpus.

These should spin out only after Agent ProofChain has users who need them independently.

## Keep private

- Live studio task bus, inboxes, claims, handoffs, heartbeats, and event history.
- Production identity registry, admission configuration, trust thresholds, and quarantine records.
- Runtime recovery, application restart, and workstation maintenance machinery.
- Provider/model routing, operator authority, protected-action grants, and billing/account topology.
- Revenue, customer, deployment, marketing, audit, and project reports.
- Curated and raw studio knowledge content.
- Private prompts, incidents, customer data, local paths, credentials, and live telemetry.

Public credibility comes from synthetic attack cases, reproducible benchmarks, signed releases,
transparent limitations, outside contributors, and responsible disclosure—not production access.

## Extraction gate

Every public module requires:

1. Clean-room boundary and provenance inventory.
2. Generic names, paths, identities, and fixtures.
3. License and third-party dependency review.
4. Secret, private-path, and private-prompt scan.
5. Threat model and explicit non-goals.
6. Windows and Linux tests.
7. Maintainer and support commitment.
8. Independent technical review before public release.

