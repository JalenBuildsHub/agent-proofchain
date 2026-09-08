import copy
import json
import subprocess
from pathlib import Path

import pytest

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
    assert any(
        "caller-controlled plaintext fields are forbidden" in item for item in result["errors"]
    )
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


@pytest.mark.parametrize("decision", [[], {}])
def test_unhashable_decision_is_invalid_in_both_verifiers(decision, tmp_path: Path):
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"]["decision"] = decision
    expected = verify_receipt_chain_vector(vector)
    vector_path = tmp_path / "invalid-decision.json"
    vector_path.write_text(json.dumps(vector), encoding="utf-8")
    completed = subprocess.run(
        ["node", "examples/verify_receipt_vector.mjs", str(vector_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    observed = json.loads(completed.stdout)
    assert observed["valid"] is expected["valid"] is False
    assert observed["last_hash"] == expected["last_hash"]


@pytest.mark.parametrize("field", ["schema_version", "sequence"])
def test_boolean_cannot_stand_in_for_vector_integer(field, tmp_path: Path):
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    target = vector if field == "schema_version" else vector["receipts"][0]
    target[field] = True
    expected = verify_receipt_chain_vector(vector)
    vector_path = tmp_path / "invalid-integer.json"
    vector_path.write_text(json.dumps(vector), encoding="utf-8")
    completed = subprocess.run(
        ["node", "examples/verify_receipt_vector.mjs", str(vector_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["valid"] is expected["valid"] is False


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_payload_is_rejected_without_advancing_either_chain(number):
    vector = copy.deepcopy(load_vector(VECTOR_PATH))
    vector["receipts"][0]["payload"]["extra"] = float(number)
    with pytest.raises(ValueError):
        compute_receipt_hash("GENESIS", vector["receipts"][0]["payload"])
    expected = verify_receipt_chain_vector(vector)
    script = """
import { readFileSync } from 'node:fs';
import { verifyVector } from './examples/verify_receipt_vector.mjs';
const vector = JSON.parse(readFileSync('spec/vectors/receipt-chain-v2.json', 'utf8'));
vector.receipts[0].payload.extra = Number(process.argv[1]);
console.log(JSON.stringify(verifyVector(vector)));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script, "--", number],
        text=True,
        capture_output=True,
        check=True,
    )
    observed = json.loads(completed.stdout)
    assert observed["valid"] is expected["valid"] is False
    assert observed["last_hash"] == expected["last_hash"]
    assert observed["errors"] == expected["errors"]
