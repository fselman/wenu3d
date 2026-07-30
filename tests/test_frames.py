import numpy as np
import pytest

from wenu3d.frames import (
    SphericalFrame,
    equatorial_frame,
    horizontal_frame,
)


def assert_orthonormal(frame: SphericalFrame) -> None:
    basis = np.vstack([frame.zero, frame.east, frame.pole])

    np.testing.assert_allclose(
        basis @ basis.T,
        np.eye(3),
        atol=1e-12,
    )


def test_frame_orthonormalizes_input_basis() -> None:
    frame = SphericalFrame(
        name="test",
        pole=np.array([0.0, 0.0, 2.0]),
        zero=np.array([0.0, 3.0, 1.0]),
        east=np.array([4.0, 1.0, 1.0]),
    )

    assert_orthonormal(frame)


def test_frame_infers_right_handed_east_direction() -> None:
    frame = SphericalFrame(
        name="inferred",
        pole=np.array([0.0, 0.0, 1.0]),
        zero=np.array([0.0, 1.0, 0.0]),
    )

    np.testing.assert_allclose(
        np.cross(frame.zero, frame.east),
        frame.pole,
        atol=1e-12,
    )


def test_horizontal_frame_uses_local_cartesian_convention() -> None:
    frame = horizontal_frame()

    np.testing.assert_allclose(frame.east, [1.0, 0.0, 0.0])
    np.testing.assert_allclose(frame.zero, [0.0, 1.0, 0.0])
    np.testing.assert_allclose(frame.pole, [0.0, 0.0, 1.0])
    assert_orthonormal(frame)


@pytest.mark.parametrize(
    ("longitude_deg", "latitude_deg", "expected"),
    [
        (0.0, 0.0, [0.0, 1.0, 0.0]),
        (90.0, 0.0, [1.0, 0.0, 0.0]),
        (0.0, 90.0, [0.0, 0.0, 1.0]),
        (0.0, -90.0, [0.0, 0.0, -1.0]),
    ],
)
def test_horizontal_frame_known_directions(
    longitude_deg: float,
    latitude_deg: float,
    expected: list[float],
) -> None:
    point = horizontal_frame().point(longitude_deg, latitude_deg)

    np.testing.assert_allclose(point, expected, atol=1e-12)


def test_point_broadcasts_longitude_and_latitude() -> None:
    points = horizontal_frame().point(
        longitude_deg=[0.0, 90.0, 180.0],
        latitude_deg=0.0,
        radius=2.0,
    )

    assert points.shape == (3, 3)
    np.testing.assert_allclose(
        np.linalg.norm(points, axis=1),
        2.0,
        atol=1e-12,
    )


@pytest.mark.parametrize("latitude_deg", [-60.0, 0.0, 45.0])
def test_equatorial_frame_has_expected_pole(
    latitude_deg: float,
) -> None:
    frame = equatorial_frame(latitude_deg)
    latitude_rad = np.deg2rad(latitude_deg)

    np.testing.assert_allclose(
        frame.pole,
        [0.0, np.cos(latitude_rad), np.sin(latitude_rad)],
        atol=1e-12,
    )
    assert_orthonormal(frame)
