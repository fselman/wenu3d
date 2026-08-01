from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyvista as pv


from .annotations import AnnotationLayer
from .camera import CameraState
from .controls import (
    AnnotationControlPanel,
    ControlManager,
    GlobalControlPanel,
    GridControlPanel,
)
from .earth import EarthObject
from .frames import horizontal_frame, equatorial_frame
from .grid import GridLayer, GridStyle
from .layer import Layer
from .local_cartoon import LocalCartoonLayer
from .observer import ObserverComposition, StickFigureRepresentation
from .observer_model import Observer
from .platforms import CardinalDirectionsDecoration, LocalPlatform
from .rendering import add_tube
from .scene_object import SceneObject
from .shell import CelestialShellObject
from .style import SceneStyle
from .surface_object import SurfaceObject
from .surfaces import PlaneSurface, SurfaceStyle
from .vector_object import VectorObject
from .vectors import VectorArrow, VectorStyle


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

    canonical_camera = CameraState(
        position=(2.35, -2.70, 1.55),
        focal_point=(0.0, 0.0, 0.02),
        view_up=(0.0, 0.0, 1.0),
        view_angle=30.0 / 1.12,
    )

    def __init__(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        location_name: str,
        title: str | None = None,
        earth_radius: float = 0.25,
        sphere_radius: float = 1.0,
        style: SceneStyle | None = None,
        window_size=(1600, 1150),
        off_screen: bool = False,
    ) -> None:
        self.latitude_deg = latitude_deg
        self.longitude_deg = longitude_deg
        self.location_name = location_name
        self.title = (
            f"Celestial grids — {location_name}" if title is None else str(title)
        )
        self.earth_radius = earth_radius
        self.sphere_radius = sphere_radius
        self.style = style or SceneStyle()

        self.horizontal = horizontal_frame()
        self.equatorial = equatorial_frame(latitude_deg)

        self.plotter = pv.Plotter(
            window_size=window_size,
            off_screen=off_screen,
        )
        self.plotter.set_background(self.style.background)

        self.graph = SceneGraph()
        self._local_scale = 1.0
        self._title_actor: object | None = None
        self._closed = False
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
        self._add_celestial_shell_layer()
        self._add_earth_and_observer()
        self._add_axis()
        self.plotter.enable_lightkit()
        self.set_camera(self.canonical_camera, render=False)

    def _add_celestial_shell_layer(self) -> None:
        """Add the celestial shell through the scene object lifecycle."""
        self.shell = CelestialShellObject(
            name="celestial_shell.surface",
            radius=self.sphere_radius,
            style=self.style,
        )
        layer = Layer(name="celestial_shell")
        layer.add(self.shell)
        self.add(layer)


    def _add_earth_and_observer(self) -> None:
        zenith = self.horizontal.pole
        east = self.horizontal.east
        north = self.horizontal.zero

        self.earth = EarthObject(
            name="local_cartoon.earth",
            radius=self.earth_radius,
            rotation_axis=self.equatorial.pole,
            observer_zenith=zenith,
            observer_north=north,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
        )
        plane_center = self.earth_radius * zenith + 0.012 * zenith
        self.platform = SurfaceObject(
            name="local_cartoon.platform",
            surface=PlaneSurface(
                center=plane_center,
                normal=zenith,
                axis_u=east,
                width=1.85 * self.earth_radius,
                height=1.20 * self.earth_radius,
                style=SurfaceStyle(
                    color=self.style.plane_color,
                    opacity=0.52,
                    show_edges=True,
                    edge_color="#777777",
                    edge_width=1.0,
                ),
            ),
        )
        directions = (east, -east, north, -north)
        self.cardinal_vectors = tuple(
            VectorObject(
                name=f"local_cartoon.cardinal.{index}",
                vector=VectorArrow(
                    start=plane_center,
                    direction=direction,
                    scale=0.28 * self.earth_radius,
                    style=VectorStyle(color="#59645d"),
                ),
            )
            for index, direction in enumerate(directions)
        )
        self.platform_decoration = CardinalDirectionsDecoration(
            name="local_cartoon.platform.cardinal_directions",
            vectors=dict(
                zip(
                    CardinalDirectionsDecoration.required_directions,
                    self.cardinal_vectors,
                )
            ),
        )
        self.local_platform = LocalPlatform(
            name="local_cartoon.platform_context",
            surface=self.platform,
            decoration=self.platform_decoration,
        )

        observer_base = plane_center - 0.05 * self.earth_radius * north
        self.observer = Observer(
            name="canonical_observer",
            position=observer_base,
            frame=self.horizontal,
        )
        self.observer_representation = StickFigureRepresentation(
            name="local_cartoon.observer.stick_figure",
            observer=self.observer,
            height=0.92 * self.earth_radius,
        )
        self.observer_composition = ObserverComposition(
            name="local_cartoon.observer",
            observer=self.observer,
            representation=self.observer_representation,
            context=(self.local_platform,),
        )
        self.ideal_horizon = self.observer_composition.ideal_horizon

        self.local_cartoon = LocalCartoonLayer(
            name="local_cartoon",
            earth=self.earth,
        )
        self.local_cartoon.add_observer(self.observer_composition)
        self.add(self.local_cartoon)

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
            get_sphere_presence=lambda: self.shell.presence,
            get_local_scale=lambda: self._local_scale,
            reset_camera=self.reset_camera,
        )
        return self.controls.register_panel(panel)

    def _set_local_scale(self, value: float) -> None:
        self._local_scale = float(value)
        self.local_cartoon.set_scale(self._local_scale)

    def _set_sphere_presence(self, value: float) -> None:
        self.shell.set_presence(value)

    @property
    def camera_state(self) -> CameraState:
        """Return the complete current camera state."""
        camera = self.plotter.camera
        return CameraState(
            position=camera.position,
            focal_point=camera.focal_point,
            view_up=camera.up,
            view_angle=camera.view_angle,
            parallel_projection=camera.parallel_projection,
            parallel_scale=camera.parallel_scale,
        )

    def set_camera(
        self,
        state: CameraState,
        *,
        render: bool = True,
    ) -> None:
        """Apply an explicit camera state to the current scene."""
        if not isinstance(state, CameraState):
            raise TypeError("state must be a CameraState.")

        self.plotter.camera_position = [
            state.position,
            state.focal_point,
            state.view_up,
        ]
        camera = self.plotter.camera
        if state.parallel_projection:
            camera.enable_parallel_projection()
        else:
            camera.disable_parallel_projection()
        camera.view_angle = state.view_angle
        camera.parallel_scale = state.parallel_scale
        self.shell.refresh()
        if render:
            self.plotter.render()

    def reset_camera(self) -> None:
        """Restore the canonical illustration camera and refresh the shell."""
        self.set_camera(self.canonical_camera)

    def _ensure_title(self) -> None:
        if self._title_actor is None:
            self._title_actor = self.plotter.add_text(
                self.title,
                position="upper_left",
                font_size=18,
                color=self.style.text_color,
            )

    def render(self) -> None:
        """Refresh derived scene state and render exactly once."""
        self._ensure_title()
        self.controls.sync(render=False)
        self.shell.refresh()
        self.plotter.render()

    def save(
        self,
        path: str | Path,
        *,
        camera_state: CameraState | None = None,
        window_size: tuple[int, int] | None = None,
        transparent_background: bool = False,
    ) -> np.ndarray:
        """Render and save an image without closing the scene."""
        if camera_state is not None:
            self.set_camera(camera_state, render=False)

        self.render()
        screenshot_options = {
            "filename": Path(path),
            "transparent_background": transparent_background,
            "return_img": True,
        }
        if window_size is not None:
            screenshot_options["window_size"] = window_size

        image = self.plotter.screenshot(**screenshot_options)
        if image is None:
            raise RuntimeError("PyVista did not return the saved image.")
        return image

    def show(self, *, screenshot: str | None = None) -> None:
        self.render()
        self.plotter.show(
            screenshot=screenshot,
            auto_close=False,
        )

    def close(self) -> None:
        """Release scene graph and PyVista resources exactly once."""
        if self._closed:
            return

        self._closed = True

        self.graph.clear(render=False)
        self.plotter.close()
