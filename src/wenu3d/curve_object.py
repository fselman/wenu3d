from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .curves import SampledCurve
from .scene_object import SceneObject


@dataclass
class CurveObject(SceneObject):
    """Lifecycle-managed PyVista representation of one sampled curve."""

    curve: SampledCurve | None = None
    _mesh: pv.PolyData | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _arrow_meshes: list[pv.PolyData] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.curve, SampledCurve):
            raise TypeError("CurveObject curve must be a SampledCurve.")
        self.visible = self.visible and self.curve.visible
        self.opacity = self.curve.style.opacity

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    @property
    def arrow_meshes(self) -> tuple[pv.PolyData, ...]:
        return tuple(self._arrow_meshes)

    def build(self, plotter: pv.Plotter) -> None:
        if not isinstance(self.curve, SampledCurve):
            raise TypeError("CurveObject curve must be a SampledCurve.")

        self._prepare_build(plotter)
        points = self.curve.as_array()
        mesh = pv.PolyData()
        mesh.points = points
        mesh.lines = np.concatenate(
            (
                np.array([len(points)], dtype=np.int64),
                np.arange(len(points), dtype=np.int64),
            )
        )
        self._mesh = mesh

        line_actor = plotter.add_mesh(
            mesh,
            color=self.curve.style.color,
            opacity=self.opacity,
            line_width=self.curve.style.width,
            name=self.name,
            render=False,
        )
        self.add_actor(line_actor)

        placement = self.curve.style.arrowheads
        if placement in ("start", "both"):
            self._add_arrowhead(
                plotter,
                endpoint=points[0],
                adjacent=points[1],
                suffix="start",
            )
        if placement in ("end", "both"):
            self._add_arrowhead(
                plotter,
                endpoint=points[-1],
                adjacent=points[-2],
                suffix="end",
            )

    def detach(self, *, render: bool = True) -> None:
        super().detach(render=render)
        self._mesh = None
        self._arrow_meshes.clear()

    def _add_arrowhead(
        self,
        plotter: pv.Plotter,
        *,
        endpoint: np.ndarray,
        adjacent: np.ndarray,
        suffix: str,
    ) -> None:
        if self.curve is None:
            raise TypeError("CurveObject curve must be a SampledCurve.")

        direction = endpoint - adjacent
        direction /= np.linalg.norm(direction)
        size = self.curve.style.arrow_size
        center = endpoint - 0.5 * size * direction
        mesh = pv.Cone(
            center=center,
            direction=direction,
            height=size,
            radius=0.4 * size,
            resolution=32,
        )
        self._arrow_meshes.append(mesh)

        actor = plotter.add_mesh(
            mesh,
            color=self.curve.style.color,
            opacity=self.opacity,
            name=f"{self.name}.arrow.{suffix}",
            render=False,
        )
        self.add_actor(actor)
