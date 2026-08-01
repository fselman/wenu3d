from __future__ import annotations

from dataclasses import dataclass, field

import pyvista as pv

from .scene_object import SceneObject
from .segments import LineSegment, SightLine


SegmentRecord = LineSegment | SightLine


@dataclass
class SegmentObject(SceneObject):
    """Lifecycle-managed PyVista representation of one finite segment."""

    segment: SegmentRecord | None = None
    _mesh: pv.PolyData | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.segment, (LineSegment, SightLine)):
            raise TypeError(
                "SegmentObject segment must be a LineSegment or SightLine."
            )
        self.visible = self.visible and self.segment.visible
        self.opacity = self.segment.style.opacity

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    def build(self, plotter: pv.Plotter) -> None:
        if not isinstance(self.segment, (LineSegment, SightLine)):
            raise TypeError(
                "SegmentObject segment must be a LineSegment or SightLine."
            )

        self._prepare_build(plotter)
        mesh = pv.Line(self.segment.start, self.segment.end)
        if self.segment.style.tube_radius is not None:
            mesh = mesh.tube(radius=self.segment.style.tube_radius)
        self._mesh = mesh

        actor = plotter.add_mesh(
            mesh,
            color=self.segment.style.color,
            opacity=self.opacity,
            line_width=self.segment.style.width,
            name=self.name,
            render=False,
        )
        self.add_actor(actor)

    def detach(self, *, render: bool = True) -> None:
        super().detach(render=render)
        self._mesh = None
