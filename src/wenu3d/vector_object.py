from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from .rendering import add_arrow
from .scene_object import SceneObject
from .vectors import VectorArrow


@dataclass
class VectorObject(SceneObject):
    vector: VectorArrow | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.vector, VectorArrow):
            raise TypeError("VectorObject vector must be a VectorArrow.")
        self.visible = self.visible and self.vector.visible
        self.opacity = self.vector.style.opacity

    def build(self, plotter: pv.Plotter) -> None:
        if not isinstance(self.vector, VectorArrow):
            raise TypeError("VectorObject vector must be a VectorArrow.")
        self._prepare_build(plotter)
        self.add_actor(
            add_arrow(
                plotter,
                np.asarray(self.vector.start),
                np.asarray(self.vector.direction),
                scale=self.vector.scale,
                color=self.vector.style.color,
            )
        )
