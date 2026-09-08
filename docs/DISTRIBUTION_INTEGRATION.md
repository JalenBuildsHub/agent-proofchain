# Nymrel Distribution Spine Integration

Status: Phase 1 example integration. Agent ProofChain remains an admission and evidence layer; it does not authenticate a social account, authorize an exact Postiz operation, consume a nonce, publish content, or prove that publishing occurred.

## Purpose

The Distribution Spine uses Agent ProofChain to answer a narrow set of questions before and after a campaign action:

1. Which authenticated runtime and actor requested the capability?
2. Was that actor family eligible for the requested capability?
3. Did the request contain injection-shaped instructions?
4. Which product, campaign revision, content item, channel, and requested effect were evaluated?
5. Can the allow or deny decision be verified later without storing raw private content?

PermitMesh or another policy decision point still evaluates the exact schedule or publish operation. The Postiz adapter or tool proxy remains the enforcement point.

## Example files

- `examples/distribution-policy.json`
- `examples/distribution-draft-request.json`
- `examples/distribution-injection-request.json`

Run the safe draft admission example:

```bash
proofchain evaluate \
  --policy examples/distribution-policy.json \
  --request examples/distribution-draft-request.json \
  --ledger distribution-proofchain.db
```

The request is advisory and explicitly asks for `draft-only`. It carries identifiers and a campaign revision hash rather than a raw post body.

Run the injection-shaped publish example:

```bash
proofchain evaluate \
  --policy examples/distribution-policy.json \
  --request examples/distribution-injection-request.json \
  --ledger distribution-proofchain.db
```

The example deliberately combines:

- a drafter requesting mutation authority;
- a forged revision value;
- a request to publish immediately;
- instructions to ignore approval rules;
- instructions to bypass audit and suppress reporting.

The policy should deny the request through both capability and injection-shaped controls.

Verify the receipt chain:

```bash
proofchain verify --ledger distribution-proofchain.db
```

## Trusted host context

A production adapter must construct `AuthenticatedRuntimeContext` from trusted transport or host evidence. The campaign payload may supply task intent, but it may not establish:

- actor identity;
- actor family;
- runtime family;
- provider;
- model identity;
- source system;
- provider request identity.

The host should normalize a distribution request using a provider-neutral adapter before admission evaluation. The payload may include only the minimum task data needed for evaluation:

```json
{
  "product_id": "goviral",
  "campaign_id": "launch-001",
  "revision_hash": "<sha256>",
  "content_id": "content-001",
  "channel": "linkedin",
  "claim_ids": ["long-form-to-clips"],
  "requested_effect": "draft-only"
}
```

Avoid placing raw post copy, private media URLs, OAuth tokens, API keys, customer content, personal data, or approval secrets into the ProofChain ledger.

## Recommended receipt sequence

The surrounding Nymrel integration should write independent receipts for:

1. `campaign.proposed`
2. `content.generated`
3. `content.approved`
4. `post.draft_requested`
5. `post.draft_created`
6. `post.schedule_requested`
7. `post.scheduled`
8. `post.published`
9. `analytics.observed`

ProofChain records the admission decision and safe digests. The surrounding system records external outcome evidence, such as a Postiz post ID, published URL, webhook event ID, analytics observation window, and PermitMesh decision reference.

## Privacy boundary

The receipt should contain digests and safe reason codes, not:

- raw prompts or generated copy;
- social OAuth credentials;
- private campaign strategy;
- customer records;
- unredacted provider error bodies;
- payment details;
- personal attribution data.

The studio event contract can retain privacy-safe campaign and outcome identifiers separately under its own retention policy.

## Limits

This integration does not claim that Agent ProofChain:

- authenticates Postiz, OpenAI, or any other provider;
- proves a model identifier is genuine;
- authorizes or executes a social post;
- prevents every prompt injection;
- guarantees a receipt was honored by the execution boundary;
- detects final-row ledger truncation without an external signed checkpoint;
- provides a security certification.
