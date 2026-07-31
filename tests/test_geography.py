import numpy as np
import pytest

from wenu3d.geography import (
    earth_fixed_frame,
    geographic_position,
    local_enu_frame,
)


def assert_orthonormal_enu(frame) -> None:
    basis = np.vstack([frame.east, frame.zero, frame.pole])
    np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(
        np.cross(frame.east, frame.zero),
        frame.pole,
        atol=1e-12,
    )


def test_earth_fixed_frame_defines_world_axes() -> None:
    frame = earth_fixed_frame()

    assert frame.name == "earth_fixed"
    np.testing.assert_allclose(frame.zero, [1.0, 0.0, 0.0])
    np.testing.assert_allclose(frame.east, [0.0, 1.0, 0.0])
    np.testing.assert_allclose(frame.pole, [0.0, 0.0, 1.0])


@pytest.mark.parametrize(
    ("latitude_deg", "longitude_deg", "expected"),
    [
        (0.0, 0.0, [1.0, 0.0, 0.0]),
        (0.0, 90.0, [0.0, 1.0, 0.0]),
        (0.0, 180.0, [-1.0, 0.0, 0.0]),
        (0.0, -90.0, [0.0, -1.0, 0.0]),
        (90.0, 37.0, [0.0, 0.0, 1.0]),
        (-90.0, -122.0, [0.0, 0.0, -1.0]),
    ],
)
def test_geographic_position_has_expected_known_values(
    latitude_deg: float,
    longitude_deg: float,
    expected: list[float],
) -> None:
    position = geographic_position(latitude_deg, longitude_deg)

    np.testing.assert_allclose(position, expected, atol=1e-12)


def test_geographic_position_preserves_requested_radius() -> None:
    position = geographic_position(-32.4524, -71.2311, radius=0.25)

    assert np.linalg.norm(position) == pytest.approx(0.25)


def test_local_enu_frame_at_greenwich_equator() -> None:
    frame = local_enu_frame(0.0, 0.0)

    np.testing.assert_allclose(frame.east, [0.0, 1.0, 0.0])
    np.testing.assert_allclose(frame.zero, [0.0, 0.0, 1.0])
    np.testing.assert_allclose(frame.pole, [1.0, 0.0, 0.0])
    assert_orthonormal_enu(frame)


def test_la_ligua_frame_is_tangent_to_earth() -> None:
    position = geographic_position(-32.4524, -71.2311, radius=0.25)
    frame = local_enu_frame(-32.4524, -71.2311)

    np.testing.assert_allclose(frame.pole, position / 0.25, atol=1e-12)
    assert np.dot(frame.east, position) == pytest.approx(0.0, abs=1e-12)
    assert np.dot(frame.zero, position) == pytest.approx(0.0, abs=1e-12)
    assert_orthonormal_enu(frame)


@pytest.mark.parametrize(
    ("latitude_deg", "longitude_deg"),
    [
        (90.0, 0.0),
        (90.0, 73.0),
        (-90.0, 0.0),
        (-90.0, -41.0),
    ],
)
def test_local_enu_frame_is_defined_at_geographic_poles(
    latitude_deg: float,
    longitude_deg: float,
) -> None:
    frame = local_enu_frame(latitude_deg, longitude_deg)
    position = geographic_position(latitude_deg, longitude_deg)

    np.testing.assert_allclose(frame.pole, position, atol=1e-12)
    assert_orthonormal_enu(frame)


def test_antipodal_sites_have_opposite_positions_and_zeniths() -> None:
    latitude_deg = -32.4524
    longitude_deg = -71.2311
    position = geographic_position(latitude_deg, longitude_deg)
    antipode = geographic_position(-latitude_deg, longitude_deg + 180.0)
    frame = local_enu_frame(latitude_deg, longitude_deg)
    antipodal_frame = local_enu_frame(-latitude_deg, longitude_deg + 180.0)

    np.testing.assert_allclose(antipode, -position, atol=1e-12)
    np.testing.assert_allclose(antipodal_frame.pole, -frame.pole, atol=1e-12)
    assert_orthonormal_enu(antipodal_frame)


@pytest.mark.parametrize("latitude_deg", [-90.1, 90.1, np.inf, np.nan])
def test_geography_rejects_invalid_latitude(latitude_deg: float) -> None:
    with pytest.raises(ValueError, match="Latitude"):
        geographic_position(latitude_deg, 0.0)
    with pytest.raises(ValueError, match="Latitude"):
        local_enu_frame(latitude_deg, 0.0)


@pytest.mark.parametrize("longitude_deg", [-np.inf, np.inf, np.nan])
def test_geography_rejects_nonfinite_longitude(longitude_deg: float) -> None:
    with pytest.raises(ValueError, match="Longitude"):
        geographic_position(0.0, longitude_deg)
    with pytest.raises(ValueError, match="Longitude"):
        local_enu_frame(0.0, longitude_deg)


@pytest.mark.parametrize("radius", [0.0, -1.0, np.inf, np.nan])
def test_geographic_position_rejects_invalid_radius(radius: float) -> None:
    with pytest.raises(ValueError, match="Radius"):
        geographic_position(0.0, 0.0, radius=radius)
