"""Strict, default-deny capability policy."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class AdmissionPolicy:
    actor_capabilities: Mapping[str, Sequence[str] | set[str] | frozenset[str]]
    injection_indicators: Sequence[str] = ()
    injection_threshold: int = 2
    max_content_bytes: int = 200_000
    model_required: bool = True
    source_required: bool = True
    _compiled_indicators: tuple[re.Pattern[str], ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.actor_capabilities, Mapping):
            raise TypeError("actor_capabilities must be an object")

        capabilities: dict[str, frozenset[str]] = {}
        for raw_actor, raw_items in self.actor_capabilities.items():
            actor = _strict_token("actor family", raw_actor)
            if isinstance(raw_items, (str, bytes)) or not isinstance(
                raw_items,
                (Sequence, set, frozenset),
            ):
                raise TypeError(f"capabilities for {actor!r} must be an array")
            items = frozenset(
                _strict_token(f"capability for {actor!r}", item) for item in raw_items
            )
            capabilities[actor] = items

        if isinstance(self.injection_indicators, (str, bytes)) or not isinstance(
            self.injection_indicators, Sequence
        ):
            raise TypeError("injection_indicators must be an array")
        if len(self.injection_indicators) > 64:
            raise ValueError("injection_indicators cannot contain more than 64 patterns")

        patterns: list[str] = []
        compiled: list[re.Pattern[str]] = []
        for index, raw_pattern in enumerate(self.injection_indicators, start=1):
            if not isinstance(raw_pattern, str):
                raise TypeError(f"injection indicator {index} must be a string")
            if not raw_pattern.strip():
                raise ValueError(f"injection indicator {index} must be non-empty")
            if len(raw_pattern.encode("utf-8")) > 4_096:
                raise ValueError(f"injection indicator {index} exceeds 4096 UTF-8 bytes")
            try:
                compiled_pattern = re.compile(raw_pattern, flags=re.IGNORECASE | re.DOTALL)
            except re.error as exc:
                raise ValueError(f"injection indicator {index} is invalid") from exc
            patterns.append(raw_pattern)
            compiled.append(compiled_pattern)

        if isinstance(self.injection_threshold, bool) or not isinstance(
            self.injection_threshold, int
        ):
            raise TypeError("injection_threshold must be an integer")
        if self.injection_threshold < 1:
            raise ValueError("injection_threshold must be at least 1")
        if patterns and self.injection_threshold > len(patterns):
            raise ValueError("injection_threshold cannot exceed the indicator count")

        if isinstance(self.max_content_bytes, bool) or not isinstance(self.max_content_bytes, int):
            raise TypeError("max_content_bytes must be an integer")
        if not 1 <= self.max_content_bytes <= 10_000_000:
            raise ValueError("max_content_bytes must be between 1 and 10000000")
        if not isinstance(self.model_required, bool):
            raise TypeError("model_required must be a boolean")
        if not isinstance(self.source_required, bool):
            raise TypeError("source_required must be a boolean")

        object.__setattr__(self, "actor_capabilities", MappingProxyType(capabilities))
        object.__setattr__(self, "injection_indicators", tuple(patterns))
        object.__setattr__(self, "_compiled_indicators", tuple(compiled))

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> AdmissionPolicy:
        if not isinstance(value, dict):
            raise TypeError("policy must be a JSON object")
        capabilities = value.get("actor_capabilities", {})
        indicators = value.get("injection_indicators", [])
        return cls(
            actor_capabilities=capabilities,
            injection_indicators=indicators,
            injection_threshold=value.get("injection_threshold", 2),
            max_content_bytes=value.get("max_content_bytes", 200_000),
            model_required=value.get("model_required", True),
            source_required=value.get("source_required", True),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> AdmissionPolicy:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def allows(self, actor_family: str, capability: str) -> bool:
        return capability in self.actor_capabilities.get(actor_family, frozenset())

    @property
    def compiled_indicators(self) -> tuple[re.Pattern[str], ...]:
        return self._compiled_indicators


def _strict_token(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value.strip():
        raise ValueError(f"{label} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{label} must not include surrounding whitespace")
    if len(value.encode("utf-8")) > 1_024:
        raise ValueError(f"{label} exceeds 1024 UTF-8 bytes")
    return value
