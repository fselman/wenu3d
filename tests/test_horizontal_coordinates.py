import numpy as np
import pytest

from wenu3d.coordinates import HorizontalCoordinateGeometry
from wenu3d.frames import horizontal_frame
from wenu3d.targets import CelestialTarget


def make_geometry(
    *,
    azimuth_deg: float,
    altitude_deg: float,
    radius: float = 2.0,
    samples: int = 11,
) -> HorizontalCoordinateGeometry:
    frame = horizontal_frame()
    target = CelestialTarget(
        name="target",
        direction=frame.point(azimuth_deg, altitude_deg),
        shell_radius=radius,
    )
    return HorizontalCoordinateGeometry(
        target=target,
        frame=frame,
        samples=samples,
    )


def test_horizontal_angles_follow_north_through_east_convention() -> None:
    geometry = make_geometry(azimuth_deg=123.0, altitude_deg=37.0)

    assert geometry.azimuth_deg == pytest.approx(123.0)
    assert geometry.altitude_deg == pytest.approx(37.0)


def test_vertical_circle_foot_is_centered_on_ideal_horizon() -> None:
    geometry = make_geometry(azimuth_deg=72.0, altitude_deg=24.0)
    frame = geometry.frame
    foot = geometry.vertical_circle_foot

    assert np.linalg.norm(foot) == pytest.approx(2.0)
    assert foot @ frame.pole == pytest.approx(0.0, abs=1e-12)
    np.testing.assert_allclose(
        foot,
        frame.point(72.0, 0.0, radius=2.0),
        atol=1e-12,
    )


def test_altitude_arc_runs_from_horizon_foot_to_target() -> None:
    geometry = make_geometry(azimuth_deg=72.0, altitude_deg=24.0)
    arc = geometry.altitude_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(24.0)
    assert arc.samples == 11
    np.testing.assert_allclose(
        arc.start_point,
        geometry.vertical_circle_foot,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        arc.end_point,
        geometry.target.display_position,
        atol=1e-12,
    )


def test_negative_altitude_preserves_decreasing_arc_direction() -> None:
    geometry = make_geometry(azimuth_deg=210.0, altitude_deg=-18.0)
    arc = geometry.altitude_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(-18.0)
    np.testing.assert_allclose(
        arc.end_point,
        geometry.target.display_position,
        atol=1e-12,
    )


def test_azimuth_arc_runs_from_north_to_vertical_circle_foot() -> None:
    geometry = make_geometry(azimuth_deg=123.0, altitude_deg=37.0)
    arc = geometry.azimuth_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(123.0)
    np.testing.assert_allclose(
        arc.start_point,
        geometry.target.shell_radius * geometry.frame.zero,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        arc.end_point,
        geometry.vertical_circle_foot,
        atol=1e-12,
    )


def test_coordinate_arcs_use_target_direction_not_finite_observer() -> None:
    geometry = make_geometry(azimuth_deg=45.0, altitude_deg=30.0)

    assert not hasattr(geometry, "observer_position")
    np.testing.assert_allclose(
        geometry.altitude_arc.end_point,
        2.0 * np.asarray(geometry.target.direction),
        atol=1e-12,
    )


def test_degenerate_zero_spans_are_represented_without_invalid_arcs() -> None:
    north_horizon = make_geometry(azimuth_deg=0.0, altitude_deg=0.0)
    east_horizon = make_geometry(azimuth_deg=90.0, altitude_deg=0.0)

    assert north_horizon.altitude_arc is None
    assert north_horizon.azimuth_arc is None
    assert east_horizon.altitude_arc is None
    assert east_horizon.azimuth_arc is not None


@pytest.mark.parametrize("altitude_deg", [-90.0, 90.0])
def test_horizontal_geometry_rejects_undefined_zenith_nadir_azimuth(
    altitude_deg: float,
) -> None:
    frame = horizontal_frame()
    target = CelestialTarget(
        name="pole",
        direction=frame.point(0.0, altitude_deg),
    )

    with pytest.raises(ValueError, match="azimuth is undefined"):
        HorizontalCoordinateGeometry(target=target, frame=frame)


def test_horizontal_geometry_validates_target_frame_and_samples() -> None:
    target = CelestialTarget(name="target", direction=(1.0, 0.0, 0.0))
    frame = horizontal_frame()

    with pytest.raises(TypeError, match="CelestialTarget"):
        HorizontalCoordinateGeometry(target=object(), frame=frame)
    with pytest.raises(TypeError, match="SphericalFrame"):
        HorizontalCoordinateGeometry(target=target, frame=object())
    for samples in (1, 2.5, True):
        with pytest.raises(ValueError, match="samples"):
            HorizontalCoordinateGeometry(
                target=target,
                frame=frame,
                samples=samples,
            )
