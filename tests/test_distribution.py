import hashlib
import json
import sqlite3

import pytest

from proofchain import (
    AdmissionPolicy,
    AdmissionRequest,
    DistributionExecutionReceipt,
    ReceiptLedger,
    evaluate,
)
from proofchain.canonical import canonical_json


def distribution_receipt() -> DistributionExecutionReceipt:
    return DistributionExecutionReceipt(
        event_id="nymrel:my-caddie:launch:001",
        idempotency_key="my-caddie:x:launch:001",
        brand_id="brand-my-caddie",
        platform="X",
        integration_id="postiz-test-x",
        source_commit="a" * 40,
        approval_artifact_id="approval-my-caddie-x-001",
        permit_contract_digest="b" * 64,
        permit_decision_digest="c" * 64,
        request_sha256="d" * 64,
        status="draft_created",
        captured_at="2026-07-29T06:00:00Z",
        provider_post_ids=("postiz-post-123",),
    )


def test_distribution_receipt_hashes_caller_controlled_identifiers():
    receipt = distribution_receipt()
    payload = receipt.to_receipt()
    serialized = json.dumps(payload, sort_keys=True)

    private_values = [
        receipt.event_id,
        receipt.idempotency_key,
        receipt.brand_id,
        receipt.platform,
        receipt.integration_id,
        receipt.source_commit,
        receipt.approval_artifact_id,
        *receipt.provider_post_ids,
    ]

    assert payload["receipt_type"] == "distribution_execution"
    assert payload["schema_version"] == 1
    assert payload["event_id_sha256"] == hashlib.sha256(receipt.event_id.encode()).hexdigest()
    assert payload["provider_post_id_sha256"] == [
        hashlib.sha256(receipt.provider_post_ids[0].encode()).hexdigest()
    ]

    for value in private_values:
        assert value not in serialized


def test_distribution_receipt_can_join_and_verify_existing_hash_chain(tmp_path):
    path = tmp_path / "proof.db"
    ledger = ReceiptLedger(path)
    appended = ledger.append_payload(distribution_receipt().to_receipt())

    assert appended["sequence"] == 1
    assert appended["previous_hash"] == "GENESIS"
    assert ledger.verify() == {
        "valid": True,
        "receipts": 1,
        "last_hash": appended["receipt_hash"],
    }

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE receipts SET payload_json = ? WHERE sequence = 1",
            ('{"schema_version":1,"receipt_type":"tampered"}',),
        )
        conn.commit()

    result = ledger.verify()
    assert result["valid"] is False
    assert result["failed_sequence"] == 1


def test_distribution_receipt_can_follow_an_admission_receipt(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    decision = evaluate(
        AdmissionRequest("agent-1", "builder", "builder", "read", "inspect", "model-v1"),
        policy,
    )

    admission = ledger.append(decision)
    distribution = ledger.append_payload(distribution_receipt().to_receipt())

    assert distribution["previous_hash"] == admission["receipt_hash"]
    assert ledger.verify()["receipts"] == 2


def test_mixed_unicode_admission_and_distribution_receipts_use_canonical_utf8(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    decision = evaluate(
        AdmissionRequest("agent-\u00e9", "builder", "builder", "read", "inspect", "model-v1"),
        policy,
    )
    admission = ledger.append(decision)
    payload = {
        **distribution_receipt().__dict__,
        "status": "failed",
        "error_code": "\u00e9chec-\u2705",
    }
    distribution = ledger.append_payload(DistributionExecutionReceipt(**payload).to_receipt())

    expected_payload = canonical_json(DistributionExecutionReceipt(**payload).to_receipt())
    assert "\u00e9chec-\u2705" in expected_payload
    assert distribution["previous_hash"] == admission["receipt_hash"]
    assert ledger.verify()["valid"] is True


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("request_sha256", "not-a-digest", "request_sha256"),
        ("permit_contract_digest", "g" * 64, "permit_contract_digest"),
        ("permit_decision_digest", "A" * 64, "permit_decision_digest"),
        ("status", "queued", "status"),
        ("brand_id", "", "brand_id"),
    ],
)
def test_distribution_receipt_rejects_invalid_evidence(field, value, message):
    receipt = distribution_receipt()

    with pytest.raises(ValueError, match=message):
        DistributionExecutionReceipt(
            **{
                **receipt.__dict__,
                field: value,
            }
        ).to_receipt()


def test_generic_ledger_rejects_unschematized_payload(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")

    with pytest.raises(ValueError, match="schema_version"):
        ledger.append_payload({"receipt_type": "distribution_execution"})


@pytest.mark.parametrize("provider_post_ids", [("",), (" ",), (1,), "post-123"])
def test_distribution_receipt_rejects_invalid_provider_post_ids(provider_post_ids):
    receipt = distribution_receipt()

    with pytest.raises((TypeError, ValueError), match="provider_post_ids"):
        DistributionExecutionReceipt(
            **{**receipt.__dict__, "provider_post_ids": provider_post_ids}
        ).to_receipt()


@pytest.mark.parametrize("status", ["published", "reconciled"])
def test_distribution_receipt_requires_provider_post_ids_for_terminal_success(status):
    receipt = distribution_receipt()

    with pytest.raises(ValueError, match="provider_post_ids"):
        DistributionExecutionReceipt(
            **{**receipt.__dict__, "status": status, "provider_post_ids": ()}
        ).to_receipt()
