from __future__ import annotations

from collections.abc import Sequence
import numpy as np
import pyvista as pv

from .earth import realistic_earth
from .frames import horizontal_frame, equatorial_frame
from .grid import SphericalGrid, GridStyle, GridRenderResult
from .labels import LabelLayer
from .local_group import ActorScaleGroup
from .observer import tangent_plane, add_observer
from .rendering import add_arrow, add_tube
from .style import SceneStyle


class CelestialScene:
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
        initial_label_size: int = 16,
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

        self.local_group = ActorScaleGroup()
        self.horizontal_grid_actors: list[pv.Actor] = []
        self.equatorial_grid_actors: list[pv.Actor] = []

        self.label_layer = LabelLayer(
            plotter=self.plotter,
            font_size=initial_label_size,
            text_color=self.style.text_color,
            name="grid_labels",
        )

        self._build_base_scene()

    def _build_base_scene(self) -> None:
        self._add_celestial_shell()
        self._add_earth_and_observer()
        self._add_axis()
        self._set_camera()

    def _add_celestial_shell(self) -> None:
        shell = pv.Sphere(
            radius=self.sphere_radius,
            theta_resolution=300,
            phi_resolution=150,
        )

        self.sphere_back_actor = self.plotter.add_mesh(
            shell,
            color=self.style.sphere_back_color,
            opacity=self.style.sphere_back_opacity,
            smooth_shading=True,
            ambient=0.70,
            diffuse=0.25,
            specular=0.08,
            specular_power=12,
            culling="front",
        )

        self.sphere_front_actor = self.plotter.add_mesh(
            shell,
            color=self.style.sphere_front_color,
            opacity=self.style.sphere_front_opacity,
            smooth_shading=True,
            ambient=0.50,
            diffuse=0.20,
            specular=self.style.sphere_specular,
            specular_power=self.style.sphere_specular_power,
            culling="back",
        )

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
        earth_actor = self.plotter.add_mesh(
            earth,
            texture=texture,
            smooth_shading=True,
            ambient=0.28,
            diffuse=0.78,
            specular=0.10,
            specular_power=12,
        )
        self.local_group.add(earth_actor)

        plane_center = self.earth_radius * zenith + 0.012 * zenith
        plane = tangent_plane(
            plane_center,
            east,
            north,
            width=1.85 * self.earth_radius,
            depth=1.20 * self.earth_radius,
        )
        plane_actor = self.plotter.add_mesh(
            plane,
            color=self.style.plane_color,
            opacity=0.52,
            show_edges=True,
            edge_color="#777777",
        )
        self.local_group.add(plane_actor)

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

    def _register_grid_result(
        self,
        result: GridRenderResult,
        *,
        target: str,
    ) -> None:
        if target == "horizontal":
            self.horizontal_grid_actors = result.actors
        elif target == "equatorial":
            self.equatorial_grid_actors = result.actors
        else:
            raise ValueError(f"Unknown grid target: {target}")

        self.label_layer.extend(result.labels)
        self.label_layer.draw()

    def add_horizontal_grid(
        self,
        *,
        meridians_deg: Sequence[float] = tuple(np.arange(0, 360, 30)),
        parallels_deg: Sequence[float] = (-60, -30, 0, 30, 60),
        labeled_meridians_deg: Sequence[float] = (0, 90, 180, 270),
        labeled_parallels_deg: Sequence[float] = (-60, -30, 0, 30, 60),
        meridian_label_latitude_deg: float = 8.0,
        parallel_label_longitude_deg: float = 15.0,
    ) -> None:
        grid = SphericalGrid(
            frame=self.horizontal,
            meridians_deg=meridians_deg,
            parallels_deg=parallels_deg,
            major_meridians_deg=(0, 90, 180, 270),
            major_parallels_deg=(0,),
            labeled_meridians_deg=labeled_meridians_deg,
            labeled_parallels_deg=labeled_parallels_deg,
            meridian_label_latitude_deg=meridian_label_latitude_deg,
            parallel_label_longitude_deg=parallel_label_longitude_deg,
            radius=1.018 * self.sphere_radius,
            style=GridStyle(
                color=self.style.horizontal_grid_color,
                label_color=self.style.horizontal_grid_color,
                label_format="{value:g} deg",
            ),
        )
        self._register_grid_result(grid.draw(self.plotter), target="horizontal")

    def add_equatorial_grid(
        self,
        *,
        meridians_deg: Sequence[float] = tuple(np.arange(0, 360, 30)),
        parallels_deg: Sequence[float] = (-60, -30, 0, 30, 60),
        labeled_meridians_deg: Sequence[float] = (0, 90, 180, 270),
        labeled_parallels_deg: Sequence[float] = (-60, -30, 0, 30, 60),
        meridian_label_latitude_deg: float = -8.0,
        parallel_label_longitude_deg: float = 195.0,
    ) -> None:
        grid = SphericalGrid(
            frame=self.equatorial,
            meridians_deg=meridians_deg,
            parallels_deg=parallels_deg,
            major_meridians_deg=(0, 90, 180, 270),
            major_parallels_deg=(0,),
            labeled_meridians_deg=labeled_meridians_deg,
            labeled_parallels_deg=labeled_parallels_deg,
            meridian_label_latitude_deg=meridian_label_latitude_deg,
            parallel_label_longitude_deg=parallel_label_longitude_deg,
            radius=1.022 * self.sphere_radius,
            style=GridStyle(
                color=self.style.equatorial_grid_color,
                label_color=self.style.equatorial_grid_color,
                label_format="{value:g} deg",
            ),
        )
        self._register_grid_result(grid.draw(self.plotter), target="equatorial")

    def set_equatorial_grid_visible(self, visible: bool) -> None:
        for actor in self.equatorial_grid_actors:
            actor.SetVisibility(bool(visible))
        self.plotter.render()

    def add_controls(self) -> None:
        def set_local_scale(value: float) -> None:
            self.local_group.set_scale(value)
            self.plotter.render()

        def set_sphere_presence(value: float) -> None:
            factor = float(value)
            self.sphere_back_actor.GetProperty().SetOpacity(
                min(0.70, self.style.sphere_back_opacity * factor)
            )
            self.sphere_front_actor.GetProperty().SetOpacity(
                min(0.30, self.style.sphere_front_opacity * factor)
            )
            self.plotter.render()

        self.plotter.add_slider_widget(
            set_sphere_presence,
            rng=(0.20, 3.00),
            value=1.0,
            title="Presencia de la esfera celeste",
            pointa=(0.04, 0.06),
            pointb=(0.31, 0.06),
            style="modern",
            fmt="%.2f×",
        )

        self.plotter.add_slider_widget(
            set_local_scale,
            rng=(0.05, 2.00),
            value=1.0,
            title="Escala Tierra / plano / observador",
            pointa=(0.37, 0.06),
            pointb=(0.64, 0.06),
            style="modern",
            fmt="%.2f×",
        )

        self.plotter.add_slider_widget(
            self.label_layer.set_font_size,
            rng=(8, 32),
            value=self.label_layer.font_size,
            title="Tamaño de labels",
            pointa=(0.70, 0.06),
            pointb=(0.96, 0.06),
            style="modern",
            fmt="%.0f",
        )

        if self.equatorial_grid_actors:
            self.plotter.add_checkbox_button_widget(
                self.set_equatorial_grid_visible,
                value=True,
                position=(20, 95),
                size=28,
                border_size=2,
                color_on=self.style.equatorial_grid_color,
                color_off="#d8d8d8",
                background_color=self.style.background,
            )
            self.plotter.add_text(
                "Grid ecuatorial",
                position=(58, 98),
                font_size=11,
                color=self.style.text_color,
            )

    def _set_camera(self) -> None:
        self.plotter.enable_lightkit()
        self.plotter.camera_position = [
            (2.35, -2.70, 1.55),
            (0.0, 0.0, 0.02),
            (0.0, 0.0, 1.0),
        ]
        self.plotter.camera.zoom(1.12)

    def show(self, *, screenshot: str | None = None) -> None:
        self.plotter.add_text(
            f"Grid horizontal y grid ecuatorial — {self.location_name}",
            position="upper_left",
            font_size=18,
            color=self.style.text_color,
        )
        self.plotter.show(
            screenshot=screenshot,
            auto_close=False,
        )
