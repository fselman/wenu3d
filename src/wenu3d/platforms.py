from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from .annotations import Annotation, AnnotationObject, AnnotationStyle
from .layer import Layer
from .segment_object import SegmentObject
from .segments import LineSegment, SegmentStyle
from .surface_object import SurfaceObject
from .vector_object import VectorObject


class PlatformDecoration(Layer):
    """Replaceable decoration attached to one finite local platform."""


class CardinalDirectionsDecoration(PlatformDecoration):
    """East, West, North, and South platform vectors."""

    required_directions = ("east", "west", "north", "south")

    def __init__(
        self,
        *,
        name: str,
        vectors: Mapping[str, VectorObject],
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if tuple(vectors) != self.required_directions:
            raise ValueError(
                "Cardinal vectors must be ordered East, West, North, South."
            )
        values = tuple(vectors.values())
        if not all(isinstance(obj, VectorObject) for obj in values):
            raise TypeError("Cardinal vectors must be VectorObjects.")
        super().__init__(name=name, visible=visible, opacity=opacity)
        self._vectors = dict(vectors)
        self.extend(values)

    @property
    def vectors(self) -> tuple[VectorObject, ...]:
        return tuple(self._vectors.values())

    def get_direction(self, direction: str) -> VectorObject:
        return self._vectors[str(direction).strip().lower()]


class CardinalLinesDecoration(PlatformDecoration):
    """N/E/S/W line segments and inscriptions for a local platform."""

    labels = ("E", "W", "N", "S")

    def __init__(
        self,
        *,
        name: str,
        center,
        east,
        north,
        length: float,
        line_style: SegmentStyle | None = None,
        text_style: AnnotationStyle | None = None,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        center = np.asarray(center, dtype=float)
        east = np.asarray(east, dtype=float)
        north = np.asarray(north, dtype=float)
        if center.shape != (3,) or not np.all(np.isfinite(center)):
            raise ValueError("center must contain three finite components.")
        for label, vector in (("east", east), ("north", north)):
            if vector.shape != (3,) or not np.all(np.isfinite(vector)):
                raise ValueError(f"{label} must contain three finite components.")
        east_norm = np.linalg.norm(east)
        if not np.isfinite(east_norm) or east_norm == 0.0:
            raise ValueError("east must be non-zero.")
        east /= east_norm
        north -= np.dot(north, east) * east
        north_norm = np.linalg.norm(north)
        if not np.isfinite(north_norm) or north_norm == 0.0:
            raise ValueError("north must not be parallel to east.")
        north /= north_norm
        length = float(length)
        if not np.isfinite(length) or length <= 0.0:
            raise ValueError("length must be finite and greater than zero.")
        line_style = line_style or SegmentStyle()
        text_style = text_style or AnnotationStyle()
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.lines = {}
        self.inscriptions = {}
        for label, direction in zip(
            self.labels,
            (east, -east, north, -north),
        ):
            end = center + length * direction
            line = SegmentObject(
                name=f"{name}.{label.lower()}.line",
                segment=LineSegment(center, end, style=line_style),
            )
            inscription = AnnotationObject(
                name=f"{name}.{label.lower()}.label",
                annotation=Annotation(
                    text=label,
                    anchor=end,
                    offset=0.08 * length * direction,
                    style=text_style,
                    associated_with=line.name,
                ),
            )
            self.lines[label] = line
            self.inscriptions[label] = inscription
            self.add(line)
            self.add(inscription)


class LocalPlatform(Layer):
    """A finite platform surface with one interchangeable decoration."""

    def __init__(
        self,
        *,
        name: str,
        surface: SurfaceObject,
        decoration: PlatformDecoration | None = None,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(surface, SurfaceObject):
            raise TypeError("surface must be a SurfaceObject.")
        if decoration is not None and not isinstance(
            decoration,
            PlatformDecoration,
        ):
            raise TypeError("decoration must be a PlatformDecoration.")
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.surface = surface
        self.decoration = decoration
        self.add(surface)
        if decoration is not None:
            self.add(decoration)

    def set_decoration(
        self,
        decoration: PlatformDecoration | None,
        *,
        render: bool = True,
    ) -> None:
        if decoration is not None and not isinstance(
            decoration,
            PlatformDecoration,
        ):
            raise TypeError("decoration must be a PlatformDecoration.")
        plotter = self.attached_plotter
        previous = self.decoration
        if previous is not None:
            previous.detach(render=False)
            self.objects.remove(previous)
        self.decoration = decoration
        if decoration is not None:
            self.objects.append(decoration)
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()
