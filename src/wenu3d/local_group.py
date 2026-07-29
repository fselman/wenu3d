from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterable
import pyvista as pv


@dataclass
class ActorScaleGroup:
    actors: list[pv.Actor] = field(default_factory=list)

    def add(self, actor: pv.Actor) -> None:
        self.actors.append(actor)

    def extend(self, actors: Iterable[pv.Actor]) -> None:
        self.actors.extend(actors)

    def set_scale(self, value: float) -> None:
        scale = (float(value),) * 3
        for actor in self.actors:
            actor.scale = scale
