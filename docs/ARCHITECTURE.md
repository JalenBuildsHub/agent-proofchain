# Architecture

Agent ProofChain separates admission, evidence, and execution so the package can remain small and independently testable.

## Components

```text
provider or local event
        |
        v
runtime adapter contract
        |
        v
AdmissionRequest + authenticated host context
        |
        v
pure policy evaluation
        |
        +--> allow / deny + reason codes
        |
        v
privacy-safe receipt projection
        |
        v
SQLite hash-chained ledger
        |
        +--> local verification
        +--> evaluation evidence
        +--> future external checkpoint
```

## Trust boundaries

### Untrusted request payload

The caller may provide task intent:

- requested capability;
- action;
- content to inspect;
- non-authoritative task metadata.

The payload must not establish its own trusted identity, runtime family, model attribution, source, or provider request identity.

### Authenticated host context

The integrating host is responsible for authenticating and supplying:

- provider;
- claimed actor;
- actor family;
- runtime family;
- model attribution when available;
- source;
- provider request identity when available.

Agent ProofChain currently accepts that context from the host. It does not cryptographically validate provider transports or issue credentials.

### Policy evaluator

Admission evaluation is a pure local decision based on:

- identity-family consistency;
- capability grants;
- model-attribution requirements;
- content size;
- configured injection indicators and threshold.

Default behavior is deny when any reason code is produced.

### Receipt projection

The receipt stores safe decision facts and SHA-256 digests of caller-controlled metadata. It intentionally omits raw content, actor names, actions, models, and sources.

The digest design supports correlation and integrity checks but does not provide confidentiality against guessing low-entropy values. Integrators must avoid treating hashes of predictable identifiers as anonymous data.

### Ledger

The local SQLite ledger links each receipt to the previous receipt hash. It detects mutation and middle-row deletion. It cannot prove that the final row was not removed without an external trusted checkpoint.

## Execution boundary

Agent ProofChain does not execute tools. After an allow decision, the host still owns:

- credential scoping;
- process and filesystem isolation;
- target authorization;
- transaction approval;
- network policy;
- timeout and resource control;
- rollback;
- audit retention.

An allow decision means the request passed the configured admission policy. It is not a guarantee that the requested action is safe, correct, or successful.

## Evaluation boundary

The synthetic corpus validates deterministic behavior and reason-code contracts. It is useful for regression testing and integration conformance. It is not a production security certification or evidence of broad prompt-injection coverage.

## Extension points

Safe extension points include:

- provider-specific packages implementing the runtime adapter protocol;
- policy backends that preserve deterministic, reviewable semantics;
- alternative receipt stores implementing a documented verifier contract;
- external checkpoint services;
- cross-language verifiers;
- independent fixture packs.

Extensions should remain replaceable. The core should not require a hosted service or a specific model provider.
