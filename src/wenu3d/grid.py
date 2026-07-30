from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping, Sequence

import numpy as np
import pyvista as pv

from .annotations import Annotation, AnnotationLayer, AnnotationStyle
from .curves import Meridian, Parallel
from .frames import SphericalFrame
from .rendering import add_tube
from .scene_object import SceneObject
from .layer import Layer


@dataclass
class GridStyle:
    color: str = "#666666"
    major_radius: float = 0.0036
    minor_radius: float = 0.0018
    major_opacity: float = 0.78
    minor_opacity: float = 0.42
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

        self._prepare_build(plotter)
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

    def set_meridian_visible(
        self,
        value_deg: float,
        visible: bool,
    ) -> None:
        self.meridians[float(value_deg)].set_visible(
            visible,
            render=False,
        )

    def set_parallel_visible(
        self,
        value_deg: float,
        visible: bool,
    ) -> None:
        self.parallels[float(value_deg)].set_visible(
            visible,
            render=False,
        )

    def set_all_meridians_visible(self, visible: bool) -> None:
        for meridian in self.meridians.values():
            meridian.set_visible(visible, render=False)

    def set_all_parallels_visible(self, visible: bool) -> None:
        for parallel in self.parallels.values():
            parallel.set_visible(visible, render=False)

    def make_label_layer(
        self,
        *,
        name: str | None = None,
        meridian_anchors: Mapping[float, float] | None = None,
        parallel_anchors: Mapping[float, float] | None = None,
        annotation_style: AnnotationStyle | None = None,
    ) -> AnnotationLayer:
        """
        Create independently selectable labels for specified grid curves.

        ``meridian_anchors`` maps meridian longitude to the latitude at which
        its label is anchored. ``parallel_anchors`` maps parallel latitude to
        its anchor longitude.
        """
        if self.frame is None:
            raise ValueError("GridLayer requires a spherical frame.")

        label_layer = AnnotationLayer(
            name=name or f"{self.name}.labels",
        )
        text_style = annotation_style or AnnotationStyle(
            color=self.style.color,
        )

        for raw_value, raw_latitude in (meridian_anchors or {}).items():
            value = float(raw_value)
            latitude = float(raw_latitude)
            curve = self.meridians[value]
            direction = self.frame.point(value, latitude, radius=1.0)
            anchor = self.frame.point(value, latitude, radius=self.radius)
            label_layer.add_annotation(
                f"{label_layer.name}.meridian.{value:g}",
                Annotation(
                    text=self.style.label_format.format(value=value),
                    anchor=anchor,
                    offset=self.style.label_offset * direction,
                    style=text_style,
                    associated_with=curve.name,
                ),
            )

        for raw_value, raw_longitude in (parallel_anchors or {}).items():
            value = float(raw_value)
            longitude = float(raw_longitude)
            curve = self.parallels[value]
            direction = self.frame.point(longitude, value, radius=1.0)
            anchor = self.frame.point(longitude, value, radius=self.radius)
            label_layer.add_annotation(
                f"{label_layer.name}.parallel.{value:g}",
                Annotation(
                    text=self.style.label_format.format(value=value),
                    anchor=anchor,
                    offset=self.style.label_offset * direction,
                    style=text_style,
                    associated_with=curve.name,
                ),
            )

        return label_layer
