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
        self.actors.clear()
        for obj in self.objects:
            obj.build(plotter)
            self.actors.extend(obj.actors)
        self.set_visible(self.visible, render=False)

    def set_visible(self, visible: bool, *, render: bool = True) -> None:
        self.visible = bool(visible)
        for obj in self.objects:
            obj.set_visible(self.visible, render=False)
        for actor in self.actors:
            actor.SetVisibility(self.visible)

    def get(self, name: str) -> SceneObject:
        for obj in self.objects:
            if obj.name == name:
                return obj
        raise KeyError(name)
