from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from .geometry import unit


def _vector3(value: Sequence[float], *, name: str) -> tuple[float, float, float]:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain three finite components.")
    return tuple(float(component) for component in vector)


@dataclass(frozen=True)
class VectorStyle:
    color: str = "#59645d"
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Vector color must be a non-empty string.")
        opacity = float(self.opacity)
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Vector opacity must be finite and between zero and one."
            )
        object.__setattr__(self, "color", self.color.strip())
        object.__setattr__(self, "opacity", opacity)


@dataclass(frozen=True)
class VectorArrow:
    start: Sequence[float]
    direction: Sequence[float]
    scale: float
    style: VectorStyle = field(default_factory=VectorStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style, VectorStyle):
            raise TypeError("VectorArrow style must be a VectorStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("VectorArrow visible must be a boolean.")
        start = _vector3(self.start, name="Vector start")
        direction = tuple(
            float(component)
            for component in unit(
                _vector3(self.direction, name="Vector direction")
            )
        )
        scale = float(self.scale)
        if not np.isfinite(scale) or scale <= 0.0:
            raise ValueError("Vector scale must be finite and greater than zero.")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "scale", scale)
        object.__setattr__(self, "visible", bool(self.visible))
