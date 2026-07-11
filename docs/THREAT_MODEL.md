# Threat model

## Protected assets

- Repository contents and write ownership.
- Agent credentials, model identity, and capability grants.
- Action receipts and validation evidence.
- Private prompts, customer data, and operational configuration.

## Primary threats

1. An unknown runtime claims a trusted agent identity.
2. A read-only worker requests mutation capability.
3. An untrusted message instructs an agent to bypass policy or expose secrets.
4. A worker omits the model or source used for an action.
5. An attacker edits historical receipts to hide an unauthorized action.
6. A trusted runtime is compromised after admission.

## Controls in this package

- Default-deny capability checks.
- Actor/runtime family equality requirement.
- Combined-indicator injection detection.
- Digest-based model/source attribution in every receipt.
- SHA-256 digests instead of plaintext caller-controlled request fields.
- Hash-chained SQLite receipts with deterministic verification.

## Required controls outside this package

- Authenticate runtime identity before constructing `AdmissionRequest`.
- Use short-lived scoped credentials and replay protection for remote workers.
- Run untrusted agents under separate OS identities or containers.
- Restrict each worker to an isolated worktree and explicit network policy.
- Store signed receipt checkpoints outside the worker's administrative boundary.
