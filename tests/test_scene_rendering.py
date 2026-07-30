from unittest.mock import Mock

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
