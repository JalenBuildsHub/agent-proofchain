"""Provider-neutral distribution execution receipts."""

from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass
from typing import Any, Literal

DistributionStatus = Literal[
    "draft_created",
    "scheduled",
    "published",
    "failed",
    "reconciled",
]

_DISTRIBUTION_STATUSES = frozenset(
    {"draft_created", "scheduled", "published", "failed", "reconciled"}
)


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _require_sha256(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in string.hexdigits for character in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


@dataclass(frozen=True)
class DistributionExecutionReceipt:
    """Evidence for one guarded social-distribution side effect.

    Caller-controlled identifiers are persisted as SHA-256 correlation digests.
    The host remains responsible for authenticating the values, consuming the
    PermitMesh nonce atomically, and retaining any private lookup mapping.
    """

    event_id: str
    idempotency_key: str
    brand_id: str
    platform: str
    integration_id: str
    source_commit: str
    approval_artifact_id: str
    permit_contract_digest: str
    permit_decision_digest: str
    request_sha256: str
    status: DistributionStatus
    captured_at: str
    provider_post_ids: tuple[str, ...] = ()
    error_code: str | None = None

    def to_receipt(self) -> dict[str, Any]:
        for name, value in (
            ("event_id", self.event_id),
            ("idempotency_key", self.idempotency_key),
            ("brand_id", self.brand_id),
            ("platform", self.platform),
            ("integration_id", self.integration_id),
            ("source_commit", self.source_commit),
            ("approval_artifact_id", self.approval_artifact_id),
            ("captured_at", self.captured_at),
        ):
            _require_text(name, value)
        if self.status not in _DISTRIBUTION_STATUSES:
            raise ValueError("status must be a supported distribution receipt status")
        _require_sha256("request_sha256", self.request_sha256)
        _require_sha256("permit_contract_digest", self.permit_contract_digest)
        _require_sha256("permit_decision_digest", self.permit_decision_digest)

        return {
            "schema_version": 1,
            "receipt_type": "distribution_execution",
            "event_id_sha256": _text_sha256(self.event_id),
            "idempotency_key_sha256": _text_sha256(self.idempotency_key),
            "brand_id_sha256": _text_sha256(self.brand_id),
            "platform_sha256": _text_sha256(self.platform),
            "integration_id_sha256": _text_sha256(self.integration_id),
            "source_commit_sha256": _text_sha256(self.source_commit),
            "approval_artifact_id_sha256": _text_sha256(self.approval_artifact_id),
            "permit_contract_digest": self.permit_contract_digest,
            "permit_decision_digest": self.permit_decision_digest,
            "request_sha256": self.request_sha256,
            "status": self.status,
            "captured_at": self.captured_at,
            "provider_post_id_sha256": [
                _text_sha256(provider_post_id)
                for provider_post_id in self.provider_post_ids
            ],
            "error_code": self.error_code,
        }
