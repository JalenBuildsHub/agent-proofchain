# Agent ProofChain frontier runtime modernization

- Goal thread: `01a04d87-73f3-73e0-bd2f-8c89ee2b1023`
- Claim: `codex-proofchain-frontier-runtime-20260830`
- Canonical base: `9b8a5b901d81adf5b8b870632734232342d3b46e`
- Worktree: `C:\Users\johns\Desktop\agent-proofchain-frontier-runtime-20260830`
- Branch: `codex/proofchain-frontier-runtime-20260830`

## Objective

Modernize Agent ProofChain's supported Python runtime, packaging, CI, security analysis,
distribution provenance, and operator-facing release truth while preserving its provider-neutral,
zero-runtime-dependency API and fail-closed admission semantics.

## Guardrails

- Preserve the dirty, diverged primary checkout and every existing PR branch.
- Do not merge, publish to PyPI, configure trusted publishers, add secrets, or claim hosted
  workflow/provider readiness without exact provider evidence.
- Keep production payloads, private prompts, credentials, and customer data out of tests and
  receipts.
- Use immutable third-party action references, least privilege, deterministic tool versions, and
  clean distribution-consumer checks.
- Treat synthetic evaluation scores as bounded test evidence, not a security certification.

## Acceptance

- Python 3.11 through 3.14 support is explicit and locally verified where interpreters are
  available.
- Formatting/lint, unit/evaluation tests, build, Twine, clean wheel/sdist install, CLI, Bandit,
  pip-audit, actionlint, and Zizmor pass.
- CI is reusable, pins action commits and runner images, retains useful failure evidence, and
  verifies built artifacts rather than only the source tree.
- Any release workflow is gated by the reusable acceptance workflows and attests the exact
  immutable artifact bundle before an OIDC publisher.
- An independent exact-commit review accepts the candidate.
- The final receipt separates local proof from GitHub Actions, registry, publication, merge,
  customer, revenue, and public-release proof.
