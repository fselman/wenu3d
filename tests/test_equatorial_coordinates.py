import numpy as np
import pytest

from wenu3d.coordinates import EquatorialCoordinateGeometry
from wenu3d.frames import SphericalFrame
from wenu3d.targets import CelestialTarget


def equatorial_frame() -> SphericalFrame:
    return SphericalFrame(
        name="diagrammatic_equatorial",
        pole=(0.0, 0.0, 1.0),
        zero=(1.0, 0.0, 0.0),
        east=(0.0, 1.0, 0.0),
    )


def make_geometry(
    *,
    longitude_deg: float = 75.0,
    declination_deg: float = -20.0,
    radius: float = 2.0,
    **kwargs,
) -> EquatorialCoordinateGeometry:
    frame = equatorial_frame()
    target = CelestialTarget(
        name="target",
        direction=frame.point(longitude_deg, declination_deg),
        shell_radius=radius,
    )
    return EquatorialCoordinateGeometry(
        target=target,
        frame=frame,
        samples=11,
        **kwargs,
    )


def test_equatorial_angles_and_hour_circle_foot() -> None:
    geometry = make_geometry()

    assert geometry.longitude_deg == pytest.approx(75.0)
    assert geometry.declination_deg == pytest.approx(-20.0)
    np.testing.assert_allclose(
        geometry.hour_circle_foot,
        geometry.frame.point(75.0, 0.0, radius=2.0),
        atol=1e-12,
    )
    assert geometry.hour_circle_foot @ geometry.frame.pole == pytest.approx(
        0.0,
        abs=1e-12,
    )


def test_declination_arc_runs_from_equator_to_target() -> None:
    geometry = make_geometry(declination_deg=32.0)
    arc = geometry.declination_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(32.0)
    assert arc.samples == 11
    np.testing.assert_allclose(
        arc.start_point,
        geometry.hour_circle_foot,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        arc.end_point,
        geometry.target.display_position,
        atol=1e-12,
    )


def test_negative_declination_preserves_decreasing_arc_direction() -> None:
    geometry = make_geometry(declination_deg=-20.0)
    arc = geometry.declination_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(-20.0)
    np.testing.assert_allclose(
        arc.end_point,
        geometry.target.display_position,
        atol=1e-12,
    )


def test_longitude_arc_runs_from_frame_origin_to_hour_circle() -> None:
    geometry = make_geometry(longitude_deg=75.0)
    arc = geometry.longitude_arc

    assert arc is not None
    assert arc.span_deg == pytest.approx(75.0)
    np.testing.assert_allclose(
        arc.start_point,
        geometry.target.shell_radius * geometry.frame.zero,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        arc.end_point,
        geometry.hour_circle_foot,
        atol=1e-12,
    )


def test_complete_equatorial_circles_contain_target_and_poles() -> None:
    geometry = make_geometry(longitude_deg=75.0, declination_deg=-20.0)

    hour_points = geometry.hour_circle.points()
    declination_points = geometry.declination_circle_points
    assert np.max(hour_points @ geometry.frame.pole) == pytest.approx(2.0, abs=1e-3)
    assert np.min(hour_points @ geometry.frame.pole) == pytest.approx(-2.0, abs=1e-3)
    assert np.min(np.linalg.norm(
        hour_points - geometry.target.display_position,
        axis=1,
    )) < 0.04
    expected_polar_component = 2.0 * np.sin(np.deg2rad(-20.0))
    np.testing.assert_allclose(
        declination_points @ geometry.frame.pole,
        expected_polar_component,
        atol=1e-12,
    )


def test_diagrammatic_longitude_is_not_called_right_ascension() -> None:
    geometry = make_geometry(longitude_kind="diagrammatic")

    assert geometry.longitude_label == "Diagrammatic equatorial longitude"
    assert geometry.right_ascension_hours is None
    assert geometry.right_ascension_origin is None


def test_right_ascension_requires_and_reports_scientific_origin() -> None:
    geometry = make_geometry(
        longitude_deg=75.0,
        longitude_kind="right_ascension",
        right_ascension_origin="ICRS vernal equinox direction",
    )

    assert geometry.right_ascension_hours == pytest.approx(5.0)
    assert geometry.longitude_label == (
        "Right ascension (origin: ICRS vernal equinox direction)"
    )


def test_zero_spans_are_represented_without_invalid_arcs() -> None:
    origin_on_equator = make_geometry(
        longitude_deg=0.0,
        declination_deg=0.0,
    )
    east_on_equator = make_geometry(
        longitude_deg=90.0,
        declination_deg=0.0,
    )

    assert origin_on_equator.declination_arc is None
    assert origin_on_equator.longitude_arc is None
    assert east_on_equator.declination_arc is None
    assert east_on_equator.longitude_arc is not None


@pytest.mark.parametrize("declination_deg", [-90.0, 90.0])
def test_equatorial_geometry_rejects_undefined_polar_longitude(
    declination_deg: float,
) -> None:
    frame = equatorial_frame()
    target = CelestialTarget(
        name="pole",
        direction=frame.point(0.0, declination_deg),
    )

    with pytest.raises(ValueError, match="longitude is undefined"):
        EquatorialCoordinateGeometry(target=target, frame=frame)


def test_right_ascension_rejects_missing_or_misapplied_origin() -> None:
    for origin in (None, "   "):
        with pytest.raises(ValueError, match="scientific origin"):
            make_geometry(
                longitude_kind="right_ascension",
                right_ascension_origin=origin,
            )
    with pytest.raises(ValueError, match="requires right_ascension"):
        make_geometry(
            longitude_kind="diagrammatic",
            right_ascension_origin="not applicable",
        )


def test_equatorial_geometry_validates_kind_target_frame_and_samples() -> None:
    target = CelestialTarget(name="target", direction=(1.0, 0.0, 0.0))
    frame = equatorial_frame()

    with pytest.raises(ValueError, match="longitude_kind"):
        EquatorialCoordinateGeometry(
            target=target,
            frame=frame,
            longitude_kind="sidereal_angle",
        )
    with pytest.raises(TypeError, match="CelestialTarget"):
        EquatorialCoordinateGeometry(target=object(), frame=frame)
    with pytest.raises(TypeError, match="SphericalFrame"):
        EquatorialCoordinateGeometry(target=target, frame=object())
    for samples in (1, 2.5, True):
        with pytest.raises(ValueError, match="samples"):
            EquatorialCoordinateGeometry(
                target=target,
                frame=frame,
                samples=samples,
            )
