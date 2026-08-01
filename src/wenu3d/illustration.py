from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .annotations import Annotation, AnnotationObject
from .curve_object import CurveObject
from .curves import SampledCurve
from .layer import Layer
from .marker_object import MarkerObject
from .markers import Marker
from .segment_object import SegmentObject
from .segments import LineSegment, SightLine
from .surface_object import SurfaceObject
from .surfaces import PlaneSurface


@dataclass
class IllustrationLayer(Layer):
    """Ordered group of related scientific-illustration objects."""

    font_size_scale: float = 1.0

    def __post_init__(self) -> None:
        self.font_size_scale = self._validate_font_size_scale(
            self.font_size_scale
        )

    @staticmethod
    def _validate_font_size_scale(scale: float) -> float:
        value = float(scale)
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(
                "Illustration font size scale must be finite and positive."
            )
        return value

    def add_marker(self, name: str, marker: Marker) -> MarkerObject:
        obj = MarkerObject(name=name, marker=marker)
        self.add(obj)
        return obj

    def add_segment(
        self,
        name: str,
        segment: LineSegment | SightLine,
    ) -> SegmentObject:
        obj = SegmentObject(name=name, segment=segment)
        self.add(obj)
        return obj

    def add_curve(self, name: str, curve: SampledCurve) -> CurveObject:
        obj = CurveObject(name=name, curve=curve)
        self.add(obj)
        return obj

    def add_surface(
        self,
        name: str,
        surface: PlaneSurface,
    ) -> SurfaceObject:
        obj = SurfaceObject(name=name, surface=surface)
        self.add(obj)
        return obj

    def add_annotation(
        self,
        name: str,
        annotation: Annotation,
    ) -> AnnotationObject:
        obj = AnnotationObject(
            name=name,
            annotation=annotation,
            font_size_scale=self.font_size_scale,
        )
        self.add(obj)
        return obj

    def set_font_size_scale(
        self,
        scale: float,
        *,
        render: bool = True,
    ) -> None:
        """Scale every annotation owned by this illustration."""
        value = self._validate_font_size_scale(scale)
        self.font_size_scale = value
        for obj in self.objects:
            if isinstance(obj, AnnotationObject):
                obj.font_size_scale = value
        plotter = self.attached_plotter
        if plotter is not None:
            self.build(plotter)
            self._request_render(render)
