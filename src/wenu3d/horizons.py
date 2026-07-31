from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .observer_model import Observer
from .surfaces import PlaneSurface, SurfaceStyle


def _points3(value, *, field_name: str) -> np.ndarray:
    points = np.asarray(value, dtype=float)
    if points.ndim == 0 or points.shape[-1] != 3:
        raise ValueError(f"{field_name} must end with three components.")
    if not np.all(np.isfinite(points)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return points


@dataclass(frozen=True, eq=False)
class IdealHorizon:
    """Observer-specific plane through the celestial origin."""

    observer: Observer

    def __post_init__(self) -> None:
        if not isinstance(self.observer, Observer):
            raise TypeError("Ideal-horizon observer must be an Observer.")
        frame = self.observer.frame
        if not np.allclose(
            np.cross(frame.east, frame.zero),
            frame.pole,
            atol=1e-12,
        ):
            raise ValueError(
                "Ideal-horizon observer frame must use East-North-Zenith "
                "handedness."
            )

    @property
    def origin(self) -> np.ndarray:
        return np.zeros(3, dtype=float)

    @property
    def normal(self) -> np.ndarray:
        return self.observer.frame.pole.copy()

    @property
    def east(self) -> np.ndarray:
        return self.observer.frame.east.copy()

    @property
    def north(self) -> np.ndarray:
        return self.observer.frame.zero.copy()

    def signed_distance(self, points) -> float | np.ndarray:
        """Return signed perpendicular distance from the ideal horizon."""
        values = _points3(points, field_name="points") @ self.normal
        if np.ndim(values) == 0:
            return float(values)
        return values

    def project(self, points) -> np.ndarray:
        """Orthogonally project one or more points onto the ideal horizon."""
        values = _points3(points, field_name="points")
        distances = np.asarray(self.signed_distance(values))
        return values - distances[..., np.newaxis] * self.normal

    def as_surface(
        self,
        *,
        width: float,
        height: float | None = None,
        style: SurfaceStyle | None = None,
        visible: bool = False,
    ) -> PlaneSurface:
        """Return an optional finite display surface for this infinite plane."""
        return PlaneSurface(
            center=self.origin,
            normal=self.normal,
            axis_u=self.east,
            width=width,
            height=width if height is None else height,
            style=style or SurfaceStyle(),
            visible=visible,
        )
