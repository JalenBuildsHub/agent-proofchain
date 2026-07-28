"""Default-deny capability policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdmissionPolicy:
    actor_capabilities: dict[str, frozenset[str]]
    injection_indicators: tuple[str, ...]
    injection_threshold: int = 2
    max_content_bytes: int = 200_000
    model_required: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> AdmissionPolicy:
        capabilities = {
            str(actor): frozenset(str(item) for item in items)
            for actor, items in value.get("actor_capabilities", {}).items()
        }
        threshold = int(value.get("injection_threshold", 2))
        if threshold < 1:
            raise ValueError("injection_threshold must be at least 1")
        max_bytes = int(value.get("max_content_bytes", 200_000))
        if max_bytes < 1:
            raise ValueError("max_content_bytes must be positive")
        return cls(
            actor_capabilities=capabilities,
            injection_indicators=tuple(str(item) for item in value.get("injection_indicators", [])),
            injection_threshold=threshold,
            max_content_bytes=max_bytes,
            model_required=bool(value.get("model_required", True)),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> AdmissionPolicy:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def allows(self, actor_family: str, capability: str) -> bool:
        return capability in self.actor_capabilities.get(actor_family, frozenset())
