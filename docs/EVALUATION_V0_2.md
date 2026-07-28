# v0.2 portable evaluation pilot

## Scope

The v0.2 benchmark is a deterministic package evaluation. It tests the current admission-policy
implementation against synthetic allow and deny cases and exercises the local receipt ledger
against known mutations.

It is not:

- a claim of complete prompt-injection detection;
- a production security certification;
- a provider comparison;
- an external-adoption result;
- evidence that a compromised trusted runtime cannot lie;
- a substitute for process isolation, scoped credentials, replay protection, or human approval.

## Running the reports

```bash
proofchain eval \
  --policy examples/policy.json \
  --fixtures evals/synthetic-v0.2.json \
  --output artifacts/eval-v0.2.json \
  --markdown-output artifacts/eval-v0.2.md

proofchain tamper-eval \
  --output artifacts/tamper-v0.2.json \
  --markdown-output artifacts/tamper-v0.2.md
```

CI runs the reports on Linux and Windows under the supported Python matrix and uploads the output
as workflow artifacts.

## Fixture contract

Each fixture is a JSON object containing:

```json
{
  "id": "stable-fixture-id",
  "category": "authorization",
  "expected_allowed": false,
  "expected_reason_codes": ["capability_not_allowed"],
  "forbidden_reason_codes": [],
  "request": {
    "claimed_actor": "synthetic-reviewer",
    "actor_family": "reviewer",
    "runtime_family": "reviewer",
    "capability": "mutation",
    "action": "edit",
    "model": "synthetic-model",
    "content": "Apply the synthetic change."
  }
}
```

Requirements:

- fixture identifiers must be unique;
- `expected_allowed` must be a JSON boolean;
- `request` must be an object;
- reason-code assertions, when present, must be string arrays;
- fixtures must remain synthetic and contain no secrets, private prompts, customer data, or
  internal machine paths.

A fixture only counts as matched when the allow/deny classification is correct, every expected
reason code is present, and every forbidden reason code is absent.

## Report metrics

The JSON report includes:

- fixture count and deterministic fixture SHA-256;
- true allows and true denies;
- false allows and false denies;
- allow precision and recall;
- deny precision and recall;
- false-allow and false-deny rates;
- per-category outcomes;
- reason-code frequencies;
- per-fixture local process latency;
- minimum, median, p95, maximum, and total local latency;
- privacy-safe per-fixture result records.

Both allow and deny metrics are reported so the benchmark does not hide safety failures behind
aggregate accuracy.

## Timing limitations

Latency is measured with `perf_counter_ns` inside the current Python process. It includes admission
evaluation only. It excludes transport, authentication, provider calls, database writes, network
latency, process startup, and surrounding runtime overhead.

Timing values may vary by operating system, Python version, CPU, virtualization, power state, and
background load. They are useful for controlled regression detection, not service-level promises or
cross-machine performance claims.

## Privacy boundary

Evaluation reports include fixture identifiers, categories, decision outcomes, safe reason codes,
injection-indicator identifiers, content hashes, and timing values.

They do not include:

- raw request content;
- claimed actor plaintext;
- actor or runtime family plaintext;
- capability, action, model, or source plaintext from the request;
- private prompts or incident transcripts.

Fixture files themselves are public synthetic test data and must be reviewed accordingly.

## Ledger tamper scenarios

The deterministic tamper evaluation exercises:

| Scenario | Expected result |
|---|---|
| payload JSON edited | detected |
| previous hash edited | detected |
| receipt hash edited | detected |
| middle receipt deleted | detected |
| final receipt truncated | not detected locally |

Final-row truncation is an intentional known limitation. A local hash chain proves continuity among
the rows that remain; it cannot prove that the latest row was not deleted. Detecting truncation
requires an externally retained signed checkpoint, transparency log, trusted timestamp, or another
independent boundary. That belongs to later roadmap work and must not be implied by v0.2 results.

## Benchmark governance

Before making broad public effectiveness claims, the project should add:

1. independently authored fixtures;
2. obfuscated and multilingual cases;
3. model-mediated trajectories rather than static strings alone;
4. versioned methodology and benchmark-review records;
5. external clean-install runs;
6. documented false positives and false negatives;
7. provider integration examples that preserve the authenticated-context boundary;
8. external signed receipt checkpoints for truncation detection.

Synthetic CI accuracy is package-regression evidence, not external validation.
