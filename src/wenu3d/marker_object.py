from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .markers import Marker
from .scene_object import SceneObject


@dataclass
class MarkerObject(SceneObject):
    """Lifecycle-managed PyVista representation of one finite marker."""

    marker: Marker | None = None
    _mesh: pv.PolyData | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.marker, Marker):
            raise TypeError("MarkerObject marker must be a Marker.")
        self.visible = self.visible and self.marker.visible
        self.opacity = self.marker.style.opacity

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    def build(self, plotter: pv.Plotter) -> None:
        if self.marker is None:
            raise TypeError("MarkerObject marker must be a Marker.")

        self._prepare_build(plotter)
        if self.marker.style.shape == "sphere":
            mesh = pv.Sphere(
                radius=self.marker.style.radius,
                center=self.marker.position,
                theta_resolution=48,
                phi_resolution=24,
            )
        else:
            mesh = self._star_mesh(
                self.marker.position,
                self.marker.style.radius,
            )
        self._mesh = mesh

        actor = plotter.add_mesh(
            mesh,
            color=self.marker.style.color,
            opacity=self.opacity,
            smooth_shading=True,
            name=self.name,
            render=False,
        )
        self.add_actor(actor)

    def detach(self, *, render: bool = True) -> None:
        super().detach(render=render)
        self._mesh = None

    @staticmethod
    def _star_mesh(
        position: tuple[float, float, float],
        radius: float,
    ) -> pv.PolyData:
        """Return a symmetric eight-point stellated marker."""
        center = np.asarray(position, dtype=float)
        inner_radius = 0.45 * radius
        points = [
            center + (inner_radius, 0.0, 0.0),
            center + (-inner_radius, 0.0, 0.0),
            center + (0.0, inner_radius, 0.0),
            center + (0.0, -inner_radius, 0.0),
            center + (0.0, 0.0, inner_radius),
            center + (0.0, 0.0, -inner_radius),
        ]

        faces: list[int] = []
        for x_sign in (-1, 1):
            for y_sign in (-1, 1):
                for z_sign in (-1, 1):
                    x_index = 0 if x_sign > 0 else 1
                    y_index = 2 if y_sign > 0 else 3
                    z_index = 4 if z_sign > 0 else 5
                    direction = np.array(
                        [x_sign, y_sign, z_sign],
                        dtype=float,
                    ) / np.sqrt(3.0)
                    point_index = len(points)
                    points.append(center + radius * direction)
                    faces.extend(
                        (
                            3,
                            x_index,
                            y_index,
                            point_index,
                            3,
                            y_index,
                            z_index,
                            point_index,
                            3,
                            z_index,
                            x_index,
                            point_index,
                        )
                    )

        mesh = pv.PolyData(
            np.asarray(points, dtype=float),
            np.asarray(faces, dtype=np.int64),
        )
        mesh.compute_normals(
            point_normals=True,
            cell_normals=False,
            auto_orient_normals=True,
            inplace=True,
        )
        return mesh
