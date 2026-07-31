from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .arcs import SphericalArc
from .frames import SphericalFrame
from .targets import CelestialTarget


@dataclass(frozen=True)
class HorizontalCoordinateGeometry:
    """Centered altitude and azimuth geometry for one celestial target."""

    target: CelestialTarget
    frame: SphericalFrame
    samples: int = 101
    _azimuth_deg: float = field(init=False, repr=False)
    _altitude_deg: float = field(init=False, repr=False)
    _foot_direction: tuple[float, float, float] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.target, CelestialTarget):
            raise TypeError("Horizontal target must be a CelestialTarget.")
        if not isinstance(self.frame, SphericalFrame):
            raise TypeError("Horizontal frame must be a SphericalFrame.")
        if (
            isinstance(self.samples, (bool, np.bool_))
            or not isinstance(self.samples, (int, np.integer))
            or self.samples < 2
        ):
            raise ValueError(
                "Horizontal samples must be an integer greater than or "
                "equal to 2."
            )

        direction = np.asarray(self.target.direction)
        north_component = float(direction @ self.frame.zero)
        east_component = float(direction @ self.frame.east)
        horizontal_norm = float(np.hypot(north_component, east_component))
        if horizontal_norm < 1e-12:
            raise ValueError(
                "Horizontal azimuth is undefined at Zenith or Nadir."
            )

        azimuth = np.rad2deg(np.arctan2(east_component, north_component))
        azimuth %= 360.0
        altitude = np.rad2deg(
            np.arcsin(np.clip(direction @ self.frame.pole, -1.0, 1.0))
        )
        foot = (
            north_component * self.frame.zero
            + east_component * self.frame.east
        ) / horizontal_norm

        object.__setattr__(self, "samples", int(self.samples))
        object.__setattr__(self, "_azimuth_deg", float(azimuth))
        object.__setattr__(self, "_altitude_deg", float(altitude))
        object.__setattr__(
            self,
            "_foot_direction",
            tuple(float(component) for component in foot),
        )

    @property
    def azimuth_deg(self) -> float:
        """Azimuth measured from North through East in [0, 360)."""
        return self._azimuth_deg

    @property
    def altitude_deg(self) -> float:
        return self._altitude_deg

    @property
    def vertical_circle_foot(self) -> np.ndarray:
        return self.target.shell_radius * np.asarray(self._foot_direction)

    @property
    def altitude_arc(self) -> SphericalArc | None:
        """Arc from the ideal horizon to the target along its vertical."""
        if abs(self.altitude_deg) < 1e-12:
            return None
        foot = np.asarray(self._foot_direction)
        vertical_frame = SphericalFrame(
            name=f"{self.target.name}.vertical_circle",
            pole=np.cross(foot, self.frame.pole),
            zero=foot,
            east=self.frame.pole,
        )
        return SphericalArc.great_circle(
            vertical_frame,
            start_deg=0.0,
            end_deg=self.altitude_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )

    @property
    def azimuth_arc(self) -> SphericalArc | None:
        """Arc on the ideal horizon from North to the vertical foot."""
        if self.azimuth_deg < 1e-12 or 360.0 - self.azimuth_deg < 1e-12:
            return None
        return SphericalArc.great_circle(
            self.frame,
            start_deg=0.0,
            end_deg=self.azimuth_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )
