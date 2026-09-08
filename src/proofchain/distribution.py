"""Provider-neutral distribution execution receipts."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
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
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_provider_post_ids(value: object, status: DistributionStatus) -> Sequence[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("provider_post_ids must be a sequence of non-empty strings")
    if any(not isinstance(post_id, str) or not post_id.strip() for post_id in value):
        raise ValueError("provider_post_ids must contain only non-empty strings")
    if status in {"published", "reconciled"} and not value:
        raise ValueError(f"provider_post_ids are required for {status} receipts")
    return value


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
        provider_post_ids = _require_provider_post_ids(self.provider_post_ids, self.status)

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
                _text_sha256(provider_post_id) for provider_post_id in provider_post_ids
            ],
            "error_code": self.error_code,
        }
