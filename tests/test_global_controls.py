from unittest.mock import Mock

import pytest

from wenu3d import GlobalControlPanel
from wenu3d.scene import CelestialScene


def make_plotter() -> Mock:
    plotter = Mock()
    plotter.window_size = (1800, 1200)
    plotter.add_text.return_value = object()
    slider = Mock()
    slider.GetRepresentation.return_value = Mock()
    plotter.add_slider_widget.return_value = slider
    return plotter


def make_panel(
    *,
    origin_x: int = 182,
    origin_y: int = 948,
) -> GlobalControlPanel:
    return GlobalControlPanel(
        plotter=make_plotter(),
        set_sphere_presence=Mock(),
        set_local_scale=Mock(),
        reset_camera=Mock(),
        origin_x=origin_x,
        origin_y=origin_y,
    )


def test_global_panel_declares_full_slider_footprint() -> None:
    assert make_panel().control_size == (340, 260)


def test_global_panel_uses_compact_nonoverlapping_sliders() -> None:
    panel = make_panel()

    panel.add()

    calls = panel.plotter.add_slider_widget.call_args_list
    sphere = calls[0].kwargs
    local = calls[1].kwargs

    assert sphere["pointa"] == pytest.approx(
        (197 / 1800, 870 / 1200)
    )
    assert sphere["pointb"] == pytest.approx(
        (507 / 1800, 870 / 1200)
    )
    assert local["pointa"] == pytest.approx(
        (197 / 1800, 773 / 1200)
    )
    assert local["pointb"] == pytest.approx(
        (507 / 1800, 773 / 1200)
    )
    assert sphere["title_height"] == 0.014
    assert local["title_height"] == 0.014
    assert len(panel.widgets) == 5

    representation = (
        panel.plotter.add_slider_widget.return_value
        .GetRepresentation.return_value
    )
    assert representation.SetLabelHeight.call_count == 2


def test_global_panel_reset_camera_action_is_momentary() -> None:
    panel = make_panel()
    panel.add()

    callback = (
        panel.plotter.add_checkbox_button_widget
        .call_args.kwargs["callback"]
    )
    callback(True)

    panel.reset_camera.assert_called_once_with()
    panel._reset_camera_widget.GetRepresentation().SetState.assert_called_with(
        0
    )


def test_scene_registers_global_panel_without_coordinates() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = make_plotter()
    scene.controls = Mock()
    scene.controls.register_panel.side_effect = lambda panel: panel

    panel = scene.add_global_controls()

    assert isinstance(panel, GlobalControlPanel)
    scene.controls.register_panel.assert_called_once_with(panel)


def test_global_panel_callbacks_update_scene() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = make_plotter()
    scene.controls = Mock()
    scene.controls.register_panel.side_effect = lambda panel: panel
    scene.local_group = Mock()
    scene._local_scale = 1.0
    scene._sphere_presence = 1.0
    scene._refresh_celestial_sphere = Mock()
    panel = scene.add_global_controls()

    panel.set_sphere_presence(1.75)

    assert scene._sphere_presence == 1.75
    scene._refresh_celestial_sphere.assert_called_once_with()
    scene.plotter.render.assert_called_once_with()

    scene.plotter.render.reset_mock()
    panel.set_local_scale(0.5)

    scene.local_group.set_scale.assert_called_once_with(0.5)
    scene.plotter.render.assert_called_once_with()


def test_scene_reset_camera_restores_canonical_view() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = make_plotter()
    scene._refresh_celestial_sphere = Mock()

    scene.reset_camera()

    assert scene.plotter.camera_position == [
        scene.canonical_camera.position,
        scene.canonical_camera.focal_point,
        scene.canonical_camera.view_up,
    ]
    assert (
        scene.plotter.camera.view_angle
        == scene.canonical_camera.view_angle
    )
    scene.plotter.camera.zoom.assert_not_called()
    scene._refresh_celestial_sphere.assert_called_once_with()
    scene.plotter.render.assert_called_once_with()


def test_global_panel_syncs_external_scene_changes() -> None:
    state = {
        "sphere": 1.0,
        "local": 1.0,
    }
    panel = GlobalControlPanel(
        plotter=make_plotter(),
        set_sphere_presence=Mock(),
        set_local_scale=Mock(),
        get_sphere_presence=lambda: state["sphere"],
        get_local_scale=lambda: state["local"],
    )
    panel.add()

    state["sphere"] = 2.25
    state["local"] = 0.4
    panel.sync_from_model()

    sphere_representation = (
        panel._sphere_widget.GetRepresentation()
    )
    local_representation = panel._local_widget.GetRepresentation()
    sphere_representation.SetValue.assert_any_call(2.25)
    local_representation.SetValue.assert_any_call(0.4)
