import numpy as np
import pytest

from wenu3d.frames import SphericalFrame, horizontal_frame
from wenu3d.horizons import IdealHorizon
from wenu3d.observer_model import Observer
from wenu3d.surfaces import SurfaceStyle


def make_observer(frame=None) -> Observer:
    return Observer(
        name="observer",
        position=np.array([0.0, -0.01, 0.262]),
        frame=frame or horizontal_frame(),
    )


def test_ideal_horizon_uses_observer_frame_at_celestial_origin() -> None:
    observer = make_observer()
    horizon = IdealHorizon(observer)

    np.testing.assert_allclose(horizon.origin, [0.0, 0.0, 0.0])
    np.testing.assert_allclose(horizon.normal, observer.frame.pole)
    np.testing.assert_allclose(horizon.east, observer.frame.east)
    np.testing.assert_allclose(horizon.north, observer.frame.zero)
    assert not np.allclose(horizon.origin, observer.position)


def test_ideal_horizon_supports_arbitrary_observer_orientation() -> None:
    pole = np.array([1.0, 1.0, 1.0])
    north = np.array([-1.0, 1.0, 0.0])
    frame = SphericalFrame(
        name="tilted",
        pole=pole,
        zero=north,
        east=np.cross(north, pole),
    )
    horizon = IdealHorizon(make_observer(frame))

    basis = np.asarray((horizon.east, horizon.north, horizon.normal))
    np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(
        np.cross(horizon.east, horizon.north),
        horizon.normal,
        atol=1e-12,
    )


def test_signed_distance_and_projection_follow_zenith() -> None:
    horizon = IdealHorizon(make_observer())
    points = np.array([
        [1.0, 2.0, 3.0],
        [-2.0, 4.0, -5.0],
    ])

    np.testing.assert_allclose(horizon.signed_distance(points), [3.0, -5.0])
    projected = horizon.project(points)
    np.testing.assert_allclose(projected, [[1.0, 2.0, 0.0], [-2.0, 4.0, 0.0]])
    np.testing.assert_allclose(horizon.signed_distance(projected), 0.0)
    assert horizon.signed_distance([0.0, 0.0, 2.5]) == pytest.approx(2.5)


@pytest.mark.parametrize(
    "points",
    [
        [1.0, 2.0],
        [[1.0, 2.0], [3.0, 4.0]],
        [1.0, np.nan, 3.0],
    ],
)
def test_ideal_horizon_rejects_invalid_query_points(points) -> None:
    horizon = IdealHorizon(make_observer())

    with pytest.raises(ValueError, match="points"):
        horizon.project(points)


def test_display_surface_is_centered_parallel_and_hidden_by_default() -> None:
    horizon = IdealHorizon(make_observer())
    surface = horizon.as_surface(width=2.0)

    np.testing.assert_allclose(surface.center, horizon.origin)
    np.testing.assert_allclose(surface.normal, horizon.normal)
    np.testing.assert_allclose(surface.axis_u, horizon.east)
    np.testing.assert_allclose(surface.axis_v, horizon.north)
    assert surface.width == 2.0
    assert surface.height == 2.0
    assert surface.visible is False


def test_display_surface_accepts_explicit_extent_style_and_visibility() -> None:
    style = SurfaceStyle(color="blue", opacity=0.2)
    surface = IdealHorizon(make_observer()).as_surface(
        width=3.0,
        height=1.5,
        style=style,
        visible=True,
    )

    assert surface.width == 3.0
    assert surface.height == 1.5
    assert surface.style is style
    assert surface.visible is True


def test_ideal_horizon_requires_observer() -> None:
    with pytest.raises(TypeError, match="Observer"):
        IdealHorizon(object())


def test_ideal_horizon_rejects_non_enu_frame() -> None:
    frame = SphericalFrame(
        name="longitude_frame",
        pole=np.array([0.0, 0.0, 1.0]),
        zero=np.array([1.0, 0.0, 0.0]),
    )

    with pytest.raises(ValueError, match="East-North-Zenith"):
        IdealHorizon(make_observer(frame))
