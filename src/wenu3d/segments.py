from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np


Vector3 = tuple[float, float, float]


def _vector3(value: Sequence[float], *, field_name: str) -> Vector3:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{field_name} must contain exactly three values.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return tuple(float(component) for component in vector)


def _validated_endpoints(
    start: Sequence[float],
    end: Sequence[float],
    *,
    start_name: str,
    end_name: str,
) -> tuple[Vector3, Vector3]:
    normalized_start = _vector3(start, field_name=start_name)
    normalized_end = _vector3(end, field_name=end_name)
    length = _length(normalized_start, normalized_end)
    if not np.isfinite(length) or length <= 0.0:
        raise ValueError(
            "Segment endpoints must define a finite, non-zero separation."
        )
    return normalized_start, normalized_end


def _length(start: Vector3, end: Vector3) -> float:
    with np.errstate(over="ignore", invalid="ignore"):
        vector = np.subtract(end, start)
        scale = float(np.max(np.abs(vector)))
        if scale == 0.0:
            return 0.0
        return float(scale * np.linalg.norm(vector / scale))


def _direction(start: Vector3, end: Vector3) -> Vector3:
    vector = np.subtract(end, start)
    scale = float(np.max(np.abs(vector)))
    scaled = vector / scale
    scaled /= np.linalg.norm(scaled)
    return tuple(float(component) for component in scaled)


@dataclass(frozen=True)
class SegmentStyle:
    """Renderer-neutral styling shared by finite line-like objects."""

    color: str = "#444444"
    width: float = 2.0
    opacity: float = 1.0
    tube_radius: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Segment color must be a non-empty string.")

        width = float(self.width)
        opacity = float(self.opacity)
        tube_radius = self.tube_radius
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError(
                "Segment width must be finite and greater than zero."
            )
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Segment opacity must be finite and between zero and one."
            )
        if tube_radius is not None:
            tube_radius = float(tube_radius)
            if not np.isfinite(tube_radius) or tube_radius <= 0.0:
                raise ValueError(
                    "Segment tube radius must be finite and positive."
                )

        object.__setattr__(self, "color", self.color.strip())
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "opacity", opacity)
        object.__setattr__(self, "tube_radius", tube_radius)


@dataclass(frozen=True)
class LineSegment:
    """Renderer-neutral finite segment with explicit Cartesian endpoints."""

    start: Sequence[float]
    end: Sequence[float]
    style: SegmentStyle = field(default_factory=SegmentStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style, SegmentStyle):
            raise TypeError("LineSegment style must be a SegmentStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("LineSegment visible must be a boolean.")

        start, end = _validated_endpoints(
            self.start,
            self.end,
            start_name="start",
            end_name="end",
        )
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "visible", bool(self.visible))

    @property
    def length(self) -> float:
        return _length(self.start, self.end)

    @property
    def direction(self) -> Vector3:
        return _direction(self.start, self.end)


@dataclass(frozen=True)
class SightLine:
    """Finite line of sight from an observer to a common target point."""

    observer_position: Sequence[float]
    target_position: Sequence[float]
    style: SegmentStyle = field(default_factory=SegmentStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style, SegmentStyle):
            raise TypeError("SightLine style must be a SegmentStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("SightLine visible must be a boolean.")

        observer, target = _validated_endpoints(
            self.observer_position,
            self.target_position,
            start_name="observer_position",
            end_name="target_position",
        )
        object.__setattr__(self, "observer_position", observer)
        object.__setattr__(self, "target_position", target)
        object.__setattr__(self, "visible", bool(self.visible))

    @property
    def start(self) -> Vector3:
        return self.observer_position

    @property
    def end(self) -> Vector3:
        return self.target_position

    @property
    def length(self) -> float:
        return _length(self.start, self.end)

    @property
    def direction(self) -> Vector3:
        return _direction(self.start, self.end)
