from __future__ import annotations
import numpy as np
import pyvista as pv
from pyvista import examples
from .geometry import unit


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
