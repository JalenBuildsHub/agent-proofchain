# Agent ProofChain receipt protocol — draft

This document defines the portable receipt and local chain contract implemented by the Python package. It is a draft interoperability specification, not a standards-body publication or a stable-version promise.

Normative words such as **MUST**, **MUST NOT**, **SHOULD**, and **MAY** describe conformance expectations for this draft.

## 1. Scope

The protocol defines:

- receipt-v2 field requirements;
- privacy-sensitive field handling;
- canonical payload serialization;
- receipt-chain hashing;
- portable conformance vectors;
- local verification outcomes.

It does not define:

- network authentication;
- credential issuance;
- agent execution;
- sandboxing;
- target-system authorization;
- external checkpoint signatures;
- retention or deletion policy;
- provider endorsement.

## 2. Receipt v2

A receipt-v2 payload MUST contain exactly the fields defined by `spec/receipt-v2.schema.json`.

### Decision fields

- `schema_version` MUST equal `2`.
- `request_id` MUST be a non-empty string.
- `allowed` MUST be a JSON boolean.
- `decision` MUST equal `allow` when `allowed` is true and `deny` when false.
- `reason_codes` MUST be an array of strings.
- `injection_matches` MUST be an array of strings.

### Digest fields

The following fields MUST be lowercase, 64-character SHA-256 hexadecimal digests:

- `content_sha256`;
- `claimed_actor_sha256`;
- `actor_family_sha256`;
- `runtime_family_sha256`;
- `capability_sha256`;
- `action_sha256`;
- `model_sha256`;
- `source_sha256`.

Implementations MUST NOT add caller-controlled plaintext fields such as raw actor names, prompts, actions, model identifiers, sources, or content to the portable receipt payload.

A SHA-256 digest is an integrity and correlation primitive, not encryption or guaranteed anonymization. Predictable low-entropy values may be guessed. Integrators remain responsible for privacy, access, retention, and correlation policy.

## 3. Canonical payload JSON

The receipt hash is calculated from a canonical JSON representation of the receipt payload.

The current canonicalization contract is:

1. encode the payload as UTF-8 JSON;
2. sort object keys lexicographically;
3. use `,` between array/object members and `:` between keys and values;
4. include no insignificant whitespace;
5. preserve Unicode characters rather than escaping all non-ASCII characters;
6. serialize only values valid under receipt v2.

The Python equivalent is:

```python
json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

This draft intentionally limits receipt values to ordinary JSON types. Future protocol versions should adopt or reference a formally standardized canonicalization scheme before claiming broader interoperability across unusual numeric or Unicode edge cases.

## 4. Receipt-chain hash

The first receipt uses the literal previous hash:

```text
GENESIS
```

For each receipt, implementations MUST compute:

```text
receipt_hash = SHA256_UTF8(previous_hash + "\n" + canonical_payload_json)
```

The resulting digest is lowercase hexadecimal.

For receipt number `n + 1`, `previous_hash` MUST equal receipt `n`'s `receipt_hash`.

Sequence values MUST begin at `1` and increase by exactly one in a portable vector.

## 5. Local verification

A verifier checks:

- vector and receipt structure;
- sequence continuity;
- receipt-v2 privacy and field contract;
- `allowed` and `decision` consistency;
- digest formatting;
- previous-hash linkage;
- recomputed receipt hashes.

A valid local chain demonstrates that the presented records are internally consistent under this contract.

It does **not** prove:

- that the authenticated host told the truth;
- that an allowed action actually executed;
- that an executed action succeeded;
- that the database or export includes the latest receipt;
- that a final receipt was not deleted before verification.

Detecting final truncation requires an external trusted checkpoint, witness, signature, or transparency mechanism that records an expected chain head.

## 6. Conformance vectors

`spec/vectors/receipt-chain-v2.json` is the initial deterministic vector.

A conforming verifier SHOULD:

1. accept the unmodified vector;
2. return the exact expected final hash;
3. reject any payload mutation;
4. reject previous-hash mutation;
5. reject receipt-hash mutation;
6. reject sequence gaps;
7. reject plaintext caller-controlled fields;
8. reject `allowed` / `decision` conflicts;
9. reject malformed digest values;
10. return machine-readable errors.

The bundled command is:

```bash
proofchain conformance --vector spec/vectors/receipt-chain-v2.json
```

## 7. Versioning

Receipt schema versions and vector-document versions are separate.

- `receipt-v2.schema.json` governs the payload.
- `receipt-chain-vector-v1.schema.json` governs the test-vector envelope.

A change that modifies required fields, canonicalization, chain hashing, or privacy semantics requires a new protocol or schema version. Implementations MUST NOT silently reinterpret an existing version.

## 8. Security posture

Conformance means an implementation matches the documented serialization and validation behavior. It is not a security certification.

Production deployments still require authenticated transports, scoped credentials, isolation, target-system authorization, replay controls, human approval where appropriate, monitoring, and incident response.
