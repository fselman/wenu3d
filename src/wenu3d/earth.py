from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
import pyvista as pv
from pyvista import examples

from .geometry import unit
from .scene_object import SceneObject


def orient_earth_to_observer(
    mesh: pv.PolyData,
    *,
    rotation_axis,
    observer_zenith,
    latitude_deg: float,
    longitude_deg: float,
    texture_longitude_correction_deg: float = 180.0,
) -> pv.PolyData:
    result = mesh.copy(deep=True)

    axis = unit(rotation_axis)
    zenith = unit(observer_zenith)

    lat = np.deg2rad(latitude_deg)
    lon = np.deg2rad(longitude_deg + texture_longitude_correction_deg)

    q = unit((zenith - np.sin(lat) * axis) / np.cos(lat))
    t = unit(np.cross(axis, q))

    earth_x = np.cos(lon) * q - np.sin(lon) * t
    earth_y = np.sin(lon) * q + np.cos(lon) * t

    transform = np.column_stack([earth_x, earth_y, axis])
    result.points = result.points @ transform.T
    return result


def realistic_earth(
    radius: float,
    *,
    rotation_axis,
    observer_zenith,
    latitude_deg: float,
    longitude_deg: float,
) -> tuple[pv.PolyData, pv.Texture]:
    earth = examples.planets.load_earth(
        radius=radius,
        lat_resolution=180,
        lon_resolution=360,
    )
    texture = examples.load_globe_texture()
    earth = orient_earth_to_observer(
        earth,
        rotation_axis=rotation_axis,
        observer_zenith=observer_zenith,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
    )
    return earth, texture


@dataclass
class EarthObject(SceneObject):
    """Lifecycle-managed rendering of the current oriented cartoon Earth."""

    radius: float = 0.25
    rotation_axis: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 0.0, 1.0])
    )
    observer_zenith: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 0.0, 1.0])
    )
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    ambient: float = 0.28
    diffuse: float = 0.78
    specular: float = 0.10
    specular_power: float = 12.0

    _mesh: pv.PolyData | None = field(default=None, init=False, repr=False)
    _texture: pv.Texture | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.radius = float(self.radius)
        if not np.isfinite(self.radius) or self.radius <= 0.0:
            raise ValueError("Earth radius must be finite and greater than zero.")
        self.rotation_axis = unit(self.rotation_axis)
        self.observer_zenith = unit(self.observer_zenith)
        self.latitude_deg = float(self.latitude_deg)
        self.longitude_deg = float(self.longitude_deg)
        if not np.isfinite(self.latitude_deg):
            raise ValueError("Earth observer latitude must be finite.")
        if not -90.0 < self.latitude_deg < 90.0:
            raise ValueError(
                "Legacy Earth orientation requires latitude strictly between "
                "-90 and 90 degrees."
            )
        if not np.isfinite(self.longitude_deg):
            raise ValueError("Earth observer longitude must be finite.")

    @property
    def mesh(self) -> pv.PolyData | None:
        return self._mesh

    @property
    def texture(self) -> pv.Texture | None:
        return self._texture

    def build(self, plotter: pv.Plotter) -> None:
        self._prepare_build(plotter)
        earth, texture = realistic_earth(
            self.radius,
            rotation_axis=self.rotation_axis,
            observer_zenith=self.observer_zenith,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
        )
        self._mesh = earth
        self._texture = texture
        self.add_actor(
            plotter.add_mesh(
                earth,
                texture=texture,
                smooth_shading=True,
                ambient=self.ambient,
                diffuse=self.diffuse,
                specular=self.specular,
                specular_power=self.specular_power,
            )
        )

    def detach(self, *, render: bool = True) -> None:
        super().detach(render=render)
        self._mesh = None
        self._texture = None
