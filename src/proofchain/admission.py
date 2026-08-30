"""Pure admission evaluation. The host remains responsible for authenticating runtimes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from time import time_ns
from typing import Any

from .policy import AdmissionPolicy


@dataclass(frozen=True)
class AdmissionRequest:
    claimed_actor: str
    actor_family: str
    runtime_family: str
    capability: str
    action: str
    model: str | None
    content: Any = None
    source: str = "unspecified"

    def __post_init__(self) -> None:
        for field_name in (
            "claimed_actor",
            "actor_family",
            "runtime_family",
            "capability",
            "action",
            "source",
        ):
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string")
        if self.model is not None and not isinstance(self.model, str):
            raise TypeError("model must be a string or null")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> AdmissionRequest:
        if not isinstance(value, dict):
            raise TypeError("admission request must be a JSON object")
        return cls(
            claimed_actor=_request_text(value, "claimed_actor", ""),
            actor_family=_request_text(value, "actor_family", "unknown"),
            runtime_family=_request_text(value, "runtime_family", "unknown"),
            capability=_request_text(value, "capability", ""),
            action=_request_text(value, "action", ""),
            model=_request_optional_text(value, "model"),
            content=value.get("content"),
            source=_request_text(value, "source", "unspecified"),
        )


@dataclass(frozen=True)
class AdmissionDecision:
    request_id: str
    allowed: bool
    decision: str
    reason_codes: tuple[str, ...]
    content_sha256: str
    injection_matches: tuple[str, ...]
    claimed_actor: str
    actor_family: str
    runtime_family: str
    capability: str
    action: str
    model: str
    source: str

    def to_receipt(self) -> dict[str, Any]:
        """Return a persistence-safe receipt without caller-controlled plaintext."""
        return {
            "schema_version": 2,
            "request_id": self.request_id,
            "allowed": self.allowed,
            "decision": self.decision,
            "reason_codes": self.reason_codes,
            "content_sha256": self.content_sha256,
            "injection_matches": self.injection_matches,
            "claimed_actor_sha256": _text_sha256(self.claimed_actor),
            "actor_family_sha256": _text_sha256(self.actor_family),
            "runtime_family_sha256": _text_sha256(self.runtime_family),
            "capability_sha256": _text_sha256(self.capability),
            "action_sha256": _text_sha256(self.action),
            "model_sha256": _text_sha256(self.model),
            "source_sha256": _text_sha256(self.source),
        }


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _content_text(content: Any) -> tuple[str, bool]:
    if content is None:
        return "", True
    if isinstance(content, str):
        return content, True
    try:
        return (
            json.dumps(
                content,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ),
            True,
        )
    except (TypeError, ValueError):
        return "", False


def evaluate(request: AdmissionRequest, policy: AdmissionPolicy) -> AdmissionDecision:
    text, content_valid = _content_text(request.content)
    raw = text.encode("utf-8", errors="replace")
    content_hash = hashlib.sha256(raw).hexdigest()
    request_id = f"pc-{time_ns():x}-{content_hash[:8]}"
    reasons: list[str] = []

    if not request.claimed_actor.strip():
        reasons.append("missing_claimed_actor")
    if (
        not request.actor_family.strip()
        or not request.runtime_family.strip()
        or request.actor_family.casefold() == "unknown"
        or request.runtime_family.casefold() == "unknown"
    ):
        reasons.append("unknown_identity_family")
    if request.actor_family != request.runtime_family:
        reasons.append("runtime_actor_family_mismatch")
    if not request.capability.strip():
        reasons.append("capability_unreported")
    if not policy.allows(request.actor_family, request.capability):
        reasons.append("capability_not_allowed")
    if not request.action.strip():
        reasons.append("action_unreported")
    if not content_valid:
        reasons.append("content_not_json_serializable")
    if len(raw) > policy.max_content_bytes:
        reasons.append("content_too_large")
    if policy.model_required and (not request.model or not request.model.strip()):
        reasons.append("model_unreported")
    if policy.source_required and (
        not request.source.strip() or request.source.casefold() == "unspecified"
    ):
        reasons.append("source_unreported")

    matches: list[str] = []
    if content_valid and len(raw) <= policy.max_content_bytes:
        for index, pattern in enumerate(policy.compiled_indicators, start=1):
            if pattern.search(text):
                matches.append(f"indicator_{index}")
    if len(matches) >= policy.injection_threshold:
        reasons.extend(matches)
        reasons.append("injection_threshold_met")

    allowed = not reasons
    return AdmissionDecision(
        request_id=request_id,
        allowed=allowed,
        decision="allow" if allowed else "deny",
        reason_codes=tuple(reasons),
        content_sha256=content_hash,
        injection_matches=tuple(matches),
        claimed_actor=request.claimed_actor,
        actor_family=request.actor_family,
        runtime_family=request.runtime_family,
        capability=request.capability,
        action=request.action,
        model=request.model or "unreported",
        source=request.source,
    )


def _request_text(value: dict[str, Any], field: str, default: str) -> str:
    candidate = value.get(field, default)
    if not isinstance(candidate, str):
        raise TypeError(f"{field} must be a string")
    return candidate


def _request_optional_text(value: dict[str, Any], field: str) -> str | None:
    candidate = value.get(field)
    if candidate is None:
        return None
    if not isinstance(candidate, str):
        raise TypeError(f"{field} must be a string or null")
    return candidate
