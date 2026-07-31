from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np


Vector3 = tuple[float, float, float]
MarkerShape = Literal["sphere", "star"]


def _vector3(value: Sequence[float], *, field_name: str) -> Vector3:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{field_name} must contain exactly three values.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return tuple(float(component) for component in vector)


@dataclass(frozen=True)
class MarkerStyle:
    """Renderer-neutral styling for a finite-position marker."""

    shape: MarkerShape = "sphere"
    color: str = "#d4a72c"
    radius: float = 0.025
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if self.shape not in ("sphere", "star"):
            raise ValueError("Marker shape must be 'sphere' or 'star'.")
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Marker color must be a non-empty string.")

        radius = float(self.radius)
        opacity = float(self.opacity)
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError(
                "Marker radius must be finite and greater than zero."
            )
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Marker opacity must be finite and between zero and one."
            )

        object.__setattr__(self, "color", self.color.strip())
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "opacity", opacity)


@dataclass(frozen=True)
class Marker:
    """Renderer-neutral marker at an explicit finite Cartesian position."""

    position: Sequence[float]
    style: MarkerStyle = field(default_factory=MarkerStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style, MarkerStyle):
            raise TypeError("Marker style must be a MarkerStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("Marker visible must be a boolean.")

        object.__setattr__(
            self,
            "position",
            _vector3(self.position, field_name="position"),
        )
        object.__setattr__(self, "visible", bool(self.visible))
