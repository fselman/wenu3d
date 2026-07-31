from unittest.mock import Mock
from unittest.mock import patch

import numpy as np
import pyvista as pv

from wenu3d.scene import CelestialScene
from wenu3d.style import SceneStyle


def make_shell_scene(*, radius: float = 1.0) -> CelestialScene:
    scene = object.__new__(CelestialScene)
    scene.sphere_radius = radius
    scene.style = SceneStyle()
    scene.plotter = Mock()
    scene.plotter.add_mesh.return_value = Mock()
    scene._closed = False
    return scene


def test_shell_construction_preserves_mesh_and_actor_configuration() -> None:
    scene = make_shell_scene(radius=1.7)

    with patch("wenu3d.scene.pv.Sphere", wraps=pv.Sphere) as sphere:
        scene._add_celestial_shell()

    sphere.assert_called_once_with(
        radius=1.7,
        theta_resolution=360,
        phi_resolution=180,
    )
    assert scene._sphere_mesh is not None
    assert "Normals" in scene._sphere_mesh.point_data
    rgba = scene._sphere_mesh.point_data[scene._sphere_rgba_name]
    assert rgba.shape == (scene._sphere_mesh.n_points, 4)
    assert rgba.dtype == np.uint8
    assert np.count_nonzero(rgba) == 0
    assert scene._sphere_presence == 1.0
    assert scene.sphere_actor is scene.plotter.add_mesh.return_value
    scene.plotter.add_mesh.assert_called_once_with(
        scene._sphere_mesh,
        scalars="celestial_sphere_rgba",
        rgba=True,
        smooth_shading=True,
        lighting=False,
        culling="back",
        interpolate_before_map=True,
    )


def test_shell_material_refresh_is_camera_dependent() -> None:
    scene = make_shell_scene()
    scene._add_celestial_shell()

    scene.plotter.camera.position = (2.35, -2.70, 1.55)
    scene._refresh_celestial_sphere()
    first = scene._sphere_mesh.point_data[
        scene._sphere_rgba_name
    ].copy()

    scene.plotter.camera.position = (-2.35, 2.70, 1.55)
    scene._refresh_celestial_sphere()
    second = scene._sphere_mesh.point_data[
        scene._sphere_rgba_name
    ].copy()

    assert first.dtype == np.uint8
    assert first.shape == (scene._sphere_mesh.n_points, 4)
    assert np.any(first[:, 3] > 0)
    assert not np.array_equal(first, second)


def test_zero_shell_presence_makes_material_fully_transparent() -> None:
    scene = make_shell_scene()
    scene._add_celestial_shell()
    scene.plotter.camera.position = (2.35, -2.70, 1.55)

    scene._sphere_presence = 0.0
    scene._refresh_celestial_sphere()

    rgba = scene._sphere_mesh.point_data[scene._sphere_rgba_name]
    assert np.all(rgba[:, 3] == 0)
    assert np.any(rgba[:, :3] > 0)


def test_shell_camera_callback_refreshes_material_and_renders() -> None:
    scene = make_shell_scene()
    scene._refresh_celestial_sphere = Mock()
    scene.plotter.iren.add_observer.return_value = 23

    scene._install_sphere_camera_observer()

    event, callback = scene.plotter.iren.add_observer.call_args.args
    assert event == "EndInteractionEvent"
    assert callback is scene._sphere_camera_callback
    assert scene._sphere_camera_observer_id == 23

    callback()

    scene._refresh_celestial_sphere.assert_called_once_with()
    scene.plotter.render.assert_called_once_with()


def test_shell_camera_callback_ignores_events_after_close() -> None:
    scene = make_shell_scene()
    scene._refresh_celestial_sphere = Mock()
    scene.plotter.iren.add_observer.return_value = 23
    scene._install_sphere_camera_observer()
    callback = scene._sphere_camera_callback

    scene._closed = True
    callback()

    scene._refresh_celestial_sphere.assert_not_called()
    scene.plotter.render.assert_not_called()


def test_shell_camera_observer_is_optional_without_interactor() -> None:
    scene = make_shell_scene()
    scene.plotter.iren = None

    scene._install_sphere_camera_observer()

    assert scene._sphere_camera_observer_id is None
