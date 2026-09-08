import json
import sqlite3

import pytest

from proofchain import AdmissionPolicy, AdmissionRequest, ReceiptLedger, evaluate


def decision():
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    request = AdmissionRequest("agent-1", "builder", "builder", "read", "inspect", "model-v1")
    return evaluate(request, policy)


def test_ledger_chain_verifies(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")
    ledger.append(decision())
    ledger.append(decision())
    assert ledger.verify()["valid"] is True
    assert ledger.verify()["receipts"] == 2


def test_ledger_tampering_is_detected(tmp_path):
    path = tmp_path / "proof.db"
    ledger = ReceiptLedger(path)
    ledger.append(decision())
    conn = sqlite3.connect(path)
    conn.execute("UPDATE receipts SET payload_json = '{}' WHERE sequence = 1")
    conn.commit()
    conn.close()
    result = ledger.verify()
    assert result["valid"] is False
    assert result["failed_sequence"] == 1


def test_ledger_never_persists_caller_metadata_plaintext(tmp_path):
    path = tmp_path / "proof.db"
    private_path = "C:/Users/private/customer-path"
    private_action = "token=raw-secret"
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    request = AdmissionRequest(
        "secret-user@example.com",
        "builder",
        "builder",
        "read",
        private_action,
        "model-v1",
        source=private_path,
    )

    ReceiptLedger(path).append(evaluate(request, policy))
    with sqlite3.connect(path) as conn:
        payload_json = conn.execute("SELECT payload_json FROM receipts").fetchone()[0]

    payload = json.loads(payload_json)
    assert private_path not in payload_json
    assert private_action not in payload_json
    assert "secret-user@example.com" not in payload_json
    assert payload["source_sha256"]
    assert payload["action_sha256"]
    assert payload["claimed_actor_sha256"]


@pytest.mark.parametrize("field", ["sequence", "previous_hash", "receipt_hash"])
def test_ledger_rejects_reserved_metadata_fields(tmp_path, field):
    ledger = ReceiptLedger(tmp_path / "proof.db")

    with pytest.raises(ValueError, match="reserved ledger fields"):
        ledger.append_payload({"schema_version": 1, field: "forged"})


def test_failed_serialization_does_not_block_following_valid_append(tmp_path):
    ledger = ReceiptLedger(tmp_path / "proof.db")

    with pytest.raises(TypeError):
        ledger.append_payload({"schema_version": 1, "not_json": object()})

    appended = ledger.append_payload({"schema_version": 1, "receipt_type": "valid"})
    assert appended["sequence"] == 1
    assert ledger.verify()["valid"] is True
