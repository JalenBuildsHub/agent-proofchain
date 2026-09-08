"""Provider-neutral runtime adapter contracts.

Adapters translate provider-specific event payloads into :class:`AdmissionRequest`
instances. Identity, model attribution, and source metadata come from a host-authenticated
context rather than caller-controlled payload fields.
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
    claimed_actor: str
    actor_family: str
    runtime_family: str
    model: str | None
    source: str
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        required: dict[str, object] = {
            "provider": self.provider,
            "claimed_actor": self.claimed_actor,
            "actor_family": self.actor_family,
            "runtime_family": self.runtime_family,
            "source": self.source,
        }
        for field, value in required.items():
            _strict_context_text(field, value)
        if self.model is not None:
            _strict_context_text("model", self.model)
        if self.provider_request_id is not None:
            _strict_context_text("provider_request_id", self.provider_request_id)


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

    Only task intent is read from ``payload``. Actor identity, runtime family, model
    attribution, source, and provider request identity come from ``context``.
    """

    provider: str
    capability_field: str = "capability"
    action_field: str = "action"
    content_field: str = "content"

    def __post_init__(self) -> None:
        for field, value in {
            "provider": self.provider,
            "capability_field": self.capability_field,
            "action_field": self.action_field,
            "content_field": self.content_field,
        }.items():
            _strict_context_text(field, value)

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
            claimed_actor=context.claimed_actor,
            actor_family=context.actor_family,
            runtime_family=context.runtime_family,
            capability=_required_payload_text(payload, self.capability_field),
            action=_required_payload_text(payload, self.action_field),
            model=context.model,
            content=payload.get(self.content_field),
            source=context.source,
        )
        return NormalizedRuntimeRequest(
            request=request,
            provider=self.provider,
            provider_request_id=context.provider_request_id,
        )


class OpenAIAdapter(MappingRuntimeAdapter):
    """Mapping contract for OpenAI-hosted requests."""

    def __init__(self) -> None:
        super().__init__(provider="openai")


class AnthropicAdapter(MappingRuntimeAdapter):
    """Mapping contract for Anthropic-hosted requests."""

    def __init__(self) -> None:
        super().__init__(provider="anthropic")


class GoogleAdapter(MappingRuntimeAdapter):
    """Mapping contract for Google-hosted requests."""

    def __init__(self) -> None:
        super().__init__(provider="google")


class LocalRuntimeAdapter(MappingRuntimeAdapter):
    """Mapping contract for a locally authenticated runtime."""

    def __init__(self) -> None:
        super().__init__(provider="local")


def _strict_context_text(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise AdapterContractError(f"{field} must be a string")
    if not value.strip():
        raise AdapterContractError(f"{field} must be non-empty")
    if value != value.strip():
        raise AdapterContractError(f"{field} must not include surrounding whitespace")
    if len(value.encode("utf-8")) > 1_024:
        raise AdapterContractError(f"{field} exceeds 1024 UTF-8 bytes")
    return value


def _required_payload_text(payload: Mapping[str, Any], field: str) -> str:
    if field not in payload:
        raise AdapterContractError(f"payload requires {field}")
    value = payload[field]
    if not isinstance(value, str):
        raise AdapterContractError(f"payload {field} must be a string")
    if not value.strip():
        raise AdapterContractError(f"payload {field} must be non-empty")
    if value != value.strip():
        raise AdapterContractError(f"payload {field} must not include surrounding whitespace")
    if len(value.encode("utf-8")) > 1_024:
        raise AdapterContractError(f"payload {field} exceeds 1024 UTF-8 bytes")
    return value
