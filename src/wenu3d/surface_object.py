from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .scene_object import SceneObject
from .surfaces import PlaneSurface


@dataclass
class SurfaceObject(SceneObject):
    """Lifecycle-managed PyVista representation of one finite surface."""

    surface: PlaneSurface | None = None
    _mesh: pv.PolyData | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.surface, PlaneSurface):
            raise TypeError("SurfaceObject surface must be a PlaneSurface.")
        self.visible = self.visible and self.surface.visible
        self.opacity = self.surface.style.opacity

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    def build(self, plotter: pv.Plotter) -> None:
        if not isinstance(self.surface, PlaneSurface):
            raise TypeError("SurfaceObject surface must be a PlaneSurface.")

        self._prepare_build(plotter)
        face = np.asarray((4, *self.surface.face), dtype=np.int64)
        mesh = pv.PolyData(self.surface.corners(), face)
        self._mesh = mesh

        actor = plotter.add_mesh(
            mesh,
            color=self.surface.style.color,
            opacity=self.opacity,
            show_edges=self.surface.style.show_edges,
            edge_color=self.surface.style.edge_color,
            line_width=self.surface.style.edge_width,
            name=self.name,
            render=False,
        )
        self.add_actor(actor)

    def detach(self, *, render: bool = True) -> None:
        super().detach(render=render)
        self._mesh = None
