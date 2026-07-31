from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .curves import CurveStyle, SampledCurve
from .frames import SphericalFrame


@dataclass(frozen=True)
class SphericalArc:
    """A sampled constant-latitude arc in an explicit spherical frame."""

    frame: SphericalFrame
    start_deg: float
    end_deg: float
    latitude_deg: float = 0.0
    radius: float = 1.0
    samples: int = 101

    def __post_init__(self) -> None:
        if not isinstance(self.frame, SphericalFrame):
            raise TypeError("SphericalArc frame must be a SphericalFrame.")

        start = float(self.start_deg)
        end = float(self.end_deg)
        latitude = float(self.latitude_deg)
        radius = float(self.radius)
        if not all(np.isfinite(value) for value in (start, end, latitude)):
            raise ValueError("SphericalArc angles must be finite.")
        if not -90.0 < latitude < 90.0:
            raise ValueError(
                "SphericalArc latitude must be strictly between -90 and 90 "
                "degrees."
            )

        span = end - start
        if abs(span) < 1e-12:
            raise ValueError(
                "SphericalArc start and end must define a non-zero span."
            )
        if abs(span) > 360.0:
            raise ValueError(
                "SphericalArc span must not exceed one revolution."
            )
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError(
                "SphericalArc radius must be finite and greater than zero."
            )
        if (
            isinstance(self.samples, (bool, np.bool_))
            or not isinstance(self.samples, (int, np.integer))
            or self.samples < 2
        ):
            raise ValueError(
                "SphericalArc samples must be an integer greater than or "
                "equal to 2."
            )

        object.__setattr__(self, "start_deg", start)
        object.__setattr__(self, "end_deg", end)
        object.__setattr__(self, "latitude_deg", latitude)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "samples", int(self.samples))

    @classmethod
    def great_circle(
        cls,
        frame: SphericalFrame,
        start_deg: float,
        end_deg: float,
        *,
        radius: float = 1.0,
        samples: int = 101,
    ) -> SphericalArc:
        """Construct an arc on the frame's equatorial great circle."""
        return cls(
            frame=frame,
            start_deg=start_deg,
            end_deg=end_deg,
            latitude_deg=0.0,
            radius=radius,
            samples=samples,
        )

    @classmethod
    def small_circle(
        cls,
        frame: SphericalFrame,
        latitude_deg: float,
        start_deg: float,
        end_deg: float,
        *,
        radius: float = 1.0,
        samples: int = 101,
    ) -> SphericalArc:
        """Construct a non-equatorial small-circle arc."""
        latitude = float(latitude_deg)
        if latitude == 0.0:
            raise ValueError(
                "Small-circle latitude must be non-zero; use great_circle()."
            )
        return cls(
            frame=frame,
            start_deg=start_deg,
            end_deg=end_deg,
            latitude_deg=latitude,
            radius=radius,
            samples=samples,
        )

    @property
    def is_great_circle(self) -> bool:
        return self.latitude_deg == 0.0

    @property
    def span_deg(self) -> float:
        return self.end_deg - self.start_deg

    def points(self) -> np.ndarray:
        parameters = np.linspace(
            self.start_deg,
            self.end_deg,
            self.samples,
        )
        latitudes = np.full_like(parameters, self.latitude_deg)
        return self.frame.point(
            parameters,
            latitudes,
            radius=self.radius,
        )

    @property
    def start_point(self) -> np.ndarray:
        return self.points()[0]

    @property
    def end_point(self) -> np.ndarray:
        return self.points()[-1]

    def to_curve(
        self,
        *,
        style: CurveStyle | None = None,
        visible: bool = True,
    ) -> SampledCurve:
        """Return this geometry as a renderer-neutral sampled curve."""
        return SampledCurve(
            points=self.points(),
            style=style or CurveStyle(),
            visible=visible,
        )
