"""Pure admission evaluation. The host remains responsible for authenticating runtimes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time
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

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AdmissionRequest":
        return cls(
            claimed_actor=str(value.get("claimed_actor", "")),
            actor_family=str(value.get("actor_family", "unknown")),
            runtime_family=str(value.get("runtime_family", "unknown")),
            capability=str(value.get("capability", "mutation")),
            action=str(value.get("action", "unknown")),
            model=str(value["model"]) if value.get("model") else None,
            content=value.get("content"),
            source=str(value.get("source", "unspecified")),
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
        return asdict(self)


def _content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return json.dumps(content, sort_keys=True, ensure_ascii=False, default=str)


def evaluate(request: AdmissionRequest, policy: AdmissionPolicy) -> AdmissionDecision:
    text = _content_text(request.content)
    raw = text.encode("utf-8", errors="replace")
    content_hash = hashlib.sha256(raw).hexdigest()
    request_id = f"pc-{int(time.time() * 1000):x}-{content_hash[:8]}"
    reasons: list[str] = []

    if not request.claimed_actor.strip():
        reasons.append("missing_claimed_actor")
    if request.actor_family == "unknown" or request.runtime_family == "unknown":
        reasons.append("unknown_identity_family")
    if request.actor_family != request.runtime_family:
        reasons.append("runtime_actor_family_mismatch")
    if not policy.allows(request.actor_family, request.capability):
        reasons.append(f"capability_not_allowed:{request.capability}")
    if len(raw) > policy.max_content_bytes:
        reasons.append("content_too_large")
    if policy.model_required and not request.model:
        reasons.append("model_unreported")

    matches: list[str] = []
    for index, pattern in enumerate(policy.injection_indicators, start=1):
        try:
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                matches.append(f"indicator_{index}")
        except re.error:
            reasons.append(f"invalid_policy_pattern:{index}")
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

