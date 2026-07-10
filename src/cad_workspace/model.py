from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Callable


class SpecError(ValueError):
    """Raised when model parameters cannot be applied."""


class CadModel:
    def __init__(
        self,
        *,
        name: str,
        description: str,
        spec_type: type,
        build: Callable[[Any], Any],
    ) -> None:
        if not is_dataclass(spec_type):
            raise TypeError("spec_type must be a dataclass type")

        self.name = name
        self.description = description
        self.spec_type = spec_type
        self.build = build

    def default_spec(self) -> Any:
        return self.spec_type()

    def spec_fields(self) -> list[tuple[str, type, Any]]:
        return [(field.name, field.type, field.default) for field in fields(self.spec_type)]

    def spec_with_overrides(self, overrides: dict[str, str]) -> Any:
        values = {field.name: field.default for field in fields(self.spec_type)}
        field_types = {field.name: field.type for field in fields(self.spec_type)}

        unknown = sorted(set(overrides) - set(values))
        if unknown:
            raise SpecError(f"Unknown parameter(s) for {self.name}: {', '.join(unknown)}")

        for name, value in overrides.items():
            values[name] = coerce_value(value, field_types[name])

        return self.spec_type(**values)


def coerce_value(raw_value: str, target_type: type) -> Any:
    if target_type is bool:
        normalized = raw_value.lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
        raise SpecError(f"Expected a boolean value, got {raw_value!r}")

    if target_type in {int, float, str}:
        return target_type(raw_value)

    return raw_value

