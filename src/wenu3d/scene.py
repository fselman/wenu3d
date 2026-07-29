from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .controls import GridControlPanel
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

    def add(self, layer: Layer) -> Layer:
        if layer.name in self.layers:
            raise ValueError(f"Layer already exists: {layer.name}")
        self.layers[layer.name] = layer
        return layer

    def get(self, name: str) -> Layer:
        return self.layers[name]


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
        self.grid_panels: list[GridControlPanel] = []

        self._build_base_scene()

    def add(self, layer: Layer) -> Layer:
        self.graph.add(layer)
        layer.build(self.plotter)
        return layer

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
            radius=1.018 * self.sphere_radius,
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
            radius=1.022 * self.sphere_radius,
            style=GridStyle(color=self.style.equatorial_grid_color),
        )

    def add_grid_controls(
        self,
        grid: GridLayer,
        *,
        origin_x: int,
        origin_y: int = 650,
    ) -> None:
        panel = GridControlPanel(
            plotter=self.plotter,
            grid=grid,
            origin_x=origin_x,
            origin_y=origin_y,
        )
        panel.add()
        self.grid_panels.append(panel)

    def add_global_controls(self) -> None:
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
            title="Celestial sphere",
            pointa=(0.05, 0.05),
            pointb=(0.43, 0.05),
            style="modern",
            fmt="%.2f x",
        )
        self.plotter.add_slider_widget(
            set_local_scale,
            rng=(0.05, 2.00),
            value=1.0,
            title="Earth / plane / observer",
            pointa=(0.57, 0.05),
            pointb=(0.95, 0.05),
            style="modern",
            fmt="%.2f x",
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
            f"Celestial grids — {self.location_name}",
            position="upper_left",
            font_size=18,
            color=self.style.text_color,
        )
        self.plotter.show(
            screenshot=screenshot,
            auto_close=False,
        )
