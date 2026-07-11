import sqlite3

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

