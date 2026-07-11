# Limitations

- Regex indicators are explainable heuristics, not a complete injection detector.
- A compromised trusted runtime can lie unless the host authenticates it independently.
- SHA-256 chaining detects modification but cannot prevent deletion of the entire ledger.
- The package does not observe filesystem writes that bypass its admission call.
- Provider model identifiers are caller-supplied unless the host binds them to provider receipts.
- Benchmark results must report false positives, false negatives, latency, model versions, and fixtures.

