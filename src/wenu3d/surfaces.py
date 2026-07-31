from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np


Vector3 = tuple[float, float, float]


def _vector3(value: Sequence[float], *, field_name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{field_name} must contain exactly three values.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return vector


def _unit_vector(value: np.ndarray, *, field_name: str) -> np.ndarray:
    scale = float(np.max(np.abs(value)))
    if scale == 0.0:
        raise ValueError(f"{field_name} must be non-zero.")
    scaled = value / scale
    norm = float(np.linalg.norm(scaled))
    if not np.isfinite(norm) or norm == 0.0:
        raise ValueError(f"{field_name} must define a finite direction.")
    return scaled / norm


def _tuple3(value: np.ndarray) -> Vector3:
    return tuple(float(component) for component in value)


@dataclass(frozen=True)
class SurfaceStyle:
    """Renderer-neutral styling for a finite surface."""

    color: str = "#c8c9c8"
    opacity: float = 0.5
    show_edges: bool = True
    edge_color: str = "#777777"
    edge_width: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Surface color must be a non-empty string.")
        if not isinstance(self.edge_color, str) or not self.edge_color.strip():
            raise ValueError("Surface edge color must be a non-empty string.")
        if not isinstance(self.show_edges, (bool, np.bool_)):
            raise TypeError("Surface show_edges must be a boolean.")

        opacity = float(self.opacity)
        edge_width = float(self.edge_width)
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Surface opacity must be finite and between zero and one."
            )
        if not np.isfinite(edge_width) or edge_width <= 0.0:
            raise ValueError(
                "Surface edge width must be finite and greater than zero."
            )

        object.__setattr__(self, "color", self.color.strip())
        object.__setattr__(self, "opacity", opacity)
        object.__setattr__(self, "show_edges", bool(self.show_edges))
        object.__setattr__(self, "edge_color", self.edge_color.strip())
        object.__setattr__(self, "edge_width", edge_width)


@dataclass(frozen=True)
class PlaneSurface:
    """Finite rectangular plane with an explicit right-handed local frame."""

    center: Sequence[float]
    normal: Sequence[float]
    axis_u: Sequence[float]
    width: float
    height: float
    style: SurfaceStyle = field(default_factory=SurfaceStyle)
    visible: bool = True
    axis_v: Vector3 = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.style, SurfaceStyle):
            raise TypeError("PlaneSurface style must be a SurfaceStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("PlaneSurface visible must be a boolean.")

        center = _vector3(self.center, field_name="center")
        normal = _unit_vector(
            _vector3(self.normal, field_name="normal"),
            field_name="normal",
        )
        raw_axis_u = _vector3(self.axis_u, field_name="axis_u")
        projected_axis_u = raw_axis_u - np.dot(raw_axis_u, normal) * normal
        axis_u = _unit_vector(projected_axis_u, field_name="axis_u")
        axis_v = _unit_vector(
            np.cross(normal, axis_u),
            field_name="axis_v",
        )

        width = float(self.width)
        height = float(self.height)
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError(
                "PlaneSurface width must be finite and greater than zero."
            )
        if not np.isfinite(height) or height <= 0.0:
            raise ValueError(
                "PlaneSurface height must be finite and greater than zero."
            )
        with np.errstate(over="ignore", invalid="ignore"):
            area = width * height
        if not np.isfinite(area):
            raise ValueError("PlaneSurface dimensions must define finite area.")

        with np.errstate(over="ignore", invalid="ignore"):
            corners = _corners(center, axis_u, axis_v, width, height)
        if not np.all(np.isfinite(corners)):
            raise ValueError("PlaneSurface corners must contain finite values.")

        object.__setattr__(self, "center", _tuple3(center))
        object.__setattr__(self, "normal", _tuple3(normal))
        object.__setattr__(self, "axis_u", _tuple3(axis_u))
        object.__setattr__(self, "axis_v", _tuple3(axis_v))
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "visible", bool(self.visible))

    @property
    def area(self) -> float:
        return self.width * self.height

    def corners(self) -> np.ndarray:
        """Return four counterclockwise corners viewed along the normal."""
        return _corners(
            np.asarray(self.center),
            np.asarray(self.axis_u),
            np.asarray(self.axis_v),
            self.width,
            self.height,
        )

    @property
    def face(self) -> tuple[int, int, int, int]:
        return (0, 1, 2, 3)


def _corners(
    center: np.ndarray,
    axis_u: np.ndarray,
    axis_v: np.ndarray,
    width: float,
    height: float,
) -> np.ndarray:
    half_u = 0.5 * width * axis_u
    half_v = 0.5 * height * axis_v
    return np.asarray(
        (
            center - half_u - half_v,
            center + half_u - half_v,
            center + half_u + half_v,
            center - half_u + half_v,
        )
    )
