# Limitations

- Regex indicators are explainable heuristics, not a complete injection detector.
- Policy regexes execute in Python's standard regular-expression engine without a per-match
  timeout. Policies are trusted configuration, pattern length/count are bounded, and oversized
  content is denied before matching, but hosts must still review pattern complexity.
- A compromised trusted runtime can lie unless the host authenticates it independently.
- SHA-256 chaining detects modification and middle-row deletion but cannot prove that the final
  receipt was not truncated without an externally retained signed checkpoint.
- Deleting the entire local ledger also remains outside the protection of the local chain.
- An intact but emptied receipt table is indistinguishable from a newly initialized empty ledger
  without an externally retained signed checkpoint. A missing table or invalid schema is rejected.
- The package does not observe filesystem writes that bypass its admission call.
- Direct `AdmissionRequest` callers control provider-model and identity fields unless the host
  authenticates those values or uses the adapter contract with trusted host context.
- The named provider adapters are normalization contracts, not provider SDK integrations,
  authentication mechanisms, or compatibility certifications.
- Metadata digests are pseudonymous correlation keys, not anonymization; low-entropy values may be
  guessable. Hosts that need stronger privacy should bind identifiers to opaque IDs or keyed HMACs.
- Synthetic benchmark accuracy is package-regression evidence, not broad security effectiveness or
  external validation.
- Local process latency varies by machine and excludes transport, authentication, network,
  persistence, and provider overhead.
- Benchmark results must report false positives, false negatives, latency, fixture versions,
  adapter versions, runtime versions, and methodology limitations.
