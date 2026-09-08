"""SQLite-backed hash-chained decision and execution receipts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any

from .admission import AdmissionDecision
from .canonical import canonical_json

_RESERVED_RECEIPT_FIELDS = frozenset({"sequence", "previous_hash", "receipt_hash"})


class ReceiptLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS receipts (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                receipt_hash TEXT NOT NULL UNIQUE
            )"""
        )
        return conn

    def _connect_read_only(self) -> sqlite3.Connection:
        uri = f"{self.path.resolve().as_uri()}?mode=ro"
        conn = sqlite3.connect(uri, timeout=10, uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def append(self, decision: AdmissionDecision) -> dict[str, Any]:
        return self.append_payload(decision.to_receipt())

    def append_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Append one already-sanitized receipt payload to the hash chain."""
        normalized = dict(payload)
        if not normalized:
            raise ValueError("receipt payload must not be empty")
        reserved_fields = sorted(_RESERVED_RECEIPT_FIELDS.intersection(normalized))
        if reserved_fields:
            raise ValueError(
                "receipt payload must not contain reserved ledger fields: "
                + ", ".join(reserved_fields)
            )
        if "schema_version" not in normalized:
            raise ValueError("receipt payload requires schema_version")

        payload_json = canonical_json(normalized)
        if json.loads(payload_json).get("schema_version") == 2 and not _valid_receipt_payload(
            json.loads(payload_json)
        ):
            raise ValueError("receipt payload does not satisfy the admission receipt contract")

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT receipt_hash FROM receipts ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(row[0]) if row else "GENESIS"
            receipt_hash = hashlib.sha256(f"{previous_hash}\n{payload_json}".encode()).hexdigest()
            cursor = conn.execute(
                "INSERT INTO receipts (payload_json, previous_hash, receipt_hash) VALUES (?, ?, ?)",
                (payload_json, previous_hash, receipt_hash),
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise sqlite3.DatabaseError("receipt insert did not return a sequence")
            sequence = int(cursor.lastrowid)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return {
            **normalized,
            "sequence": sequence,
            "previous_hash": previous_hash,
            "receipt_hash": receipt_hash,
        }

    def verify(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"valid": True, "receipts": 0, "last_hash": "GENESIS"}

        try:
            with closing(self._connect_read_only()) as conn:
                table = conn.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'receipts'"
                ).fetchone()
                if table is None:
                    return {"valid": False, "receipts": 0, "failure": "missing_receipts_table"}
                columns = {
                    str(row["name"]): (
                        str(row["type"]).upper(),
                        int(row["notnull"]),
                        int(row["pk"]),
                    )
                    for row in conn.execute("PRAGMA table_info(receipts)").fetchall()
                }
                required_columns = {
                    "sequence": ("INTEGER", 0, 1),
                    "payload_json": ("TEXT", 1, 0),
                    "previous_hash": ("TEXT", 1, 0),
                    "receipt_hash": ("TEXT", 1, 0),
                }
                if any(
                    columns.get(name) != contract for name, contract in required_columns.items()
                ):
                    return {"valid": False, "receipts": 0, "failure": "invalid_receipts_schema"}
                unique_receipt_hash = False
                for index in conn.execute("PRAGMA index_list(receipts)").fetchall():
                    if not bool(index["unique"]) or bool(index["partial"]):
                        continue
                    indexed_columns = [
                        str(row["name"])
                        for row in conn.execute(
                            "SELECT name FROM pragma_index_info(?) ORDER BY seqno",
                            (str(index["name"]),),
                        ).fetchall()
                    ]
                    if indexed_columns == ["receipt_hash"]:
                        unique_receipt_hash = True
                        break
                if not unique_receipt_hash:
                    return {"valid": False, "receipts": 0, "failure": "invalid_receipts_schema"}
                rows = conn.execute(
                    "SELECT sequence, payload_json, previous_hash, receipt_hash "
                    "FROM receipts ORDER BY sequence"
                ).fetchall()
        except sqlite3.Error:
            return {"valid": False, "receipts": 0, "failure": "unreadable_ledger"}

        previous_hash = "GENESIS"
        for expected_sequence, row in enumerate(rows, start=1):
            if int(row["sequence"]) != expected_sequence:
                return {
                    "valid": False,
                    "receipts": len(rows),
                    "failed_sequence": int(row["sequence"]),
                    "failure": "non_contiguous_sequence",
                }
            try:
                payload = json.loads(str(row["payload_json"]))
            except (TypeError, json.JSONDecodeError):
                return {
                    "valid": False,
                    "receipts": len(rows),
                    "failed_sequence": int(row["sequence"]),
                    "failure": "invalid_receipt_payload",
                }
            if payload.get("schema_version") == 2 and not _valid_receipt_payload(payload):
                return {
                    "valid": False,
                    "receipts": len(rows),
                    "failed_sequence": int(row["sequence"]),
                    "failure": "invalid_receipt_payload",
                }
            expected = hashlib.sha256(
                f"{previous_hash}\n{row['payload_json']}".encode()
            ).hexdigest()
            if row["previous_hash"] != previous_hash or row["receipt_hash"] != expected:
                return {
                    "valid": False,
                    "receipts": len(rows),
                    "failed_sequence": int(row["sequence"]),
                    "failure": "hash_chain_mismatch",
                }
            previous_hash = str(row["receipt_hash"])
        return {"valid": True, "receipts": len(rows), "last_hash": previous_hash}


def _valid_receipt_payload(payload: object) -> bool:
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        return False
    allowed = payload.get("allowed")
    decision = payload.get("decision")
    if not isinstance(allowed, bool) or decision != ("allow" if allowed else "deny"):
        return False
    if not isinstance(payload.get("request_id"), str) or not payload["request_id"].startswith(
        "pc-"
    ):
        return False
    for field in ("reason_codes", "injection_matches"):
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return False
    digest_fields = (
        "content_sha256",
        "claimed_actor_sha256",
        "actor_family_sha256",
        "runtime_family_sha256",
        "capability_sha256",
        "action_sha256",
        "model_sha256",
        "source_sha256",
    )
    return all(_is_lower_sha256(payload.get(field)) for field in digest_fields)


def _is_lower_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
