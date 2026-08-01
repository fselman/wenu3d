from unittest.mock import Mock, PropertyMock, patch

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
    scene.shell = Mock()
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
    assert scene.shell.refresh.call_count == 2
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


def test_scene_selects_parallel_projection_through_camera_state() -> None:
    scene = object.__new__(CelestialScene)
    scene.set_camera = Mock()
    state = make_state()
    scene.default_camera = state

    with patch.object(
        CelestialScene,
        "camera_state",
        new_callable=PropertyMock,
        return_value=state,
    ):
        scene.set_parallel_projection(
            True,
            parallel_scale=1.12,
            make_default=True,
            render=False,
        )

    applied = scene.set_camera.call_args.args[0]
    assert applied.parallel_projection is True
    assert applied.parallel_scale == pytest.approx(1.12)
    assert applied.position == state.position
    assert applied.focal_point == state.focal_point
    assert applied.view_up == state.view_up
    assert scene.default_camera.parallel_projection is True
    assert scene.default_camera.parallel_scale == pytest.approx(1.12)
    scene.set_camera.assert_called_once_with(applied, render=False)


def test_projection_selection_preserves_scale_when_unspecified() -> None:
    scene = object.__new__(CelestialScene)
    scene.set_camera = Mock()
    state = make_state()

    with patch.object(
        CelestialScene,
        "camera_state",
        new_callable=PropertyMock,
        return_value=state,
    ):
        scene.set_parallel_projection(True)

    applied = scene.set_camera.call_args.args[0]
    assert applied.parallel_projection is True
    assert applied.parallel_scale == state.parallel_scale


def test_projection_selection_validates_mode_and_scale() -> None:
    scene = object.__new__(CelestialScene)
    state = make_state()
    scene.default_camera = state

    with patch.object(
        CelestialScene,
        "camera_state",
        new_callable=PropertyMock,
        return_value=state,
    ):
        with pytest.raises(TypeError, match="boolean"):
            scene.set_parallel_projection(1)
        with pytest.raises(TypeError, match="make_default"):
            scene.set_parallel_projection(True, make_default=1)
        with pytest.raises(ValueError, match="positive"):
            scene.set_parallel_projection(True, parallel_scale=0.0)
