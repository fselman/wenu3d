from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .frames import SphericalFrame
from .geography import geographic_position, local_enu_frame


def _finite_position(value, *, name: str) -> np.ndarray:
    position = np.asarray(value, dtype=float)
    if position.shape != (3,) or not np.all(np.isfinite(position)):
        raise ValueError(f"{name} must contain three finite components.")
    result = position.copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True, eq=False)
class Observer:
    """Renderer-neutral observer identity, position, and local frame."""

    name: str
    position: np.ndarray
    frame: SphericalFrame
    latitude_deg: float | None = None
    longitude_deg: float | None = None

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("Observer name must not be empty.")
        if not isinstance(self.frame, SphericalFrame):
            raise TypeError("Observer frame must be a SphericalFrame.")

        position = _finite_position(self.position, name="Observer position")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "position", position)

        latitude = self.latitude_deg
        longitude = self.longitude_deg
        if (latitude is None) != (longitude is None):
            raise ValueError(
                "Geographic latitude and longitude must be supplied together."
            )
        if latitude is None:
            return

        radius = float(np.linalg.norm(position))
        if radius == 0.0:
            raise ValueError(
                "A geographic observer position must have nonzero radius."
            )
        expected_position = geographic_position(
            latitude,
            longitude,
            radius=radius,
        )
        expected_frame = local_enu_frame(latitude, longitude)
        if not np.allclose(position, expected_position, atol=1e-12):
            raise ValueError(
                "Observer position does not match its geographic location."
            )
        for actual, expected in (
            (self.frame.east, expected_frame.east),
            (self.frame.zero, expected_frame.zero),
            (self.frame.pole, expected_frame.pole),
        ):
            if not np.allclose(actual, expected, atol=1e-12):
                raise ValueError(
                    "Observer frame does not match its geographic location."
                )

        object.__setattr__(self, "latitude_deg", float(latitude))
        object.__setattr__(self, "longitude_deg", float(longitude))

    @classmethod
    def at_geographic_site(
        cls,
        name: str,
        *,
        latitude_deg: float,
        longitude_deg: float,
        earth_radius: float,
    ) -> Observer:
        return cls(
            name=name,
            position=geographic_position(
                latitude_deg,
                longitude_deg,
                radius=earth_radius,
            ),
            frame=local_enu_frame(latitude_deg, longitude_deg),
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
        )

    def antipode(self, name: str) -> Observer:
        """Return a geographic observer at the opposite point on Earth."""
        if self.latitude_deg is None or self.longitude_deg is None:
            raise ValueError(
                "An antipode requires a geographic observer."
            )
        antipodal_longitude = (
            (self.longitude_deg + 360.0) % 360.0 - 180.0
        )
        return Observer.at_geographic_site(
            name,
            latitude_deg=-self.latitude_deg,
            longitude_deg=antipodal_longitude,
            earth_radius=float(np.linalg.norm(self.position)),
        )
