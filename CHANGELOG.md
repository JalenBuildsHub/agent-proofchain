# Changelog

## 0.1.0 — unreleased

- Added provider-neutral admission requests and decisions.
- Added default-deny capability policy.
- Added prompt-injection indicator evaluation.
- Added tamper-evident SQLite receipt ledger and verifier.
- Added synthetic tests, examples, and project governance documents.
- Added a 20-task synthetic admission evaluation pilot and machine-readable runner.
- Replaced plaintext caller metadata in receipt schema v2 with SHA-256 correlation digests.
- Added a 40-case v0.2 adversarial and benign evaluation corpus with category and reason-code
  contracts.
- Added allow and deny precision/recall, false-allow and false-deny rates, local latency,
  category summaries, fixture digests, and Markdown report rendering.
- Added deterministic ledger-tamper reports that explicitly document the undetectable
  final-row truncation case without an external checkpoint.
- Added provider-neutral OpenAI, Anthropic, Google, and local-runtime adapter contracts bound
  to host-authenticated identity and attribution context.
- Added cross-platform CI evidence-artifact generation for the v0.2 evaluation pilot.
- Added a network-free `proofchain demo` covering admission, receipts, verification, evaluation,
  and tamper limits.
- Added architecture, vision, adoption, support, citation, and logs-versus-receipts documentation.
- Added structured bug, feature, and independent-fixture contribution forms.
- Added pull-request guidance, Dependabot configuration, typed-package metadata, and pinned
  OpenSSF Scorecard analysis.
