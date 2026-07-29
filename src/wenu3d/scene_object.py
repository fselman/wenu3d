from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyvista as pv


@dataclass
class SceneObject:
    """
    Base class for a drawable scene object.

    A SceneObject owns its PyVista actors and exposes uniform visibility and
    opacity controls. Subclasses implement build().
    """

    name: str
    visible: bool = True
    opacity: float = 1.0
    actors: list[pv.Actor] = field(default_factory=list, init=False)

    def build(self, plotter: pv.Plotter) -> None:
        raise NotImplementedError

    def add_actor(self, actor: pv.Actor) -> pv.Actor:
        self.actors.append(actor)
        self._apply_actor_state(actor)
        return actor

    def _apply_actor_state(self, actor: pv.Actor) -> None:
        actor.SetVisibility(bool(self.visible))
        prop = actor.GetProperty()
        if prop is not None:
            prop.SetOpacity(float(self.opacity))

    def set_visible(self, visible: bool, *, render: bool = True) -> None:
        self.visible = bool(visible)
        for actor in self.actors:
            actor.SetVisibility(self.visible)
        if render and self.actors:
            renderer = self.actors[0].GetMapper()
            _ = renderer  # state is applied immediately by VTK

    def set_opacity(self, opacity: float) -> None:
        self.opacity = float(opacity)
        for actor in self.actors:
            prop = actor.GetProperty()
            if prop is not None:
                prop.SetOpacity(self.opacity)
