from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .scene_object import SceneObject
from .style import SceneStyle


@dataclass
class CelestialShellObject(SceneObject):
    """Camera-dependent translucent celestial sphere."""

    radius: float = 1.0
    style: SceneStyle = field(default_factory=SceneStyle)
    presence: float = 1.0

    _mesh: pv.PolyData | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _rgba_name: str = field(
        default="celestial_sphere_rgba",
        init=False,
        repr=False,
    )
    _camera_callback: object | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _camera_observer_id: int | None = field(
        default=None,
        init=False,
        repr=False,
    )

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    @property
    def camera_observer_id(self) -> int | None:
        return self._camera_observer_id

    def build(self, plotter: pv.Plotter) -> None:
        self._prepare_build(plotter)

        shell = pv.Sphere(
            radius=self.radius,
            theta_resolution=360,
            phi_resolution=180,
        )
        shell.compute_normals(
            point_normals=True,
            cell_normals=False,
            auto_orient_normals=True,
            inplace=True,
        )
        shell.point_data[self._rgba_name] = np.zeros(
            (shell.n_points, 4),
            dtype=np.uint8,
        )
        self._mesh = shell

        actor = plotter.add_mesh(
            shell,
            scalars=self._rgba_name,
            rgba=True,
            smooth_shading=True,
            lighting=False,
            culling="back",
            interpolate_before_map=True,
        )
        self.add_actor(actor)
        self._install_camera_observer(plotter)

    def detach(self, *, render: bool = True) -> None:
        plotter = self._plotter
        observer_id = self._camera_observer_id
        self._camera_observer_id = None
        self._camera_callback = None

        if plotter is not None and observer_id is not None:
            try:
                plotter.iren.remove_observer(observer_id)
            except (AttributeError, RuntimeError):
                pass

        super().detach(render=render)
        self._mesh = None

    def set_presence(
        self,
        presence: float,
        *,
        render: bool = True,
    ) -> None:
        self.presence = float(presence)
        self.refresh()
        self._request_render(render)

    def refresh(self) -> None:
        """Refresh the material for the attached plotter's camera."""
        mesh = self._mesh
        plotter = self._plotter
        if mesh is None or plotter is None:
            return

        points = np.asarray(mesh.points, dtype=float)
        normals = np.asarray(
            mesh.point_data["Normals"],
            dtype=float,
        )
        normals = self._normalized_rows(normals)

        camera_position = np.asarray(
            plotter.camera.position,
            dtype=float,
        )
        view_vectors = self._normalized_rows(
            camera_position[None, :] - points
        )
        normal_dot_view = np.clip(
            np.einsum("ij,ij->i", normals, view_vectors),
            0.0,
            1.0,
        )
        limb = np.power(
            1.0 - normal_dot_view,
            self.style.sphere_limb_power,
        )

        center_rgb = np.asarray(
            pv.Color(self.style.sphere_center_color).float_rgb,
            dtype=float,
        )
        rim_rgb = np.asarray(
            pv.Color(self.style.sphere_rim_color).float_rgb,
            dtype=float,
        )
        highlight_rgb = np.asarray(
            pv.Color(self.style.sphere_highlight_color).float_rgb,
            dtype=float,
        )
        rgb = (
            center_rgb[None, :] * (1.0 - limb[:, None])
            + rim_rgb[None, :] * limb[:, None]
        )

        key_position = np.array([2.7, -2.4, 3.1], dtype=float)
        key_vectors = self._normalized_rows(
            key_position[None, :] - points
        )
        key_half_vectors = self._normalized_rows(
            key_vectors + view_vectors
        )
        key_specular = np.power(
            np.clip(
                np.einsum("ij,ij->i", normals, key_half_vectors),
                0.0,
                1.0,
            ),
            self.style.sphere_specular_power,
        )

        secondary_position = np.array(
            [-2.3, -0.6, 2.0],
            dtype=float,
        )
        secondary_vectors = self._normalized_rows(
            secondary_position[None, :] - points
        )
        secondary_half_vectors = self._normalized_rows(
            secondary_vectors + view_vectors
        )
        secondary_specular = np.power(
            np.clip(
                np.einsum(
                    "ij,ij->i",
                    normals,
                    secondary_half_vectors,
                ),
                0.0,
                1.0,
            ),
            self.style.sphere_secondary_specular_power,
        )

        total_highlight = np.clip(
            self.style.sphere_specular_strength * key_specular
            + self.style.sphere_secondary_specular_strength
            * secondary_specular,
            0.0,
            1.0,
        )
        rgb = (
            rgb * (1.0 - 0.90 * total_highlight[:, None])
            + highlight_rgb[None, :]
            * (0.90 * total_highlight[:, None])
        )
        rgb = np.clip(rgb, 0.0, 1.0)

        alpha = self.style.sphere_center_opacity + (
            self.style.sphere_rim_opacity
            - self.style.sphere_center_opacity
        ) * limb
        alpha += 0.24 * key_specular + 0.12 * secondary_specular
        alpha *= self.presence
        alpha = np.clip(alpha, 0.0, 0.82)

        rgba = np.empty((mesh.n_points, 4), dtype=np.uint8)
        rgba[:, :3] = np.rint(255.0 * rgb).astype(np.uint8)
        rgba[:, 3] = np.rint(255.0 * alpha).astype(np.uint8)
        mesh.point_data[self._rgba_name] = rgba
        mesh.Modified()

    def _install_camera_observer(self, plotter: pv.Plotter) -> None:
        def refresh_after_camera_motion(*_args) -> None:
            if self._plotter is not plotter:
                return
            self.refresh()
            plotter.render()

        self._camera_callback = refresh_after_camera_motion
        try:
            self._camera_observer_id = plotter.iren.add_observer(
                "EndInteractionEvent",
                self._camera_callback,
            )
        except (AttributeError, RuntimeError):
            self._camera_observer_id = None

    @staticmethod
    def _normalized_rows(vectors: np.ndarray) -> np.ndarray:
        lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
        lengths = np.where(lengths == 0.0, 1.0, lengths)
        return vectors / lengths
