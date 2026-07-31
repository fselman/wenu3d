from __future__ import annotations

import numpy as np

from .frames import SphericalFrame


def _finite_scalar(value: float, *, name: str) -> float:
    array = np.asarray(value, dtype=float)
    if array.ndim != 0 or not np.isfinite(array):
        raise ValueError(f"{name} must be a finite scalar.")
    return float(array)


def _geographic_angles(
    latitude_deg: float,
    longitude_deg: float,
) -> tuple[float, float]:
    latitude = _finite_scalar(latitude_deg, name="Latitude")
    longitude = _finite_scalar(longitude_deg, name="Longitude")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    return np.deg2rad(latitude), np.deg2rad(longitude)


def earth_fixed_frame() -> SphericalFrame:
    """Return the spherical Earth-fixed world frame.

    The positive x axis is latitude 0, longitude 0; positive y is latitude 0,
    longitude 90 degrees East; and positive z is the geographic north pole.
    """
    return SphericalFrame(
        name="earth_fixed",
        pole=np.array([0.0, 0.0, 1.0]),
        zero=np.array([1.0, 0.0, 0.0]),
        east=np.array([0.0, 1.0, 0.0]),
    )


def geographic_position(
    latitude_deg: float,
    longitude_deg: float,
    *,
    radius: float = 1.0,
) -> np.ndarray:
    """Return a position on the spherical Earth in the Earth-fixed frame."""
    latitude, longitude = _geographic_angles(latitude_deg, longitude_deg)
    radius = _finite_scalar(radius, name="Radius")
    if radius <= 0.0:
        raise ValueError("Radius must be greater than zero.")

    cos_latitude = np.cos(latitude)
    return radius * np.array([
        cos_latitude * np.cos(longitude),
        cos_latitude * np.sin(longitude),
        np.sin(latitude),
    ])


def local_enu_frame(
    latitude_deg: float,
    longitude_deg: float,
) -> SphericalFrame:
    """Return the local East-North-Zenith frame at a spherical Earth site.

    At either geographic pole, longitude selects the limiting local meridian
    and therefore fixes the otherwise non-unique East and North directions.
    """
    latitude, longitude = _geographic_angles(latitude_deg, longitude_deg)

    cos_latitude = np.cos(latitude)
    sin_latitude = np.sin(latitude)
    cos_longitude = np.cos(longitude)
    sin_longitude = np.sin(longitude)

    zenith = np.array([
        cos_latitude * cos_longitude,
        cos_latitude * sin_longitude,
        sin_latitude,
    ])
    east = np.array([
        -sin_longitude,
        cos_longitude,
        0.0,
    ])
    north = np.array([
        -sin_latitude * cos_longitude,
        -sin_latitude * sin_longitude,
        cos_latitude,
    ])

    return SphericalFrame(
        name="local_enu",
        pole=zenith,
        zero=north,
        east=east,
    )
