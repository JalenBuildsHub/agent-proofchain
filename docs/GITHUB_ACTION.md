# GitHub Action: generate Agent ProofChain evidence

The repository includes a composite GitHub Action that installs Agent ProofChain from the checked-out action source and generates privacy-safe evidence files in the caller's workflow.

The action does not execute an AI agent, authenticate a provider, mutate a repository, send messages, or deploy anything. It runs the local demo, receipt conformance check, synthetic evaluation, and ledger-tamper evaluation.

## Example

After a reviewed release tag exists, a caller can pin that immutable tag or commit:

```yaml
name: agent evidence

on:
  pull_request:

permissions:
  contents: read

jobs:
  proofchain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate Agent ProofChain evidence
        id: proofchain
        uses: JalenBuildsHub/agent-proofchain@REVIEWED_COMMIT_SHA
        with:
          output-directory: proofchain-evidence
          policy: policy/agent-policy.json
          fixtures: evals/agent-fixtures.json

      - uses: actions/upload-artifact@v4
        with:
          name: proofchain-evidence
          path: ${{ steps.proofchain.outputs.evidence-directory }}
```

Do not use a mutable branch name for security-sensitive workflows. Pin the action to a reviewed commit SHA or immutable release tag.

## Inputs

| Input | Required | Default | Purpose |
|---|---:|---|---|
| `python-version` | no | `3.13` | Python runtime for the action. |
| `output-directory` | no | `proofchain-evidence` | Caller-workspace directory for generated files. |
| `policy` | no | bundled synthetic policy | Policy to evaluate. |
| `fixtures` | no | bundled synthetic v0.2 fixtures | Fixture corpus to evaluate. |
| `vector` | no | bundled receipt vector | Portable conformance vector. |

Custom policy and fixture paths are interpreted relative to the caller workspace. Bundled defaults come from the action source.

## Output files

- `demo.json` — local admission, receipt, evaluation, and limitation summary;
- `conformance.json` — portable receipt-vector verification;
- `evaluation.json` and `evaluation.md` — decision metrics and fixture outcomes;
- `tamper.json` and `tamper.md` — local hash-chain mutation outcomes and known limitation.

## Trust boundary

A green action run demonstrates that:

- the installed package can execute in the workflow environment;
- the selected fixtures match expected decisions and reason contracts;
- the selected receipt vector verifies;
- the local tamper scenarios match documented outcomes.

It does not demonstrate that:

- a production agent or provider was authenticated;
- a real tool action was authorized or executed;
- production prompts are safe;
- the benchmark covers unknown attacks;
- the latest receipt cannot be truncated without an external checkpoint.

## Privacy

The generated reports omit raw request content and caller-controlled identity metadata. Custom fixtures still exist in the caller workspace, so the caller must keep them synthetic or apply an approved privacy and retention policy.

## Maintainer validation

The repository smoke-tests the action on Ubuntu and Windows and uploads the action output as CI artifacts before release.
