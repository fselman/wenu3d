from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Sequence
import numpy as np
import pyvista as pv

from .frames import SphericalFrame
from .curves import Meridian, Parallel
from .rendering import add_tube


@dataclass
class GridStyle:
    color: str = "#666666"
    major_radius: float = 0.0060
    minor_radius: float = 0.0025
    major_opacity: float = 0.82
    minor_opacity: float = 0.33

    label_color: str | None = None
    label_format: str = "{value:g} deg"
    label_offset: float = 0.025


@dataclass
class GridLabel:
    text: str
    position: np.ndarray


@dataclass
class GridRenderResult:
    actors: list[pv.Actor] = field(default_factory=list)
    labels: list[GridLabel] = field(default_factory=list)


@dataclass
class SphericalGrid:
    frame: SphericalFrame
    meridians_deg: Sequence[float]
    parallels_deg: Sequence[float]

    major_meridians_deg: Sequence[float] = field(default_factory=tuple)
    major_parallels_deg: Sequence[float] = field(default_factory=tuple)

    # Only these selected curves receive labels. Empty means no labels.
    labeled_meridians_deg: Sequence[float] = field(default_factory=tuple)
    labeled_parallels_deg: Sequence[float] = field(default_factory=tuple)

    # Where labels are placed along each curve.
    meridian_label_latitude_deg: float = 6.0
    parallel_label_longitude_deg: float = 12.0

    style: GridStyle = field(default_factory=GridStyle)
    radius: float = 1.0

    @staticmethod
    def _contains(value: float, values: Sequence[float]) -> bool:
        return any(np.isclose(value, item, atol=1e-9) for item in values)

    def _label_text(self, kind: str, value: float) -> str:
        return self.style.label_format.format(
            kind=kind,
            value=value,
            frame=self.frame.name,
        )

    def draw(self, plotter: pv.Plotter) -> GridRenderResult:
        result = GridRenderResult()
        label_radius = self.radius + self.style.label_offset

        for lon in self.meridians_deg:
            lon = float(lon)
            major = self._contains(lon, self.major_meridians_deg)

            result.actors.append(
                add_tube(
                    plotter,
                    Meridian(self.frame, lon).points(self.radius),
                    color=self.style.color,
                    radius=(
                        self.style.major_radius
                        if major else self.style.minor_radius
                    ),
                    opacity=(
                        self.style.major_opacity
                        if major else self.style.minor_opacity
                    ),
                )
            )

            if self._contains(lon, self.labeled_meridians_deg):
                position = self.frame.point(
                    lon,
                    self.meridian_label_latitude_deg,
                    radius=label_radius,
                )
                result.labels.append(
                    GridLabel(
                        text=self._label_text("meridian", lon),
                        position=np.asarray(position),
                    )
                )

        for lat in self.parallels_deg:
            lat = float(lat)
            major = self._contains(lat, self.major_parallels_deg)

            result.actors.append(
                add_tube(
                    plotter,
                    Parallel(self.frame, lat).points(self.radius),
                    color=self.style.color,
                    radius=(
                        self.style.major_radius
                        if major else self.style.minor_radius
                    ),
                    opacity=(
                        self.style.major_opacity
                        if major else self.style.minor_opacity
                    ),
                )
            )

            if self._contains(lat, self.labeled_parallels_deg):
                position = self.frame.point(
                    self.parallel_label_longitude_deg,
                    lat,
                    radius=label_radius,
                )
                result.labels.append(
                    GridLabel(
                        text=self._label_text("parallel", lat),
                        position=np.asarray(position),
                    )
                )

        return result
