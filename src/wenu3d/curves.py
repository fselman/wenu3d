from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .frames import SphericalFrame


@dataclass(frozen=True)
class Meridian:
    frame: SphericalFrame
    longitude_deg: float
    latitude_min_deg: float = -90.0
    latitude_max_deg: float = 90.0
    samples: int = 361

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

    def points(self, radius: float = 1.0) -> np.ndarray:
        lon = np.linspace(
            self.longitude_min_deg,
            self.longitude_max_deg,
            self.samples,
        )
        lat = np.full_like(lon, self.latitude_deg)
        return self.frame.point(lon, lat, radius=radius)
