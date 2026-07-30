from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

import numpy as np
import pyvista as pv


from .annotations import AnnotationLayer
from .controls import (
    AnnotationControlPanel,
    ControlManager,
    GlobalControlPanel,
    GridControlPanel,
)
from .earth import realistic_earth
from .frames import horizontal_frame, equatorial_frame
from .grid import GridLayer, GridStyle
from .layer import Layer
from .local_group import ActorScaleGroup
from .observer import tangent_plane, add_observer
from .rendering import add_arrow, add_tube
from .scene_object import SceneObject
from .style import SceneStyle


@dataclass
class SceneGraph:
    layers: dict[str, Layer] = field(default_factory=dict)

    def __iter__(self) -> Iterator[Layer]:
        return iter(self.layers.values())

    def __len__(self) -> int:
        return len(self.layers)

    def add(self, layer: Layer) -> Layer:
        if layer.name in self.layers:
            raise ValueError(f"Layer already exists: {layer.name}")
        self.layers[layer.name] = layer
        return layer

    def get(self, name: str) -> Layer:
        return self.layers[name]

    def remove(self, name: str, *, render: bool = True) -> Layer:
        layer = self.layers.pop(name)
        layer.detach(render=render)
        return layer

    def clear(self, *, render: bool = True) -> None:
        attached_plotters: dict[int, pv.Plotter] = {}
        for layer in self.layers.values():
            plotter = layer.attached_plotter
            if plotter is not None:
                attached_plotters[id(plotter)] = plotter

        layers = tuple(self.layers.values())
        self.layers.clear()

        for layer in layers:
            layer.detach(render=False)

        if render:
            for plotter in attached_plotters.values():
                plotter.render()


class CelestialScene:
    """
    The scene owns generic layers. Grid-specific interaction lives in GridLayer
    and GridControlPanel, not in CelestialScene.
    """

    def __init__(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        location_name: str,
        earth_radius: float = 0.25,
        sphere_radius: float = 1.0,
        style: SceneStyle | None = None,
        window_size=(1600, 1150),
    ) -> None:
        self.latitude_deg = latitude_deg
        self.longitude_deg = longitude_deg
        self.location_name = location_name
        self.earth_radius = earth_radius
        self.sphere_radius = sphere_radius
        self.style = style or SceneStyle()

        self.horizontal = horizontal_frame()
        self.equatorial = equatorial_frame(latitude_deg)

        self.plotter = pv.Plotter(window_size=window_size)
        self.plotter.set_background(self.style.background)

        self.graph = SceneGraph()
        self.local_group = ActorScaleGroup()
        self._local_scale = 1.0
        self.controls = ControlManager(
            plotter=self.plotter,
            window_size=window_size,
        )

        self._build_base_scene()

    def add(self, layer: Layer) -> Layer:
        self.graph.add(layer)
        layer.build(self.plotter)
        return layer

    def _build_base_scene(self) -> None:
        self._add_celestial_shell()
        self._add_earth_and_observer()
        self._add_axis()
        self.plotter.enable_lightkit()
        self._set_camera()
        self._refresh_celestial_sphere()
        self._install_sphere_camera_observer()

    def _add_celestial_shell(self) -> None:
        """
        Create a transparent glass sphere using per-vertex RGBA values.

        Opacity and colour depend on the angle between the surface normal and
        the camera. This gives genuine limb darkening rather than drawing a
        separate circular outline.
        """
        shell = pv.Sphere(
            radius=self.sphere_radius,
            theta_resolution=360,
            phi_resolution=180,
        )

        shell.compute_normals(
            point_normals=True,
            cell_normals=False,
            auto_orient_normals=True,
            inplace=True,
        )

        self._sphere_mesh = shell
        self._sphere_presence = 1.0
        self._sphere_rgba_name = "celestial_sphere_rgba"

        # Temporary values. They are replaced after the camera is configured.
        shell.point_data[self._sphere_rgba_name] = np.zeros(
            (shell.n_points, 4),
            dtype=np.uint8,
        )

        self.sphere_actor = self.plotter.add_mesh(
            shell,
            scalars=self._sphere_rgba_name,
            rgba=True,
            smooth_shading=True,
            lighting=False,
            culling="back",
            interpolate_before_map=True,
        )

    def _install_sphere_camera_observer(self) -> None:
        """
        Recalculate the Fresnel material after camera interaction.

        The sphere therefore keeps the same realistic appearance when the user
        rotates or changes the viewpoint.
        """
        def refresh_after_camera_motion(*_args) -> None:
            self._refresh_celestial_sphere()
            self.plotter.render()

        self._sphere_camera_callback = refresh_after_camera_motion

        try:
            self._sphere_camera_observer_id = (
                self.plotter.iren.add_observer(
                    "EndInteractionEvent",
                    self._sphere_camera_callback,
                )
            )
        except (AttributeError, RuntimeError):
            self._sphere_camera_observer_id = None

    @staticmethod
    def _normalized_rows(vectors: np.ndarray) -> np.ndarray:
        lengths = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )
        lengths = np.where(lengths == 0.0, 1.0, lengths)
        return vectors / lengths

    def _refresh_celestial_sphere(self) -> None:
        """
        Update limb darkening and specular reflections for the current camera.
        """
        mesh = self._sphere_mesh

        points = np.asarray(
            mesh.points,
            dtype=float,
        )
        normals = np.asarray(
            mesh.point_data["Normals"],
            dtype=float,
        )

        normals = self._normalized_rows(normals)

        camera_position = np.asarray(
            self.plotter.camera.position,
            dtype=float,
        )

        view_vectors = self._normalized_rows(
            camera_position[None, :] - points
        )

        normal_dot_view = np.clip(
            np.einsum(
                "ij,ij->i",
                normals,
                view_vectors,
            ),
            0.0,
            1.0,
        )

        # Fresnel-like limb factor:
        # 0 at the apparent centre, approaching 1 at the projected border.
        limb = np.power(
            1.0 - normal_dot_view,
            self.style.sphere_limb_power,
        )

        center_rgb = np.asarray(
            pv.Color(
                self.style.sphere_center_color
            ).float_rgb,
            dtype=float,
        )

        rim_rgb = np.asarray(
            pv.Color(
                self.style.sphere_rim_color
            ).float_rgb,
            dtype=float,
        )

        highlight_rgb = np.asarray(
            pv.Color(
                self.style.sphere_highlight_color
            ).float_rgb,
            dtype=float,
        )

        # Blue-grey centre transitioning gradually to a darker blue limb.
        rgb = (
            center_rgb[None, :]
            * (1.0 - limb[:, None])
            + rim_rgb[None, :]
            * limb[:, None]
        )

        # Fixed world-space key light.
        key_position = np.array(
            [2.7, -2.4, 3.1],
            dtype=float,
        )

        key_vectors = self._normalized_rows(
            key_position[None, :] - points
        )

        key_half_vectors = self._normalized_rows(
            key_vectors + view_vectors
        )

        key_specular = np.power(
            np.clip(
                np.einsum(
                    "ij,ij->i",
                    normals,
                    key_half_vectors,
                ),
                0.0,
                1.0,
            ),
            self.style.sphere_specular_power,
        )

        # Broader secondary reflection on the opposite side.
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
            (
                self.style.sphere_specular_strength
                * key_specular
                + self.style.sphere_secondary_specular_strength
                * secondary_specular
            ),
            0.0,
            1.0,
        )

        rgb = (
            rgb * (1.0 - 0.90 * total_highlight[:, None])
            + highlight_rgb[None, :]
            * (0.90 * total_highlight[:, None])
        )

        rgb = np.clip(
            rgb,
            0.0,
            1.0,
        )

        # Almost transparent at the centre, substantially darker at the limb.
        alpha = (
            self.style.sphere_center_opacity
            + (
                self.style.sphere_rim_opacity
                - self.style.sphere_center_opacity
            )
            * limb
        )

        # Highlights need some opacity even away from the limb.
        alpha += (
            0.24 * key_specular
            + 0.12 * secondary_specular
        )

        alpha *= self._sphere_presence

        alpha = np.clip(
            alpha,
            0.0,
            0.82,
        )

        rgba = np.empty(
            (mesh.n_points, 4),
            dtype=np.uint8,
        )

        rgba[:, :3] = np.rint(
            255.0 * rgb
        ).astype(np.uint8)

        rgba[:, 3] = np.rint(
            255.0 * alpha
        ).astype(np.uint8)

        mesh.point_data[self._sphere_rgba_name] = rgba
        mesh.Modified()

    def _add_earth_and_observer(self) -> None:
        zenith = self.horizontal.pole
        east = self.horizontal.east
        north = self.horizontal.zero

        earth, texture = realistic_earth(
            self.earth_radius,
            rotation_axis=self.equatorial.pole,
            observer_zenith=zenith,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
        )
        self.local_group.add(
            self.plotter.add_mesh(
                earth,
                texture=texture,
                smooth_shading=True,
                ambient=0.28,
                diffuse=0.78,
                specular=0.10,
                specular_power=12,
            )
        )

        plane_center = self.earth_radius * zenith + 0.012 * zenith
        plane = tangent_plane(
            plane_center,
            east,
            north,
            width=1.85 * self.earth_radius,
            depth=1.20 * self.earth_radius,
        )
        self.local_group.add(
            self.plotter.add_mesh(
                plane,
                color=self.style.plane_color,
                opacity=0.52,
                show_edges=True,
                edge_color="#777777",
            )
        )

        for direction in (east, -east, north, -north):
            self.local_group.add(
                add_arrow(
                    self.plotter,
                    plane_center,
                    direction,
                    scale=0.28 * self.earth_radius,
                    color="#59645d",
                )
            )

        self.local_group.extend(
            add_observer(
                self.plotter,
                base=plane_center - 0.05 * self.earth_radius * north,
                zenith=zenith,
                east=east,
                height=0.92 * self.earth_radius,
            )
        )

    def _add_axis(self) -> None:
        ncp = self.equatorial.pole
        add_tube(
            self.plotter,
            np.vstack([
                -1.10 * self.sphere_radius * ncp,
                1.10 * self.sphere_radius * ncp,
            ]),
            color="#333333",
            radius=0.006,
            opacity=0.85,
        )

    def make_horizontal_grid(
        self,
        *,
        name: str = "horizontal",
        meridians_deg=tuple(np.arange(0, 360, 30)),
        parallels_deg=(-60, -30, 0, 30, 60),
    ) -> GridLayer:
        return GridLayer(
            name=name,
            frame=self.horizontal,
            meridians_deg=meridians_deg,
            parallels_deg=parallels_deg,
            major_meridians_deg=(0, 90, 180, 270),
            major_parallels_deg=(0,),
            radius=0.992 * self.sphere_radius,
            style=GridStyle(color=self.style.horizontal_grid_color),
        )

    def make_equatorial_grid(
        self,
        *,
        name: str = "equatorial",
        meridians_deg=tuple(np.arange(0, 360, 30)),
        parallels_deg=(-60, -30, 0, 30, 60),
    ) -> GridLayer:
        return GridLayer(
            name=name,
            frame=self.equatorial,
            meridians_deg=meridians_deg,
            parallels_deg=parallels_deg,
            major_meridians_deg=(0, 90, 180, 270),
            major_parallels_deg=(0,),
            radius=0.988 * self.sphere_radius,
            style=GridStyle(color=self.style.equatorial_grid_color),
        )

    def add_grid_controls(
        self,
        grid: GridLayer,
    ) -> GridControlPanel:
        panel = GridControlPanel(
            plotter=self.plotter,
            grid=grid,
        )
        return self.controls.register_panel(panel)

    def add_annotation_controls(
        self,
        *layers: AnnotationLayer,
    ) -> AnnotationControlPanel:
        panel = AnnotationControlPanel(
            plotter=self.plotter,
            layers=layers,
            color=self.style.horizontal_grid_color,
        )
        return self.controls.register_panel(panel)

    def add_global_controls(self) -> GlobalControlPanel:
        panel = GlobalControlPanel(
            plotter=self.plotter,
            set_sphere_presence=self._set_sphere_presence,
            set_local_scale=self._set_local_scale,
            get_sphere_presence=lambda: self._sphere_presence,
            get_local_scale=lambda: self._local_scale,
            reset_camera=self.reset_camera,
        )
        return self.controls.register_panel(panel)

    def _set_local_scale(self, value: float) -> None:
        self._local_scale = float(value)
        self.local_group.set_scale(self._local_scale)
        self.plotter.render()

    def _set_sphere_presence(self, value: float) -> None:
        self._sphere_presence = float(value)
        self._refresh_celestial_sphere()
        self.plotter.render()

    def _set_camera(self) -> None:
        self.plotter.camera_position = [
            (2.35, -2.70, 1.55),
            (0.0, 0.0, 0.02),
            (0.0, 0.0, 1.0),
        ]
        self.plotter.camera.zoom(1.12)

    def reset_camera(self) -> None:
        """Restore the canonical illustration camera and refresh the shell."""
        self._set_camera()
        self._refresh_celestial_sphere()
        self.plotter.render()

    def show(self, *, screenshot: str | None = None) -> None:
        self.plotter.add_text(
            f"Celestial grids — {self.location_name}",
            position="upper_left",
            font_size=18,
            color=self.style.text_color,
        )
        self.plotter.show(
            screenshot=screenshot,
            auto_close=False,
        )
