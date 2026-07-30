from unittest.mock import Mock

import pytest

from wenu3d import CameraState
from wenu3d.scene import CelestialScene


def make_state() -> CameraState:
    return CameraState(
        position=(2.0, -3.0, 1.5),
        focal_point=(0.0, 0.0, 0.0),
        view_up=(0.0, 0.0, 1.0),
        view_angle=25.0,
        parallel_projection=False,
        parallel_scale=1.5,
    )


def test_camera_state_normalizes_sequences_to_float_tuples() -> None:
    state = CameraState(
        position=[2, -3, 1],
        focal_point=[0, 0, 0],
        view_up=[0, 0, 1],
    )

    assert state.position == (2.0, -3.0, 1.0)
    assert state.focal_point == (0.0, 0.0, 0.0)
    assert state.view_up == (0.0, 0.0, 1.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("position", (1.0, 2.0), "exactly three"),
        ("view_up", (0.0, 0.0, 0.0), "nonzero"),
        ("view_angle", 0.0, "between 0 and 180"),
        ("parallel_scale", 0.0, "positive"),
    ],
)
def test_camera_state_rejects_invalid_values(
    field: str,
    value: object,
    message: str,
) -> None:
    values = {
        "position": (2.0, -3.0, 1.5),
        "focal_point": (0.0, 0.0, 0.0),
        "view_up": (0.0, 0.0, 1.0),
        "view_angle": 25.0,
        "parallel_scale": 1.5,
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        CameraState(**values)


def test_camera_state_rejects_focal_point_at_camera() -> None:
    with pytest.raises(ValueError, match="must be different"):
        CameraState(
            position=(1.0, 2.0, 3.0),
            focal_point=(1.0, 2.0, 3.0),
            view_up=(0.0, 0.0, 1.0),
        )


def test_scene_applies_camera_state_without_cumulative_zoom() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = Mock()
    scene._refresh_celestial_sphere = Mock()
    state = make_state()

    scene.set_camera(state)
    scene.set_camera(state)

    assert scene.plotter.camera_position == [
        state.position,
        state.focal_point,
        state.view_up,
    ]
    assert scene.plotter.camera.view_angle == 25.0
    assert (
        scene.plotter.camera.disable_parallel_projection.call_count
        == 2
    )
    scene.plotter.camera.enable_parallel_projection.assert_not_called()
    assert scene.plotter.camera.parallel_scale == 1.5
    assert scene._refresh_celestial_sphere.call_count == 2
    assert scene.plotter.render.call_count == 2
    scene.plotter.camera.zoom.assert_not_called()


def test_scene_captures_current_camera_state() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = Mock()
    scene.plotter.camera.position = (4.0, 3.0, 2.0)
    scene.plotter.camera.focal_point = (0.0, 0.0, 0.0)
    scene.plotter.camera.up = (0.0, 0.0, 1.0)
    scene.plotter.camera.view_angle = 22.0
    scene.plotter.camera.parallel_projection = False
    scene.plotter.camera.parallel_scale = 1.0

    assert scene.camera_state == CameraState(
        position=(4.0, 3.0, 2.0),
        focal_point=(0.0, 0.0, 0.0),
        view_up=(0.0, 0.0, 1.0),
        view_angle=22.0,
    )
