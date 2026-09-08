# Current pre-release evidence

This page records the latest maintainer-generated evidence for the stacked pre-release work. It is not a release attestation, external review, or security certification.

## Evidence snapshot

- Date: 2026-07-28
- Branch head: `e9b15800c0161279dfc34a7ad73938a1526b36d7`
- Status: draft stacked pull requests; unmerged and unreleased
- Supported CI environments exercised:
  - Ubuntu / Python 3.11
  - Ubuntu / Python 3.13
  - Windows / Python 3.11
  - Windows / Python 3.13

## Test and build evidence

The primary CI workflow passed in all four environments:

- Ruff: passed;
- pytest: 40 tests passed;
- wheel and source distribution build: passed;
- one-command demo: passed;
- Python receipt-vector verifier: passed;
- JavaScript receipt-vector verifier: passed;
- 40-case admission evaluation: passed;
- five-case tamper evaluation: passed;
- evidence artifact upload: passed.

The action-smoke workflow also passed on Ubuntu and Windows. The clean-install workflow built the wheel, installed it outside the repository's editable environment, and ran the demo and conformance verifier on Ubuntu and Windows under Python 3.11 and 3.13.

## Admission evaluation

- Fixtures: 40
- Fixture SHA-256: `101ad383ba3489ed0ff0f8812d7095a3d9dcad49e8d278334929d650f841b5d8`
- Expected allows: 15
- Expected denies: 25
- Matched outcomes: 40
- False allows: 0
- False denies: 0
- Allow precision / recall: 1.0 / 1.0
- Deny precision / recall: 1.0 / 1.0
- Raw request content included in report: no

These results describe the bundled synthetic corpus only. They do not establish general prompt-injection detection performance or production security.

## Cross-language conformance

The dependency-free Python and JavaScript verifiers both accepted the published two-receipt vector and produced the same final chain head:

```text
abd74ad6e6c978f83a1d95fb58a6fdc481d80e0dc84613a3b3a031d0c8e465ee
```

This demonstrates compatibility for the published vector under the draft canonicalization contract. It does not prove compatibility for unreviewed numeric, Unicode, or schema-extension edge cases.

## Tamper evaluation

Expected outcomes matched: 5 / 5.

Detected:

- receipt payload edit;
- previous-hash edit;
- receipt-hash edit;
- middle-row deletion.

Intentionally not detected by a local chain alone:

- final-row truncation.

The final-row limitation requires an external signed checkpoint, witness, or transparency mechanism that records the expected chain head.

## Reproducing the evidence

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
proofchain demo
proofchain conformance --vector spec/vectors/receipt-chain-v2.json
proofchain eval \
  --policy examples/policy.json \
  --fixtures evals/synthetic-v0.2.json \
  --output artifacts/evaluation.json \
  --markdown-output artifacts/evaluation.md
proofchain tamper-eval \
  --output artifacts/tamper.json \
  --markdown-output artifacts/tamper.md
node examples/verify_receipt_vector.mjs spec/vectors/receipt-chain-v2.json
```

## Evidence still required

Before a stronger adoption or security claim:

- independently authored fixture packs;
- external benchmark-methodology review;
- clean-install evidence from outside Jalen Builds Studio;
- real provider integration examples with explicit authentication boundaries;
- review of canonicalization edge cases;
- external checkpoint implementation;
- production pilots with scoped credentials and host-owned isolation.
