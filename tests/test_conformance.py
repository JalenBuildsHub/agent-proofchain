import copy
import json
import subprocess
from pathlib import Path

from proofchain.conformance import (
    compute_receipt_hash,
    load_vector,
    validate_receipt_v2,
    verify_receipt_chain_vector,
)

VECTOR_PATH = "spec/vectors/receipt-chain-v2.json"
EXPECTED_LAST_HASH = "abd74ad6e6c978f83a1d95fb58a6fdc481d80e0dc84613a3b3a031d0c8e465ee"


def test_published_receipt_chain_vector_is_valid():
    result = verify_receipt_chain_vector(load_vector(VECTOR_PATH))

    assert result == {
        "valid": True,
        "receipts": 2,
        "last_hash": EXPECTED_LAST_HASH,
        "errors": [],
    }


def test_hash_helper_reproduces_published_vector():
    vector = load_vector(VECTOR_PATH)
    previous_hash = vector["genesis"]

    for receipt in vector["receipts"]:
        observed = compute_receipt_hash(previous_hash, receipt["payload"])
        assert observed == receipt["receipt_hash"]
        previous_hash = observed


def test_payload_mutation_is_detected():
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"]["request_id"] = "mutated-request"

    result = verify_receipt_chain_vector(vector)

    assert result["valid"] is False
    assert "receipt 1: receipt_hash mismatch" in result["errors"]
    assert "receipt 2: previous_hash does not match prior receipt" in result["errors"]


def test_sequence_gap_is_rejected():
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][1]["sequence"] = 3

    result = verify_receipt_chain_vector(vector)

    assert result["valid"] is False
    assert "receipt 2: sequence must equal 2, got 3" in result["errors"]


def test_plaintext_caller_metadata_is_rejected():
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"]["claimed_actor"] = "private-human-identity"

    result = verify_receipt_chain_vector(vector)

    assert result["valid"] is False
    assert any("caller-controlled plaintext fields are forbidden" in item for item in result["errors"])
    assert any("unknown fields: claimed_actor" in item for item in result["errors"])


def test_decision_boolean_conflict_is_rejected():
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"]["decision"] = "deny"

    result = verify_receipt_chain_vector(vector)

    assert result["valid"] is False
    assert any("conflicts with allowed=True" in item for item in result["errors"])


def test_receipt_validator_rejects_invalid_digest_and_array_contracts():
    payload = copy.deepcopy(load_vector(VECTOR_PATH)["receipts"][0]["payload"])
    payload["content_sha256"] = "not-a-digest"
    payload["reason_codes"] = "not-an-array"

    errors = validate_receipt_v2(payload, sequence=1)

    assert "receipt 1: content_sha256 must be a lowercase SHA-256 hex digest" in errors
    assert "receipt 1: reason_codes must be a string array" in errors


def test_malformed_payload_matches_javascript_chain_progression(tmp_path: Path):
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"] = "malformed"
    expected = verify_receipt_chain_vector(vector)
    vector_path = tmp_path / "malformed-vector.json"
    vector_path.write_text(json.dumps(vector), encoding="utf-8")
    completed = subprocess.run(
        ["node", "examples/verify_receipt_vector.mjs", str(vector_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    observed = json.loads(completed.stdout)
    assert observed["last_hash"] == expected["last_hash"]
    assert observed["errors"] == expected["errors"]
