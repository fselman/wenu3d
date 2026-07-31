from __future__ import annotations

from collections.abc import Mapping

from .layer import Layer
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
