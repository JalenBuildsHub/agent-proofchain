# Roadmap

## v0.1 — local alpha

- Admission policy, injection indicators, and hash-chained receipt ledger.
- Synthetic test corpus and CLI examples.
- Threat model, limitations, security policy, and governance baseline.

## v0.2 — portable evaluation and protocol pilot

Foundation completed on feature branches:

- [x] 40 provider-neutral synthetic adversarial and benign tasks.
- [x] Allow/deny precision and recall, false-allow and false-deny rates, category summaries,
  reason-code assertions, and local process latency reports.
- [x] Machine-readable JSON and human-readable Markdown reports.
- [x] Deterministic ledger-tamper evaluation with the final-truncation limitation reported.
- [x] Provider-neutral OpenAI, Anthropic, Google, and local-runtime adapter contracts.
- [x] Cross-platform CI generation of evaluation evidence artifacts.
- [x] Network-free one-command demonstration.
- [x] Draft receipt-v2 and vector JSON Schemas.
- [x] Portable receipt-chain conformance vector and dependency-free verifier.
- [x] Draft protocol documentation for canonicalization, hashing, privacy, and versioning.

Remaining before calling v0.2 complete:

- [ ] Independently authored or externally reviewed fixtures.
- [ ] Provider SDK integration examples that preserve the authenticated host-context boundary.
- [ ] Clean-install evaluation receipts from outside Jalen Builds Studio.
- [ ] Benchmark methodology review and versioning policy.
- [ ] A second-language verifier that passes the published vector.
- [ ] External signed checkpoints for final-ledger truncation detection.

## v0.3 — remote-worker boundary

- Signed requests, nonce/replay protection, revocation, and scoped grants.
- Container/worktree reference architecture.
- External adopter and independent-review evidence.
