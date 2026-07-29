from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Sequence

import numpy as np
import pyvista as pv

from .curves import Meridian, Parallel
from .frames import SphericalFrame
from .rendering import add_tube
from .scene_object import SceneObject
from .layer import Layer


@dataclass
class GridStyle:
    color: str = "#666666"
    major_radius: float = 0.0060
    minor_radius: float = 0.0025
    major_opacity: float = 0.82
    minor_opacity: float = 0.33
    label_format: str = "{value:g} deg"
    label_offset: float = 0.025


@dataclass
class GridCurveObject(SceneObject):
    frame: SphericalFrame | None = None
    value_deg: float = 0.0
    radius: float = 1.0
    tube_radius: float = 0.003
    color: str = "#666666"
    kind: str = "meridian"

    def build(self, plotter: pv.Plotter) -> None:
        if self.frame is None:
            raise ValueError("GridCurveObject requires a frame.")

        if self.kind == "meridian":
            points = Meridian(self.frame, self.value_deg).points(self.radius)
        elif self.kind == "parallel":
            points = Parallel(self.frame, self.value_deg).points(self.radius)
        else:
            raise ValueError(f"Unsupported grid curve kind: {self.kind}")

        actor = add_tube(
            plotter,
            points,
            color=self.color,
            radius=self.tube_radius,
            opacity=self.opacity,
            name=self.name,
        )
        self.add_actor(actor)


@dataclass
class GridLayer(Layer):
    """
    Grid layer whose meridians and parallels are individually addressable.

    Example:
        grid.meridians[90].set_visible(False)
        grid.parallels[-30].set_visible(False)
    """

    frame: SphericalFrame | None = None
    meridians_deg: Sequence[float] = field(default_factory=tuple)
    parallels_deg: Sequence[float] = field(default_factory=tuple)
    major_meridians_deg: Sequence[float] = field(default_factory=tuple)
    major_parallels_deg: Sequence[float] = field(default_factory=tuple)
    style: GridStyle = field(default_factory=GridStyle)
    radius: float = 1.0

    meridians: dict[float, GridCurveObject] = field(
        default_factory=dict,
        init=False,
    )
    parallels: dict[float, GridCurveObject] = field(
        default_factory=dict,
        init=False,
    )

    def __post_init__(self) -> None:
        if self.frame is None:
            raise ValueError("GridLayer requires a spherical frame.")
        self._create_curve_objects()

    @staticmethod
    def _contains(value: float, values: Sequence[float]) -> bool:
        return any(np.isclose(value, item, atol=1e-9) for item in values)

    def _create_curve_objects(self) -> None:
        self.objects.clear()
        self.meridians.clear()
        self.parallels.clear()

        for value in self.meridians_deg:
            value = float(value)
            major = self._contains(value, self.major_meridians_deg)
            obj = GridCurveObject(
                name=f"{self.name}.meridian.{value:g}",
                frame=self.frame,
                value_deg=value,
                radius=self.radius,
                tube_radius=(
                    self.style.major_radius if major
                    else self.style.minor_radius
                ),
                color=self.style.color,
                opacity=(
                    self.style.major_opacity if major
                    else self.style.minor_opacity
                ),
                kind="meridian",
            )
            self.meridians[value] = obj
            self.add(obj)

        for value in self.parallels_deg:
            value = float(value)
            major = self._contains(value, self.major_parallels_deg)
            obj = GridCurveObject(
                name=f"{self.name}.parallel.{value:g}",
                frame=self.frame,
                value_deg=value,
                radius=self.radius,
                tube_radius=(
                    self.style.major_radius if major
                    else self.style.minor_radius
                ),
                color=self.style.color,
                opacity=(
                    self.style.major_opacity if major
                    else self.style.minor_opacity
                ),
                kind="parallel",
            )
            self.parallels[value] = obj
            self.add(obj)

    def set_meridian_visible(self, value_deg: float, visible: bool) -> None:
        self.meridians[float(value_deg)].set_visible(visible, render=False)

    def set_parallel_visible(self, value_deg: float, visible: bool) -> None:
        self.parallels[float(value_deg)].set_visible(visible, render=False)
