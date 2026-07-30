from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .frames import SphericalFrame


def _validate_samples(samples: int) -> None:
    if (
        isinstance(samples, (bool, np.bool_))
        or not isinstance(samples, (int, np.integer))
        or samples < 2
    ):
        raise ValueError("Samples must be an integer greater than or equal to 2.")


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
