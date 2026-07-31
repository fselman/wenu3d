import numpy as np
import pytest

from wenu3d import CurveStyle, SphericalArc
from wenu3d.frames import horizontal_frame


def test_great_circle_arc_has_expected_endpoints_and_radius() -> None:
    frame = horizontal_frame()
    arc = SphericalArc.great_circle(
        frame,
        start_deg=0.0,
        end_deg=90.0,
        radius=2.0,
        samples=7,
    )

    points = arc.points()

    assert arc.is_great_circle
    assert arc.span_deg == 90.0
    assert points.shape == (7, 3)
    np.testing.assert_allclose(points[0], 2.0 * frame.zero, atol=1e-12)
    np.testing.assert_allclose(points[-1], 2.0 * frame.east, atol=1e-12)
    np.testing.assert_allclose(
        np.linalg.norm(points, axis=1),
        2.0,
        atol=1e-12,
    )


def test_arc_preserves_decreasing_parameter_direction() -> None:
    frame = horizontal_frame()
    arc = SphericalArc.great_circle(
        frame,
        start_deg=90.0,
        end_deg=0.0,
        samples=5,
    )

    points = arc.points()

    assert arc.span_deg == -90.0
    np.testing.assert_allclose(points[0], frame.east, atol=1e-12)
    np.testing.assert_allclose(points[-1], frame.zero, atol=1e-12)


def test_arc_crosses_zero_with_unwrapped_parameters() -> None:
    frame = horizontal_frame()
    arc = SphericalArc.great_circle(
        frame,
        start_deg=350.0,
        end_deg=370.0,
        samples=3,
    )

    np.testing.assert_allclose(arc.points()[1], frame.zero, atol=1e-12)


def test_small_circle_has_constant_frame_latitude() -> None:
    frame = horizontal_frame()
    latitude_deg = 30.0
    radius = 1.7
    arc = SphericalArc.small_circle(
        frame,
        latitude_deg=latitude_deg,
        start_deg=-45.0,
        end_deg=75.0,
        radius=radius,
        samples=11,
    )

    points = arc.points()

    assert not arc.is_great_circle
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


def test_full_revolution_repeats_endpoint() -> None:
    arc = SphericalArc.small_circle(
        horizontal_frame(),
        latitude_deg=-20.0,
        start_deg=15.0,
        end_deg=375.0,
        samples=37,
    )

    np.testing.assert_allclose(arc.start_point, arc.end_point, atol=1e-12)


def test_arc_converts_directly_to_styled_sampled_curve() -> None:
    arc = SphericalArc.great_circle(
        horizontal_frame(),
        start_deg=0.0,
        end_deg=60.0,
        samples=9,
    )
    style = CurveStyle(
        color="gold",
        width=8.0,
        arrowheads="end",
    )

    curve = arc.to_curve(style=style, visible=False)

    np.testing.assert_allclose(curve.as_array(), arc.points(), atol=1e-12)
    assert curve.style is style
    assert curve.visible is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_deg": np.nan},
        {"end_deg": np.inf},
        {"latitude_deg": np.nan},
        {"latitude_deg": -90.0},
        {"latitude_deg": 90.0},
        {"start_deg": 10.0, "end_deg": 10.0},
        {"start_deg": 10.0, "end_deg": 10.0 + 1e-13},
        {"start_deg": 0.0, "end_deg": 361.0},
        {"start_deg": 0.0, "end_deg": -361.0},
        {"radius": 0.0},
        {"radius": -1.0},
        {"radius": np.inf},
        {"samples": 1},
        {"samples": 2.5},
        {"samples": True},
    ],
)
def test_spherical_arc_rejects_invalid_definition(kwargs) -> None:
    arguments = {
        "frame": horizontal_frame(),
        "start_deg": 0.0,
        "end_deg": 90.0,
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError):
        SphericalArc(**arguments)


def test_spherical_arc_rejects_invalid_frame() -> None:
    with pytest.raises(TypeError, match="frame"):
        SphericalArc(frame=None, start_deg=0.0, end_deg=90.0)


def test_small_circle_constructor_rejects_great_circle() -> None:
    with pytest.raises(ValueError, match="great_circle"):
        SphericalArc.small_circle(
            horizontal_frame(),
            latitude_deg=0.0,
            start_deg=0.0,
            end_deg=90.0,
        )
