import hashlib
import json
import sqlite3

from proofchain import AdmissionPolicy, AdmissionRequest, ReceiptLedger, evaluate


def decision():
    policy = AdmissionPolicy.from_dict({"actor_capabilities": {"builder": ["read"]}})
    request = AdmissionRequest(
        "agent-1",
        "builder",
        "builder",
        "read",
        "inspect",
        "model-v1",
        source="unit-test",
    )
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


def test_verify_fails_closed_when_receipts_table_is_removed(tmp_path):
    path = tmp_path / "proof.db"
    ledger = ReceiptLedger(path)
    ledger.append(decision())
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE receipts")

    result = ledger.verify()

    assert result == {
        "valid": False,
        "receipts": 0,
        "failure": "missing_receipts_table",
    }
    with sqlite3.connect(path) as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'receipts'"
        ).fetchone()
    assert table is None


def test_verify_rejects_non_contiguous_sequence(tmp_path):
    path = tmp_path / "proof.db"
    ledger = ReceiptLedger(path)
    ledger.append(decision())
    ledger.append(decision())
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE receipts SET sequence = 3 WHERE sequence = 2")

    result = ledger.verify()

    assert result["valid"] is False
    assert result["failure"] == "non_contiguous_sequence"


def test_verify_rejects_schema_without_receipt_hash_uniqueness(tmp_path):
    path = tmp_path / "proof.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            """CREATE TABLE receipts (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                receipt_hash TEXT NOT NULL
            )"""
        )

    result = ReceiptLedger(path).verify()

    assert result["valid"] is False
    assert result["failure"] == "invalid_receipts_schema"


def test_verify_rejects_structurally_invalid_hashed_payload(tmp_path):
    path = tmp_path / "proof.db"
    ReceiptLedger(path).append(decision())
    payload_json = json.dumps({"schema_version": 2}, sort_keys=True, separators=(",", ":"))
    receipt_hash = hashlib.sha256(f"GENESIS\n{payload_json}".encode()).hexdigest()
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM receipts")
        conn.execute(
            "INSERT INTO receipts (sequence, payload_json, previous_hash, receipt_hash) "
            "VALUES (1, ?, 'GENESIS', ?)",
            (payload_json, receipt_hash),
        )

    result = ReceiptLedger(path).verify()

    assert result["valid"] is False
    assert result["failure"] == "invalid_receipt_payload"
