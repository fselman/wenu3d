from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import numpy as np

from wenu3d import CameraState
from wenu3d.scene import CelestialScene


def make_scene() -> CelestialScene:
    scene = object.__new__(CelestialScene)
    scene.location_name = "La Ligua"
    scene.style = Mock()
    scene.style.text_color = "#202020"
    scene.plotter = Mock()
    scene.plotter.add_text.return_value = object()
    scene.controls = Mock()
    scene._refresh_celestial_sphere = Mock()
    scene._title_actor = None
    scene._closed = False
    scene._sphere_camera_observer_id = 17
    return scene


def test_render_updates_scene_with_exactly_one_plotter_render() -> None:
    scene = make_scene()

    scene.render()

    scene.controls.sync.assert_called_once_with(render=False)
    scene._refresh_celestial_sphere.assert_called_once_with()
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
    image = np.zeros((800, 1200, 3), dtype=np.uint8)
    scene.plotter.screenshot.return_value = image
    output = Path("illustration.png")

    result = scene.save(output)

    scene.render.assert_called_once_with()
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


def test_close_releases_scene_resources() -> None:
    scene = make_scene()
    scene.graph = Mock()

    scene.close()

    scene.plotter.iren.remove_observer.assert_called_once_with(17)
    scene.graph.clear.assert_called_once_with(render=False)
    scene.plotter.close.assert_called_once_with()
    assert scene._sphere_camera_observer_id is None
    assert scene._closed is True


def test_repeated_close_is_idempotent() -> None:
    scene = make_scene()
    scene.graph = Mock()

    scene.close()
    scene.close()

    scene.plotter.iren.remove_observer.assert_called_once_with(17)
    scene.graph.clear.assert_called_once_with(render=False)
    scene.plotter.close.assert_called_once_with()


def test_close_without_camera_observer_still_releases_resources() -> None:
    scene = make_scene()
    scene.graph = Mock()
    scene._sphere_camera_observer_id = None

    scene.close()

    scene.plotter.iren.remove_observer.assert_not_called()
    scene.graph.clear.assert_called_once_with(render=False)
    scene.plotter.close.assert_called_once_with()


def test_sphere_camera_callback_does_nothing_after_close() -> None:
    scene = make_scene()
    scene._install_sphere_camera_observer()
    callback = scene._sphere_camera_callback
    scene._closed = True

    callback()

    scene._refresh_celestial_sphere.assert_not_called()
    scene.plotter.render.assert_not_called()
