# Vision: verifiable authority for agent work

## The problem

Agent systems increasingly perform consequential work across repositories, cloud infrastructure, communications, payments, business operations, and private data. Their authorization, model metadata, tool calls, and logs often live in unrelated systems and cannot be independently reconciled later.

A log can say that an action happened. It usually cannot prove:

- which authenticated runtime requested it;
- what capability that runtime held at the time;
- which policy produced the decision;
- whether the evidence was rewritten or truncated later;
- whether another implementation can verify the record without trusting the original dashboard.

## The end state

Agent ProofChain aims to provide a narrow, provider-neutral protocol for two moments.

### Before an action

- normalize task intent from a provider or local runtime;
- bind identity and attribution to authenticated host context;
- evaluate the requested capability under an explicit policy;
- fail closed when identity, attribution, authority, or policy integrity is insufficient.

### After an action decision

- create a privacy-safe receipt;
- link it to prior receipts or an external checkpoint;
- preserve reason codes and versioned evidence;
- allow independent verification without requiring the original agent framework.

The intended architecture is:

```text
agent or worker
    -> authenticated host or gateway
    -> Agent ProofChain admission decision
    -> isolated tool execution owned by the host
    -> tamper-evident receipt
    -> external checkpoint or verifier
```

Agent ProofChain does not execute tools and should not become an all-in-one agent platform.

## Open-core boundary

The open project should contain the parts that benefit from inspection and independent implementation:

- request and receipt specifications;
- deterministic policy evaluation;
- local hash-chained receipts;
- independent verification;
- conformance and adversarial evaluation;
- provider-neutral adapter contracts;
- test vectors and compatibility documentation.

Commercial or hosted systems may eventually exist around the core:

- managed runtime gateways;
- organizational identity and policy administration;
- signed external checkpoints;
- searchable evidence consoles;
- enterprise adapters;
- retention, export, and compliance workflows.

A hosted system must not become the only way to verify an exported receipt.

## Success criteria

The project is succeeding when:

1. independent teams can install and evaluate it without studio assistance;
2. external contributors author fixtures and identify false confidence;
3. multiple runtimes produce compatible admission requests and receipts;
4. receipt verifiers exist outside the primary Python implementation;
5. organizations require verifiable authority evidence before agents mutate valuable systems;
6. public claims remain narrower than demonstrated evidence.

GitHub stars can amplify discovery, but compatible implementations, external receipts, and real review are the durable measures.
