import hashlib
import json
import sqlite3

import pytest

from proofchain import DistributionExecutionReceipt, ReceiptLedger


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
    assert payload["event_id_sha256"] == hashlib.sha256(
        receipt.event_id.encode()
    ).hexdigest()
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


def test_distribution_receipt_rejects_non_digest_evidence():
    receipt = distribution_receipt()

    with pytest.raises(ValueError, match="request_sha256"):
        DistributionExecutionReceipt(
            **{
                **receipt.__dict__,
                "request_sha256": "not-a-digest",
            }
        ).to_receipt()


def test_generic_ledger_rejects_unschematized_payload(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")

    with pytest.raises(ValueError, match="schema_version"):
        ledger.append_payload({"receipt_type": "distribution_execution"})
