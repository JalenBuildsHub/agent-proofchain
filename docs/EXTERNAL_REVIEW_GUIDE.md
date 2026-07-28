# External review guide

Agent ProofChain needs skeptical review more than broad approval. This guide identifies the questions most likely to uncover false confidence before a stronger release or adoption claim.

Do not publish undisclosed vulnerabilities or live exploit details. Use `SECURITY.md` for private reporting.

## Review scope

### 1. Authenticated host-context boundary

Questions:

- Can caller-controlled payload fields override actor identity, actor family, runtime family, model attribution, source, or provider request identity?
- Is the adapter contract clear about what the host must authenticate?
- Could an integration mistakenly treat host-asserted data as cryptographically verified?
- Does a provider mismatch fail closed?

Relevant files:

- `src/proofchain/adapters.py`
- `docs/ADAPTER_CONTRACT.md`
- `examples/gateway_adapter.py`
- `tests/test_adapters.py`

### 2. Admission semantics

Questions:

- Are default-deny conditions complete and understandable?
- Are reason codes stable enough for evaluation and operations?
- Can missing or malformed fields produce an unsafe allow?
- Are injection indicators described narrowly enough to avoid a protection guarantee?
- Which benign inputs are likely to be overblocked?

Relevant files:

- `src/proofchain/admission.py`
- `src/proofchain/policy.py`
- `evals/synthetic-v0.2.json`
- `tests/test_admission.py`
- `tests/test_evals.py`

### 3. Receipt privacy

Questions:

- Can raw caller-controlled values enter receipts, reports, errors, or CI artifacts?
- Are low-entropy digests mistakenly described as anonymous or confidential?
- Can reason codes or injection-match identifiers reveal private content indirectly?
- Are retention and correlation responsibilities clearly assigned to the host?

Relevant files:

- `src/proofchain/admission.py`
- `src/proofchain/ledger.py`
- `src/proofchain/evals.py`
- `spec/receipt-v2.schema.json`
- `docs/PROTOCOL_SPEC.md`
- `docs/LIMITATIONS.md`

### 4. Chain integrity and truncation

Questions:

- Is canonical JSON implemented consistently in Python and JavaScript?
- Can unusual Unicode, numeric, or nested values produce incompatible hashes?
- Are sequence, previous-hash, and payload mutations detected?
- Is the final-row truncation limitation stated everywhere it matters?
- What minimum external-checkpoint design would close that gap?

Relevant files:

- `src/proofchain/conformance.py`
- `src/proofchain/ledger.py`
- `src/proofchain/tamper.py`
- `examples/verify_receipt_vector.mjs`
- `spec/`
- `tests/test_conformance.py`
- `tests/test_tamper.py`

### 5. Evaluation methodology

Questions:

- Does the corpus contain redundant fixtures that inflate apparent coverage?
- Are allow and deny classes balanced enough for the claimed metrics?
- Which likely false positives are absent?
- Which policy-bypass families are absent?
- Are fixture authors independent from the implementation authors?
- Does the report distinguish classification correctness from reason-code correctness?

Relevant files:

- `evals/synthetic-v0.2.json`
- `src/proofchain/evals.py`
- `docs/EVALUATION_V0_2.md`
- `docs/EVIDENCE.md`

### 6. Packaging and automation

Questions:

- Does the built wheel work without the source tree?
- Are package metadata and included files accurate?
- Are GitHub Action dependencies pinned?
- Could custom fixture paths cause private content to be uploaded unintentionally?
- Does the reusable action describe only what it actually verifies?

Relevant files:

- `pyproject.toml`
- `action.yml`
- `.github/workflows/`
- `docs/GITHUB_ACTION.md`
- `docs/RELEASE_CHECKLIST.md`

## Useful review outputs

A strong review can be small. Useful outputs include:

- one independently authored fixture with rationale;
- one reproducible false allow or false deny;
- one canonicalization incompatibility;
- one privacy leak path;
- one unclear or overly broad claim;
- one proposed external-checkpoint design with explicit assumptions;
- confirmation that a clean install and vector verification work in an outside environment.

## Evidence expectations

Include:

- exact commit or release;
- operating system and runtime versions;
- synthetic reproduction;
- expected and observed behavior;
- privacy-safe logs or receipts;
- whether the finding is public-safe or requires private handling.

A reviewer does not need to endorse the project. Clear disagreement and failed tests are valuable evidence.
