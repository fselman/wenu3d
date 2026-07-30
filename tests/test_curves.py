import numpy as np

from wenu3d.curves import Meridian, Parallel
from wenu3d.frames import horizontal_frame


def test_meridian_sampling_and_radius() -> None:
    frame = horizontal_frame()
    points = Meridian(
        frame,
        longitude_deg=30.0,
        latitude_min_deg=-45.0,
        latitude_max_deg=45.0,
        samples=7,
    ).points(radius=2.5)

    assert points.shape == (7, 3)
    np.testing.assert_allclose(
        np.linalg.norm(points, axis=1),
        2.5,
        atol=1e-12,
    )


def test_meridian_stays_in_constant_longitude_plane() -> None:
    frame = horizontal_frame()
    longitude_deg = 37.0
    points = Meridian(
        frame,
        longitude_deg=longitude_deg,
        samples=11,
    ).points()

    longitude_rad = np.deg2rad(longitude_deg)
    equatorial_direction = (
        np.cos(longitude_rad) * frame.zero
        + np.sin(longitude_rad) * frame.east
    )
    plane_normal = np.cross(frame.pole, equatorial_direction)

    np.testing.assert_allclose(
        points @ plane_normal,
        0.0,
        atol=1e-12,
    )


def test_parallel_sampling_radius_and_latitude() -> None:
    frame = horizontal_frame()
    latitude_deg = -30.0
    radius = 1.7
    points = Parallel(
        frame,
        latitude_deg=latitude_deg,
        samples=13,
    ).points(radius=radius)

    assert points.shape == (13, 3)
    np.testing.assert_allclose(
        np.linalg.norm(points, axis=1),
        radius,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        points @ frame.pole,
        radius * np.sin(np.deg2rad(latitude_deg)),
        atol=1e-12,
    )


def test_parallel_is_closed_by_repeated_endpoint() -> None:
    points = Parallel(
        horizontal_frame(),
        latitude_deg=20.0,
        samples=9,
    ).points()

    np.testing.assert_allclose(points[0], points[-1], atol=1e-12)
