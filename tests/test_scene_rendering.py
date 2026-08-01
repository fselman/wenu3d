from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import patch

import numpy as np
import pytest

from wenu3d import CameraState
from wenu3d.scene import CelestialScene


def make_scene() -> CelestialScene:
    scene = object.__new__(CelestialScene)
    scene.location_name = "La Ligua"
    scene.title = "Celestial grids — La Ligua"
    scene.style = Mock()
    scene.style.text_color = "#202020"
    scene.plotter = Mock()
    scene.plotter.add_text.return_value = object()
    scene.controls = Mock()
    scene.shell = Mock()
    scene._title_actor = None
    scene._closed = False
    return scene


def test_render_updates_scene_with_exactly_one_plotter_render() -> None:
    scene = make_scene()

    scene.render()

    scene.controls.sync.assert_called_once_with(render=False)
    scene.shell.refresh.assert_called_once_with()
    scene.plotter.render.assert_called_once_with()


def test_repeated_render_does_not_duplicate_title() -> None:
    scene = make_scene()

    scene.render()
    scene.render()

    scene.plotter.add_text.assert_called_once_with(
        "Celestial grids — La Ligua",
        position="upper_left",
        font_size=18,
        color="#202020",
    )
    assert scene.plotter.render.call_count == 2


def test_explicit_scene_title_replaces_grid_specific_default() -> None:
    scene = make_scene()
    scene.title = "Two observers and one star"

    scene.render()

    scene.plotter.add_text.assert_called_once_with(
        "Two observers and one star",
        position="upper_left",
        font_size=18,
        color="#202020",
    )


def test_render_does_not_rebuild_scene_graph_layers() -> None:
    scene = make_scene()
    layer = Mock()
    scene.graph = [layer]

    scene.render()

    layer.build.assert_not_called()


def test_show_uses_render_path_before_interaction() -> None:
    scene = make_scene()
    scene.render = Mock()

    scene.show(screenshot="scene.png")

    scene.render.assert_called_once_with()
    scene.plotter.show.assert_called_once_with(
        screenshot="scene.png",
        auto_close=False,
    )


def test_scene_configures_plotter_for_off_screen_rendering() -> None:
    with (
        patch("wenu3d.scene.pv.Plotter") as plotter_class,
        patch.object(CelestialScene, "_build_base_scene"),
    ):
        CelestialScene(
            latitude_deg=-32.45,
            longitude_deg=-71.23,
            location_name="La Ligua",
            window_size=(1200, 800),
            off_screen=True,
        )

    plotter_class.assert_called_once_with(
        window_size=(1200, 800),
        off_screen=True,
    )


def test_save_renders_opaque_image_at_configured_size() -> None:
    scene = make_scene()
    scene.render = Mock()
    scene.set_camera = Mock()
    image = np.zeros((800, 1200, 3), dtype=np.uint8)
    scene.plotter.screenshot.return_value = image
    output = Path("illustration.png")

    result = scene.save(output)

    scene.render.assert_called_once_with()
    scene.set_camera.assert_not_called()
    scene.plotter.screenshot.assert_called_once_with(
        filename=output,
        transparent_background=False,
        return_img=True,
    )
    assert result is image


def test_save_applies_explicit_camera_before_rendering() -> None:
    scene = make_scene()
    scene.set_camera = Mock()
    scene.render = Mock()
    scene.plotter.screenshot.return_value = np.zeros(
        (2, 3, 3),
        dtype=np.uint8,
    )
    state = CameraState(
        position=(3.0, -2.0, 1.0),
        focal_point=(0.0, 0.0, 0.0),
        view_up=(0.0, 0.0, 1.0),
    )

    scene.save("camera.png", camera_state=state)

    scene.set_camera.assert_called_once_with(
        state,
        render=False,
    )
    scene.render.assert_called_once_with()


def test_save_supports_export_dimensions_and_transparency() -> None:
    scene = make_scene()
    scene.render = Mock()
    image = np.zeros((800, 1200, 4), dtype=np.uint8)
    scene.plotter.screenshot.return_value = image
    output = Path("transparent.png")

    result = scene.save(
        output,
        window_size=(1200, 800),
        transparent_background=True,
    )

    scene.render.assert_called_once_with()
    scene.plotter.screenshot.assert_called_once_with(
        filename=output,
        transparent_background=True,
        return_img=True,
        window_size=(1200, 800),
    )
    assert result is image


def test_repeated_save_reuses_scene_content() -> None:
    scene = make_scene()
    scene.plotter.screenshot.return_value = np.zeros(
        (2, 3, 3),
        dtype=np.uint8,
    )

    scene.save("first.png")
    scene.save("second.png")

    scene.plotter.add_text.assert_called_once()
    assert scene.plotter.screenshot.call_count == 2


def test_sphere_frame_export_validates_size_and_padding() -> None:
    scene = make_scene()

    with pytest.raises(ValueError, match="size"):
        scene.save_sphere_frame("sphere.png", size=0)
    with pytest.raises(ValueError, match="padding"):
        scene.save_sphere_frame("sphere.png", padding=0.5)


def test_sphere_frame_export_hides_ui_and_restores_scene() -> None:
    scene = make_scene()
    scene.sphere_radius = 1.0
    scene.plotter.window_size = (1800, 1200)
    scene.controls.hidden.return_value = nullcontext()
    scene.save = Mock(return_value=np.zeros((1200, 1200, 3), dtype=np.uint8))
    scene.set_camera = Mock()
    scene.render = Mock()
    scene._title_actor = Mock()
    scene._title_actor.GetVisibility.return_value = 1
    scene.plotter.camera.parallel_projection = False
    scene.plotter.camera.position = (0.0, 0.0, 4.0)

    with patch.object(
        CelestialScene,
        "camera_state",
        new_callable=PropertyMock,
        return_value=Mock(),
    ):
        image = scene.save_sphere_frame("sphere.png", size=1200, padding=0.04)

    assert image.shape == (1200, 1200, 3)
    scene.controls.hidden.assert_called_once_with()
    scene.plotter.reset_camera.assert_called_once_with(
        render=False,
        bounds=(-1.0, 1.0) * 3,
    )
    expected_angle = np.degrees(
        2.0 * np.arcsin(1.0 / 4.0)
    ) / 0.92
    assert scene.plotter.camera.view_angle == pytest.approx(expected_angle)
    scene.plotter.camera.zoom.assert_not_called()
    scene.save.assert_called_once_with("sphere.png", transparent_background=False)
    assert scene.plotter.window_size == (1800, 1200)


def test_close_releases_scene_resources() -> None:
    scene = make_scene()
    scene.graph = Mock()

    scene.close()

    scene.graph.clear.assert_called_once_with(render=False)
    scene.plotter.close.assert_called_once_with()
    assert scene._closed is True


def test_repeated_close_is_idempotent() -> None:
    scene = make_scene()
    scene.graph = Mock()

    scene.close()
    scene.close()

    scene.graph.clear.assert_called_once_with(render=False)
    scene.plotter.close.assert_called_once_with()
