# Contributing to Agent ProofChain

Agent ProofChain is intentionally narrow: deterministic admission decisions, privacy-safe receipts, portable evaluation, and independently checkable evidence for AI-agent systems.

Contributions are welcome when they strengthen that core without turning the project into an agent orchestrator, credential store, execution sandbox, or provider-specific framework.

## Start here

1. Read `README.md`, `docs/THREAT_MODEL.md`, and `docs/LIMITATIONS.md`.
2. Review `ROADMAP.md` and open issues before beginning large work.
3. For security-sensitive changes, open a design issue before a pull request.
4. Keep fixtures synthetic. Never submit customer data, private prompts, credentials, internal paths, or live exploit material.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
proofchain demo
```

The supported CI matrix covers Python 3.11 and 3.13 on Ubuntu and Windows.

## Contribution lanes

### Evaluation fixtures

Useful fixture contributions include:

- authorization boundary cases;
- actor/runtime identity mismatches;
- model-attribution failures;
- benign security language that should not be overblocked;
- compound injection-shaped instructions;
- reason-code contract tests;
- receipt-tampering cases.

Each fixture must have a stable unique ID, category, expected allow/deny result, and a short explanation in the pull request. Prefer independently authored cases rather than paraphrasing existing fixtures.

### Runtime adapters

Provider adapters must preserve the authenticated host-context boundary:

- identity and runtime metadata come from the trusted host;
- caller payloads provide task intent only;
- raw private prompts do not enter receipts or reports;
- provider/context mismatches fail closed;
- the integration documents which fields are verified and which are merely host-asserted.

### Receipt and policy changes

Changes to receipt schemas, reason codes, hash construction, or policy semantics require:

- a design explanation;
- migration or compatibility notes;
- deterministic tests;
- updated threat-model and limitation documentation;
- evidence that privacy boundaries remain intact.

## Pull request requirements

A pull request should include:

- the problem and intended user outcome;
- the trust boundary affected;
- tests and evaluation evidence;
- documentation updates;
- compatibility implications;
- known limitations and non-goals.

Keep pull requests reviewable. Separate infrastructure, new semantics, documentation, and releases when practical.

## Commit and release discipline

- Do not commit generated databases, credentials, private prompts, or customer data.
- Do not weaken default-deny behavior to make a benchmark pass.
- Do not claim security certification from synthetic evaluation results.
- Maintainers perform releases separately from feature pull requests.

## Reporting vulnerabilities

Follow `SECURITY.md`. Do not open public issues containing exploitable details, secrets, private data, or live attack payloads.

## Good first contributions

Strong first contributions are usually:

- clearer examples;
- independently authored synthetic fixtures;
- documentation corrections;
- cross-platform test improvements;
- conformance checks;
- privacy-preserving report improvements.
