from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from .frames import SphericalFrame


Vector3 = tuple[float, float, float]
ArrowheadPlacement = Literal["none", "start", "end", "both"]


def _validate_samples(samples: int) -> None:
    if (
        isinstance(samples, (bool, np.bool_))
        or not isinstance(samples, (int, np.integer))
        or samples < 2
    ):
        raise ValueError("Samples must be an integer greater than or equal to 2.")


def _curve_points(value: Sequence[Sequence[float]]) -> tuple[Vector3, ...]:
    try:
        points = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Curve points must be a rectangular array of Cartesian vectors."
        ) from error

    if points.ndim != 2 or points.shape[1:] != (3,) or points.shape[0] < 2:
        raise ValueError(
            "Curve points must have shape (n, 3) with at least two points."
        )
    if not np.all(np.isfinite(points)):
        raise ValueError("Curve points must contain only finite values.")

    with np.errstate(over="ignore", invalid="ignore"):
        differences = np.diff(points, axis=0)
        scales = np.max(np.abs(differences), axis=1)
        scaled = differences / scales[:, np.newaxis]
        lengths = scales * np.linalg.norm(scaled, axis=1)
    if not np.all(np.isfinite(lengths)) or np.any(lengths <= 0.0):
        raise ValueError(
            "Consecutive curve points must define finite, non-zero segments."
        )

    return tuple(
        tuple(float(component) for component in point)
        for point in points
    )


@dataclass(frozen=True)
class CurveStyle:
    """Renderer-neutral styling for a sampled Cartesian curve."""

    color: str = "#444444"
    width: float = 2.0
    opacity: float = 1.0
    arrowheads: ArrowheadPlacement = "none"
    arrow_size: float = 0.04

    def __post_init__(self) -> None:
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Curve color must be a non-empty string.")
        if self.arrowheads not in ("none", "start", "end", "both"):
            raise ValueError(
                "Curve arrowheads must be 'none', 'start', 'end', or 'both'."
            )

        width = float(self.width)
        opacity = float(self.opacity)
        arrow_size = float(self.arrow_size)
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError(
                "Curve width must be finite and greater than zero."
            )
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Curve opacity must be finite and between zero and one."
            )
        if not np.isfinite(arrow_size) or arrow_size <= 0.0:
            raise ValueError(
                "Curve arrow size must be finite and greater than zero."
            )

        object.__setattr__(self, "color", self.color.strip())
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "opacity", opacity)
        object.__setattr__(self, "arrow_size", arrow_size)


@dataclass(frozen=True)
class SampledCurve:
    """Renderer-neutral curve defined by ordered finite Cartesian samples."""

    points: Sequence[Sequence[float]]
    style: CurveStyle = field(default_factory=CurveStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style, CurveStyle):
            raise TypeError("SampledCurve style must be a CurveStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("SampledCurve visible must be a boolean.")

        object.__setattr__(self, "points", _curve_points(self.points))
        object.__setattr__(self, "visible", bool(self.visible))

    def as_array(self) -> np.ndarray:
        """Return the sampled points as a new floating-point array."""
        return np.asarray(self.points, dtype=float)


@dataclass(frozen=True)
class Meridian:
    frame: SphericalFrame
    longitude_deg: float
    latitude_min_deg: float = -90.0
    latitude_max_deg: float = 90.0
    samples: int = 361

    def __post_init__(self) -> None:
        values = (
            self.longitude_deg,
            self.latitude_min_deg,
            self.latitude_max_deg,
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("Meridian angles must be finite.")
        if not -90.0 <= self.latitude_min_deg <= 90.0:
            raise ValueError(
                "Meridian minimum latitude must be between -90 and 90 degrees."
            )
        if not -90.0 <= self.latitude_max_deg <= 90.0:
            raise ValueError(
                "Meridian maximum latitude must be between -90 and 90 degrees."
            )
        if self.latitude_min_deg >= self.latitude_max_deg:
            raise ValueError(
                "Meridian minimum latitude must be less than maximum latitude."
            )
        _validate_samples(self.samples)

    def points(self, radius: float = 1.0) -> np.ndarray:
        lat = np.linspace(
            self.latitude_min_deg,
            self.latitude_max_deg,
            self.samples,
        )
        lon = np.full_like(lat, self.longitude_deg)
        return self.frame.point(lon, lat, radius=radius)


@dataclass(frozen=True)
class Parallel:
    frame: SphericalFrame
    latitude_deg: float
    longitude_min_deg: float = 0.0
    longitude_max_deg: float = 360.0
    samples: int = 721

    def __post_init__(self) -> None:
        values = (
            self.latitude_deg,
            self.longitude_min_deg,
            self.longitude_max_deg,
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("Parallel angles must be finite.")
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError(
                "Parallel latitude must be between -90 and 90 degrees."
            )
        if self.longitude_min_deg >= self.longitude_max_deg:
            raise ValueError(
                "Parallel minimum longitude must be less than maximum longitude."
            )
        _validate_samples(self.samples)

    def points(self, radius: float = 1.0) -> np.ndarray:
        lon = np.linspace(
            self.longitude_min_deg,
            self.longitude_max_deg,
            self.samples,
        )
        lat = np.full_like(lon, self.latitude_deg)
        return self.frame.point(lon, lat, radius=radius)
