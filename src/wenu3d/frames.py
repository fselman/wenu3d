from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .geometry import unit


@dataclass(frozen=True)
class SphericalFrame:
    name: str
    pole: np.ndarray
    zero: np.ndarray
    east: np.ndarray | None = None

    def __post_init__(self) -> None:
        pole = unit(self.pole)

        zero = np.asarray(self.zero, dtype=float)
        zero = unit(zero - np.dot(zero, pole) * pole)

        if self.east is None:
            east = unit(np.cross(pole, zero))
        else:
            east = np.asarray(self.east, dtype=float)
            east = unit(
                east
                - np.dot(east, pole) * pole
                - np.dot(east, zero) * zero
            )

        object.__setattr__(self, "pole", pole)
        object.__setattr__(self, "zero", zero)
        object.__setattr__(self, "east", east)

    def point(self, longitude_deg, latitude_deg, radius: float = 1.0) -> np.ndarray:
        lon = np.deg2rad(np.asarray(longitude_deg, dtype=float))
        lat = np.deg2rad(np.asarray(latitude_deg, dtype=float))
        lon, lat = np.broadcast_arrays(lon, lat)

        c = np.cos(lat)
        return radius * (
            (c * np.cos(lon))[..., None] * self.zero
            + (c * np.sin(lon))[..., None] * self.east
            + np.sin(lat)[..., None] * self.pole
        )


def horizontal_frame() -> SphericalFrame:
    # Local Cartesian convention:
    # +x East, +y North, +z Zenith
    return SphericalFrame(
        name="horizontal",
        pole=np.array([0.0, 0.0, 1.0]),
        zero=np.array([0.0, 1.0, 0.0]),
        east=np.array([1.0, 0.0, 0.0]),
    )


def equatorial_frame(latitude_deg: float) -> SphericalFrame:
    lat = np.deg2rad(latitude_deg)

    ncp = unit(np.array([0.0, np.cos(lat), np.sin(lat)]))
    zenith = np.array([0.0, 0.0, 1.0])

    # RA zero chosen on the upper local meridian.
    zero = unit(zenith - np.dot(zenith, ncp) * ncp)

    return SphericalFrame(
        name="equatorial",
        pole=ncp,
        zero=zero,
    )
