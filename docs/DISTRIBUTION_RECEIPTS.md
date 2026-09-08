# Distribution Execution Receipts

Agent ProofChain can append privacy-preserving, host-supplied evidence about one guarded social-distribution side effect to its existing SHA-256 receipt chain. A receipt does not establish that an external side effect occurred.

## What the receipt records

A `DistributionExecutionReceipt` records digests that correlate:

- the Nymrel source event and exact product commit;
- the AdFunnel idempotency key and brand;
- the target platform and Postiz integration;
- the human approval artifact;
- the PermitMesh contract and decision digests;
- the exact Postiz request fingerprint;
- the resulting Postiz post identifiers or safe failure code; and
- the captured execution status.

Caller-controlled identifiers are stored as SHA-256 correlation digests. Raw account IDs, brand IDs, source-event names, approval IDs, idempotency keys, and provider post IDs are not written to the public receipt payload.

The library rejects missing correlation fields, unsupported statuses, and malformed SHA-256 evidence digests. Those structural checks do not authenticate the supplied values or a provider response.

## Required host controls

ProofChain does not connect accounts, authenticate Postiz, consume a PermitMesh nonce, execute a post, or guarantee that a provider response is truthful. The guarded worker must:

1. authenticate the worker and load the exact persisted approval;
2. recompute and verify the content and request fingerprints;
3. obtain a PermitMesh allow decision for the exact operation;
4. atomically reserve or consume the one-time operation nonce;
5. execute the matching Postiz request only once;
6. construct the execution receipt from authenticated local state and the provider response; and
7. append it to the ledger before declaring the job reconciled.

## Status lifecycle

Supported receipt statuses are:

- `draft_created`
- `scheduled`
- `published`
- `failed`
- `reconciled`

A provider acceptance is not equivalent to verified business impact. Activation, revenue, and retention evidence remain separate attributed events in Nymrel's commercial operating layer.

## Privacy boundary

Plain SHA-256 digests are pseudonymous correlation keys, not anonymization. Low-entropy identifiers may be guessable. Production hosts should prefer opaque high-entropy IDs or keyed HMACs when the correlation values require stronger privacy.

## Example

```python
from proofchain import DistributionExecutionReceipt, ReceiptLedger

receipt = DistributionExecutionReceipt(
    event_id="opaque-event-id",
    idempotency_key="opaque-idempotency-key",
    brand_id="opaque-brand-id",
    platform="X",
    integration_id="opaque-postiz-integration-id",
    source_commit="a" * 40,
    approval_artifact_id="opaque-approval-id",
    permit_contract_digest="b" * 64,
    permit_decision_digest="c" * 64,
    request_sha256="d" * 64,
    status="draft_created",
    captured_at="2026-07-29T06:00:00Z",
    provider_post_ids=("opaque-provider-post-id",),
)

ledger = ReceiptLedger("proofchain.db")
ledger.append_payload(receipt.to_receipt())
assert ledger.verify()["valid"] is True
```
