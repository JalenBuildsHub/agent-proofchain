"""SQLite-backed hash-chained decision and execution receipts."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .admission import AdmissionDecision


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

    def append(self, decision: AdmissionDecision) -> dict[str, Any]:
        return self.append_payload(decision.to_receipt())

    def append_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Append one already-sanitized receipt payload to the hash chain."""
        normalized = dict(payload)
        if not normalized:
            raise ValueError("receipt payload must not be empty")
        if "schema_version" not in normalized:
            raise ValueError("receipt payload requires schema_version")

        conn = self._connect()
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT receipt_hash FROM receipts ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = str(row[0]) if row else "GENESIS"
        payload_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        receipt_hash = hashlib.sha256(f"{previous_hash}\n{payload_json}".encode()).hexdigest()
        cursor = conn.execute(
            "INSERT INTO receipts (payload_json, previous_hash, receipt_hash) VALUES (?, ?, ?)",
            (payload_json, previous_hash, receipt_hash),
        )
        conn.commit()
        sequence = int(cursor.lastrowid)
        conn.close()
        return {
            "sequence": sequence,
            "previous_hash": previous_hash,
            "receipt_hash": receipt_hash,
            **normalized,
        }

    def verify(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"valid": True, "receipts": 0, "last_hash": "GENESIS"}
        conn = self._connect()
        rows = conn.execute("SELECT * FROM receipts ORDER BY sequence").fetchall()
        conn.close()
        previous_hash = "GENESIS"
        for row in rows:
            expected = hashlib.sha256(f"{previous_hash}\n{row['payload_json']}".encode()).hexdigest()
            if row["previous_hash"] != previous_hash or row["receipt_hash"] != expected:
                return {
                    "valid": False,
                    "receipts": len(rows),
                    "failed_sequence": row["sequence"],
                }
            previous_hash = row["receipt_hash"]
        return {"valid": True, "receipts": len(rows), "last_hash": previous_hash}
