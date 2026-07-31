from unittest.mock import Mock

import numpy as np

from wenu3d import CelestialShellObject
from wenu3d.scene import CelestialScene, SceneGraph
from wenu3d.style import SceneStyle


CAMERA_POSITION = (2.35, -2.70, 1.55)


def make_plotter() -> Mock:
    plotter = Mock()
    plotter.camera.position = CAMERA_POSITION
    plotter.iren.add_observer.return_value = 17
    return plotter


def make_legacy_shell_scene(plotter: Mock) -> CelestialScene:
    scene = object.__new__(CelestialScene)
    scene.sphere_radius = 1.0
    scene.style = SceneStyle()
    scene.plotter = plotter
    scene._closed = False
    return scene


def test_shell_object_build_owns_mesh_actor_and_observer() -> None:
    plotter = make_plotter()
    actor = plotter.add_mesh.return_value
    shell = CelestialShellObject(
        name="celestial_shell",
        radius=1.4,
    )

    shell.build(plotter)

    assert shell.attached_plotter is plotter
    assert shell.mesh is not None
    assert shell.actors == [actor]
    assert shell.camera_observer_id == 17
    plotter.add_mesh.assert_called_once_with(
        shell.mesh,
        scalars="celestial_sphere_rgba",
        rgba=True,
        smooth_shading=True,
        lighting=False,
        culling="back",
        interpolate_before_map=True,
    )
    event, callback = plotter.iren.add_observer.call_args.args
    assert event == "EndInteractionEvent"
    assert callable(callback)


def test_shell_object_material_matches_characterized_scene() -> None:
    legacy_plotter = make_plotter()
    legacy = make_legacy_shell_scene(legacy_plotter)
    legacy._add_celestial_shell()
    legacy._refresh_celestial_sphere()
    expected = legacy._sphere_mesh.point_data[
        legacy._sphere_rgba_name
    ]

    object_plotter = make_plotter()
    shell = CelestialShellObject(
        name="celestial_shell",
        radius=1.0,
        style=legacy.style,
    )
    shell.build(object_plotter)
    shell.refresh()

    actual = shell.mesh.point_data["celestial_sphere_rgba"]
    np.testing.assert_array_equal(actual, expected)


def test_shell_object_presence_refreshes_and_renders_once() -> None:
    plotter = make_plotter()
    shell = CelestialShellObject(name="celestial_shell")
    shell.build(plotter)
    plotter.reset_mock()
    plotter.camera.position = CAMERA_POSITION

    shell.set_presence(0.0)

    rgba = shell.mesh.point_data["celestial_sphere_rgba"]
    assert shell.presence == 0.0
    assert np.all(rgba[:, 3] == 0)
    plotter.render.assert_called_once_with()


def test_shell_object_rebuild_replaces_actor_and_observer() -> None:
    plotter = make_plotter()
    first_actor = Mock()
    second_actor = Mock()
    plotter.add_mesh.side_effect = [first_actor, second_actor]
    plotter.iren.add_observer.side_effect = [11, 12]
    shell = CelestialShellObject(name="celestial_shell")

    shell.build(plotter)
    shell.build(plotter)

    plotter.remove_actor.assert_called_once_with(
        first_actor,
        render=False,
    )
    plotter.iren.remove_observer.assert_called_once_with(11)
    assert shell.actors == [second_actor]
    assert shell.camera_observer_id == 12
    assert plotter.add_mesh.call_count == 2


def test_shell_object_detach_releases_actor_and_observer() -> None:
    plotter = make_plotter()
    actor = plotter.add_mesh.return_value
    shell = CelestialShellObject(name="celestial_shell")
    shell.build(plotter)

    shell.detach(render=False)

    plotter.iren.remove_observer.assert_called_once_with(17)
    plotter.remove_actor.assert_called_once_with(actor, render=False)
    assert shell.attached_plotter is None
    assert shell.mesh is None
    assert shell.actors == []
    assert shell.camera_observer_id is None


def test_detached_shell_callback_does_not_render() -> None:
    plotter = make_plotter()
    shell = CelestialShellObject(name="celestial_shell")
    shell.build(plotter)
    callback = shell._camera_callback
    shell.detach(render=False)
    plotter.reset_mock()

    callback()

    plotter.render.assert_not_called()


def test_shell_object_builds_without_camera_interactor() -> None:
    plotter = make_plotter()
    plotter.iren = None
    shell = CelestialShellObject(name="celestial_shell")

    shell.build(plotter)

    assert shell.attached_plotter is plotter
    assert shell.camera_observer_id is None


def test_scene_adds_shell_as_named_layer() -> None:
    scene = object.__new__(CelestialScene)
    scene.sphere_radius = 1.4
    scene.style = SceneStyle()
    scene.plotter = make_plotter()
    scene.graph = SceneGraph()

    scene._add_celestial_shell_layer()

    layer = scene.graph.get("celestial_shell")
    assert layer.get("celestial_shell.surface") is scene.shell
    assert scene.shell.radius == 1.4
    assert scene.shell.attached_plotter is scene.plotter
