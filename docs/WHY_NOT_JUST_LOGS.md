# Why not just use logs?

Logs are necessary. They are not the same thing as verifiable admission evidence.

## Ordinary logs usually answer

- which application emitted an event;
- what message the application chose to record;
- when the event reached a logging system;
- which tool call or error occurred.

## Agent ProofChain is designed to answer

- which authenticated host context was used for the admission request;
- which capability the agent requested;
- which policy checks allowed or denied it;
- which reason codes were produced;
- whether stored decision receipts still form the expected chain;
- whether another verifier can check exported evidence without the original UI.

## Comparison

| Property | Application logs | Agent ProofChain receipts |
|---|---|---|
| Primary purpose | Operations and debugging | Admission evidence |
| Schema | Application-specific | Versioned receipt contract |
| Default privacy | Often includes plaintext | Caller-controlled fields are digested |
| Authorization semantics | Usually implicit | Explicit capability decision and reasons |
| Tamper evidence | Depends on logging system | Local hash chain, with documented limits |
| Independent verification | Often requires vendor access | Intended to support portable verification |
| Tool execution | Records what app says occurred | Does not execute tools |
| Final truncation detection | Vendor-dependent | Requires future external checkpoint |

## Use both

A production system should retain operational logs for debugging and service health while using admission receipts for authority and evidence. Correlation identifiers can connect the two systems under an approved privacy and retention policy.

Do not copy raw private prompts or credentials into either system merely to make correlation easier.
