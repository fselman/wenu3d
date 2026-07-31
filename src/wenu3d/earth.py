from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
import pyvista as pv
from pyvista import examples

from .frames import SphericalFrame
from .geography import geographic_position, local_enu_frame
from .geometry import unit
from .observer_model import Observer
from .scene_object import SceneObject


EARTH_TEXTURE_LONGITUDE_CORRECTION_DEG = 180.0


def earth_orientation_matrix(
    *,
    rotation_axis,
    observer_zenith,
    latitude_deg: float,
    longitude_deg: float,
    observer_north=None,
    texture_longitude_correction_deg: float = (
        EARTH_TEXTURE_LONGITUDE_CORRECTION_DEG
    ),
) -> np.ndarray:
    """Map the Earth-fixed source basis into the illustration display basis."""
    axis = unit(rotation_axis)
    zenith = unit(observer_zenith)
    latitude = float(latitude_deg)
    longitude = float(longitude_deg)
    correction = float(texture_longitude_correction_deg)
    if not np.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
        raise ValueError("Earth observer latitude must be between -90 and 90.")
    if not np.isfinite(longitude):
        raise ValueError("Earth observer longitude must be finite.")
    if not np.isfinite(correction):
        raise ValueError("Texture longitude correction must be finite.")

    latitude_rad = np.deg2rad(latitude)
    cos_latitude = np.cos(latitude_rad)
    sin_latitude = np.sin(latitude_rad)
    if observer_north is None:
        if abs(cos_latitude) > 1e-12:
            north = unit(
                (axis - sin_latitude * zenith) / cos_latitude
            )
        else:
            reference = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(reference, zenith)) > 0.9:
                reference = np.array([0.0, 1.0, 0.0])
            north = unit(
                reference - np.dot(reference, zenith) * zenith
            )
    else:
        north_value = np.asarray(observer_north, dtype=float)
        if north_value.shape != (3,) or not np.all(np.isfinite(north_value)):
            raise ValueError(
                "Observer North must contain three finite components."
            )
        north = unit(north_value - np.dot(north_value, zenith) * zenith)

    east = unit(np.cross(north, zenith))
    north = unit(np.cross(zenith, east))
    expected_axis = sin_latitude * zenith + cos_latitude * north
    if not np.allclose(axis, expected_axis, atol=1e-12):
        raise ValueError(
            "Rotation axis is inconsistent with the observer display frame."
        )

    source = local_enu_frame(
        latitude,
        longitude + correction,
    )
    source_basis = np.column_stack([
        source.east,
        source.zero,
        source.pole,
    ])
    target_basis = np.column_stack([east, north, zenith])
    return target_basis @ source_basis.T


def orient_earth_to_observer(
    mesh: pv.PolyData,
    *,
    rotation_axis,
    observer_zenith,
    latitude_deg: float,
    longitude_deg: float,
    observer_north=None,
    texture_longitude_correction_deg: float = (
        EARTH_TEXTURE_LONGITUDE_CORRECTION_DEG
    ),
) -> pv.PolyData:
    result = mesh.copy(deep=True)
    transform = earth_orientation_matrix(
        rotation_axis=rotation_axis,
        observer_zenith=observer_zenith,
        observer_north=observer_north,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        texture_longitude_correction_deg=(
            texture_longitude_correction_deg
        ),
    )
    result.points = result.points @ transform.T
    return result


def realistic_earth(
    radius: float,
    *,
    rotation_axis,
    observer_zenith,
    latitude_deg: float,
    longitude_deg: float,
    observer_north=None,
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
        observer_north=observer_north,
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
        default_factory=lambda: np.array([1.0, 0.0, 0.0])
    )
    observer_north: np.ndarray | None = None
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
        if self.observer_north is not None:
            self.observer_north = unit(self.observer_north)
        self.latitude_deg = float(self.latitude_deg)
        self.longitude_deg = float(self.longitude_deg)
        earth_orientation_matrix(
            rotation_axis=self.rotation_axis,
            observer_zenith=self.observer_zenith,
            observer_north=self.observer_north,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
        )

    @property
    def orientation_matrix(self) -> np.ndarray:
        return earth_orientation_matrix(
            rotation_axis=self.rotation_axis,
            observer_zenith=self.observer_zenith,
            observer_north=self.observer_north,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
        )

    def display_observer(self, observer: Observer) -> Observer:
        """Return a geographic observer expressed in the rendered frame."""
        if not isinstance(observer, Observer):
            raise TypeError("observer must be an Observer.")
        if observer.latitude_deg is None or observer.longitude_deg is None:
            raise ValueError("A displayed observer must be geographic.")
        radius = float(np.linalg.norm(observer.position))
        if not np.isclose(radius, self.radius, atol=1e-12):
            raise ValueError("Observer radius must match the rendered Earth.")

        longitude = (
            observer.longitude_deg
            + EARTH_TEXTURE_LONGITUDE_CORRECTION_DEG
        )
        source_frame = local_enu_frame(observer.latitude_deg, longitude)
        matrix = self.orientation_matrix
        return Observer(
            name=observer.name,
            position=matrix @ geographic_position(
                observer.latitude_deg,
                longitude,
                radius=radius,
            ),
            frame=SphericalFrame(
                name=f"{observer.name}.display_enu",
                pole=matrix @ source_frame.pole,
                zero=matrix @ source_frame.zero,
                east=matrix @ source_frame.east,
            ),
        )

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
            observer_north=self.observer_north,
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
