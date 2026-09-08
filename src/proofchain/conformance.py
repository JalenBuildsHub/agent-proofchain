"""Portable receipt-chain conformance helpers and deterministic test-vector verification."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_V2_FIELDS = {
    "schema_version",
    "request_id",
    "allowed",
    "decision",
    "reason_codes",
    "content_sha256",
    "injection_matches",
    "claimed_actor_sha256",
    "actor_family_sha256",
    "runtime_family_sha256",
    "capability_sha256",
    "action_sha256",
    "model_sha256",
    "source_sha256",
}
DIGEST_FIELDS = {
    "content_sha256",
    "claimed_actor_sha256",
    "actor_family_sha256",
    "runtime_family_sha256",
    "capability_sha256",
    "action_sha256",
    "model_sha256",
    "source_sha256",
}
PLAINTEXT_CALLER_FIELDS = {
    "claimed_actor",
    "actor_family",
    "runtime_family",
    "capability",
    "action",
    "model",
    "source",
    "content",
}


def canonical_payload_json(payload: dict[str, Any]) -> str:
    """Return the canonical JSON representation used by receipt-chain hashing."""

    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def compute_receipt_hash(previous_hash: str, payload: dict[str, Any]) -> str:
    """Compute SHA-256(previous_hash + newline + canonical payload JSON)."""

    material = f"{previous_hash}\n{canonical_payload_json(payload)}".encode()
    return hashlib.sha256(material).hexdigest()


def _validate_string_array(value: Any, field: str, errors: list[str], sequence: int) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"receipt {sequence}: {field} must be a string array")


def validate_receipt_v2(payload: Any, sequence: int) -> list[str]:
    """Validate the narrow receipt-v2 portability and privacy contract."""

    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"receipt {sequence}: payload must be an object"]

    fields = set(payload)
    missing = sorted(RECEIPT_V2_FIELDS - fields)
    extra = sorted(fields - RECEIPT_V2_FIELDS)
    if missing:
        errors.append(f"receipt {sequence}: missing fields: {', '.join(missing)}")
    if extra:
        errors.append(f"receipt {sequence}: unknown fields: {', '.join(extra)}")

    plaintext = sorted(fields & PLAINTEXT_CALLER_FIELDS)
    if plaintext:
        errors.append(
            f"receipt {sequence}: caller-controlled plaintext fields are forbidden: "
            f"{', '.join(plaintext)}"
        )

    if payload.get("schema_version") != 2:
        errors.append(f"receipt {sequence}: schema_version must equal 2")
    if not isinstance(payload.get("request_id"), str) or not payload.get("request_id", "").strip():
        errors.append(f"receipt {sequence}: request_id must be a non-empty string")

    allowed = payload.get("allowed")
    decision = payload.get("decision")
    if type(allowed) is not bool:
        errors.append(f"receipt {sequence}: allowed must be a boolean")
    if not isinstance(decision, str) or decision not in {"allow", "deny"}:
        errors.append(f"receipt {sequence}: decision must be allow or deny")
    if type(allowed) is bool and isinstance(decision, str) and decision in {"allow", "deny"}:
        expected = "allow" if allowed else "deny"
        if decision != expected:
            errors.append(
                f"receipt {sequence}: decision {decision!r} conflicts with allowed={allowed}"
            )

    _validate_string_array(payload.get("reason_codes"), "reason_codes", errors, sequence)
    _validate_string_array(payload.get("injection_matches"), "injection_matches", errors, sequence)

    for field in sorted(DIGEST_FIELDS):
        value = payload.get(field)
        if not isinstance(value, str) or not DIGEST_PATTERN.fullmatch(value):
            errors.append(f"receipt {sequence}: {field} must be a lowercase SHA-256 hex digest")

    return errors


def verify_receipt_chain_vector(document: Any) -> dict[str, Any]:
    """Verify a portable receipt-chain vector without using the SQLite ledger."""

    if not isinstance(document, dict):
        return {
            "valid": False,
            "receipts": 0,
            "last_hash": "GENESIS",
            "errors": ["vector document must be an object"],
        }

    errors: list[str] = []
    if type(document.get("schema_version")) is bool or document.get("schema_version") != 1:
        errors.append("vector schema_version must equal 1")
    if document.get("genesis") != "GENESIS":
        errors.append("vector genesis must equal GENESIS")

    receipts = document.get("receipts")
    if not isinstance(receipts, list):
        return {
            "valid": False,
            "receipts": 0,
            "last_hash": "GENESIS",
            "errors": [*errors, "receipts must be an array"],
        }

    previous_hash = "GENESIS"
    for expected_sequence, receipt in enumerate(receipts, start=1):
        if not isinstance(receipt, dict):
            errors.append(f"receipt {expected_sequence}: vector entry must be an object")
            continue

        sequence = receipt.get("sequence")
        if type(sequence) is bool or sequence != expected_sequence:
            errors.append(
                f"receipt {expected_sequence}: sequence must equal "
                f"{expected_sequence}, got {sequence!r}"
            )

        payload = receipt.get("payload")
        errors.extend(validate_receipt_v2(payload, expected_sequence))

        observed_previous = receipt.get("previous_hash")
        if observed_previous != previous_hash:
            errors.append(
                f"receipt {expected_sequence}: previous_hash does not match prior receipt"
            )

        observed_hash = receipt.get("receipt_hash")
        if not isinstance(observed_hash, str) or not DIGEST_PATTERN.fullmatch(observed_hash):
            errors.append(
                f"receipt {expected_sequence}: receipt_hash must be a lowercase SHA-256 hex digest"
            )
        if isinstance(payload, dict):
            try:
                expected_hash = compute_receipt_hash(previous_hash, payload)
            except (ValueError, TypeError):
                errors.append(
                    f"receipt {expected_sequence}: payload must contain finite JSON values"
                )
                continue
            if observed_hash != expected_hash:
                errors.append(f"receipt {expected_sequence}: receipt_hash mismatch")
            previous_hash = expected_hash

    return {
        "valid": not errors,
        "receipts": len(receipts),
        "last_hash": previous_hash,
        "errors": errors,
    }


def load_vector(path: str | Path) -> dict[str, Any]:
    """Load one JSON conformance vector."""

    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("conformance vector must be a JSON object")
    return value
