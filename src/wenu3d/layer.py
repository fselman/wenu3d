from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable

import pyvista as pv

from .scene_object import SceneObject


@dataclass
class Layer(SceneObject):
    """A named collection of SceneObjects."""

    objects: list[SceneObject] = field(default_factory=list)

    def add(self, obj: SceneObject) -> SceneObject:
        self.objects.append(obj)
        return obj

    def extend(self, objects: Iterable[SceneObject]) -> None:
        self.objects.extend(objects)

    def build(self, plotter: pv.Plotter) -> None:
        self.detach(render=False)
        self._plotter = plotter
        for obj in self.objects:
            obj.build(plotter)
            self.actors.extend(obj.actors)
        self.set_visible(self.visible, render=False)

    def detach(self, *, render: bool = True) -> None:
        plotter = self._plotter
        for obj in self.objects:
            obj.detach(render=False)
        self.actors.clear()
        self._plotter = None
        if render and plotter is not None:
            plotter.render()

    def set_visible(self, visible: bool, *, render: bool = True) -> None:
        self.visible = bool(visible)
        for obj in self.objects:
            for actor in obj.actors:
                actor.SetVisibility(self.visible and obj.visible)
        self._request_render(render)

    def get(self, name: str) -> SceneObject:
        for obj in self.objects:
            if obj.name == name:
                return obj
        raise KeyError(name)
