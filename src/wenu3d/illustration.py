from __future__ import annotations

from dataclasses import dataclass

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
        obj = AnnotationObject(name=name, annotation=annotation)
        self.add(obj)
        return obj
