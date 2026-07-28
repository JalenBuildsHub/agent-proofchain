"""Provider-neutral runtime adapter contract.

Adapters translate provider-specific event payloads into :class:`AdmissionRequest`
instances. Trusted runtime identity, model attribution, and source metadata must come
from the host-supplied context rather than caller-controlled payload fields.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .admission import AdmissionRequest


class AdapterContractError(ValueError):
    """Raised when a runtime adapter cannot safely normalize an event."""


@dataclass(frozen=True)
class AuthenticatedRuntimeContext:
    """Host-authenticated metadata that caller payloads cannot override."""

    provider: str
    runtime_family: str
    model: str | None
    source: str
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise AdapterContractError("provider must be non-empty")
        if not self.runtime_family.strip():
            raise AdapterContractError("runtime_family must be non-empty")
        if not self.source.strip():
            raise AdapterContractError("source must be non-empty")


@dataclass(frozen=True)
class NormalizedRuntimeRequest:
    """A normalized request plus non-sensitive adapter provenance."""

    request: AdmissionRequest
    provider: str
    provider_request_id: str | None = None


@runtime_checkable
class RuntimeAdapter(Protocol):
    """Minimal contract for provider or runtime integrations."""

    provider: str

    def normalize(
        self,
        payload: Mapping[str, Any],
        context: AuthenticatedRuntimeContext,
    ) -> NormalizedRuntimeRequest:
        """Normalize one untrusted payload using trusted host context."""


@dataclass(frozen=True)
class MappingRuntimeAdapter:
    """Reference adapter for dictionary-shaped runtime events.

    Only task intent is read from ``payload``. Runtime family, model attribution,
    source, and provider request identity come from ``context``.
    """

    provider: str
    claimed_actor_field: str = "claimed_actor"
    actor_family_field: str = "actor_family"
    capability_field: str = "capability"
    action_field: str = "action"
    content_field: str = "content"

    def normalize(
        self,
        payload: Mapping[str, Any],
        context: AuthenticatedRuntimeContext,
    ) -> NormalizedRuntimeRequest:
        if context.provider != self.provider:
            raise AdapterContractError(
                f"adapter provider {self.provider!r} does not match context provider "
                f"{context.provider!r}"
            )
        if not isinstance(payload, Mapping):
            raise AdapterContractError("payload must be a mapping")

        request = AdmissionRequest(
            claimed_actor=str(payload.get(self.claimed_actor_field, "")),
            actor_family=str(payload.get(self.actor_family_field, "unknown")),
            runtime_family=context.runtime_family,
            capability=str(payload.get(self.capability_field, "mutation")),
            action=str(payload.get(self.action_field, "unknown")),
            model=context.model,
            content=payload.get(self.content_field),
            source=context.source,
        )
        return NormalizedRuntimeRequest(
            request=request,
            provider=self.provider,
            provider_request_id=context.provider_request_id,
        )
