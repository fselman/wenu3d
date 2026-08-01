from unittest.mock import Mock
from unittest.mock import patch

import numpy as np
import pyvista as pv
import pytest

from wenu3d import CelestialShellObject
from wenu3d.style import SceneStyle


def make_plotter() -> Mock:
    plotter = Mock()
    plotter.camera.position = (2.35, -2.70, 1.55)
    plotter.iren.add_observer.return_value = 23
    return plotter


def make_shell(*, radius: float = 1.0) -> CelestialShellObject:
    return CelestialShellObject(
        name="celestial_shell",
        radius=radius,
        style=SceneStyle(),
    )


def test_shell_construction_preserves_mesh_and_actor_configuration() -> None:
    plotter = make_plotter()
    shell = make_shell(radius=1.7)

    with patch("wenu3d.shell.pv.Sphere", wraps=pv.Sphere) as sphere:
        shell.build(plotter)

    sphere.assert_called_once_with(
        radius=1.7,
        theta_resolution=360,
        phi_resolution=180,
    )
    assert shell.mesh is not None
    assert "Normals" in shell.mesh.point_data
    rgba = shell.mesh.point_data["celestial_sphere_rgba"]
    assert rgba.shape == (shell.mesh.n_points, 4)
    assert rgba.dtype == np.uint8
    assert np.count_nonzero(rgba) == 0
    assert shell.presence == 1.0
    assert shell.actors == [plotter.add_mesh.return_value]
    plotter.add_mesh.assert_called_once_with(
        shell.mesh,
        scalars="celestial_sphere_rgba",
        rgba=True,
        smooth_shading=True,
        lighting=False,
        culling="back",
        interpolate_before_map=True,
    )


def test_shell_material_refresh_is_camera_dependent() -> None:
    plotter = make_plotter()
    shell = make_shell()
    shell.build(plotter)

    shell.refresh()
    first = shell.mesh.point_data["celestial_sphere_rgba"].copy()

    plotter.camera.position = (-2.35, 2.70, 1.55)
    shell.refresh()
    second = shell.mesh.point_data["celestial_sphere_rgba"].copy()

    assert first.dtype == np.uint8
    assert first.shape == (shell.mesh.n_points, 4)
    assert np.any(first[:, 3] > 0)
    assert not np.array_equal(first, second)


def test_default_shell_material_has_broad_translucent_depth_cues() -> None:
    style = SceneStyle()

    assert style.sphere_center_opacity == pytest.approx(0.030)
    assert style.sphere_rim_opacity == pytest.approx(0.46)
    assert style.sphere_limb_power == pytest.approx(0.80)
    assert style.sphere_directional_strength == pytest.approx(0.18)
    assert style.sphere_specular_power == pytest.approx(42.0)
    assert style.sphere_secondary_specular_power == pytest.approx(22.0)

    plotter = make_plotter()
    shell = make_shell()
    shell.build(plotter)
    shell.refresh()
    alpha = shell.mesh.point_data["celestial_sphere_rgba"][:, 3]

    assert np.ptp(alpha.astype(int)) > 80
    assert 0 < np.median(alpha) < np.max(alpha)


def test_directional_shell_shading_changes_rgb_without_changing_alpha() -> None:
    plotter = make_plotter()
    directional = CelestialShellObject(
        name="directional",
        style=SceneStyle(sphere_directional_strength=0.18),
    )
    symmetric = CelestialShellObject(
        name="symmetric",
        style=SceneStyle(sphere_directional_strength=0.0),
    )

    directional.build(plotter)
    directional.refresh()
    symmetric.build(plotter)
    symmetric.refresh()
    directional_rgba = directional.mesh.point_data["celestial_sphere_rgba"]
    symmetric_rgba = symmetric.mesh.point_data["celestial_sphere_rgba"]

    assert not np.array_equal(directional_rgba[:, :3], symmetric_rgba[:, :3])
    np.testing.assert_array_equal(directional_rgba[:, 3], symmetric_rgba[:, 3])


def test_zero_shell_presence_makes_material_fully_transparent() -> None:
    plotter = make_plotter()
    shell = make_shell()
    shell.build(plotter)

    shell.set_presence(0.0, render=False)

    rgba = shell.mesh.point_data["celestial_sphere_rgba"]
    assert np.all(rgba[:, 3] == 0)
    assert np.any(rgba[:, :3] > 0)
    plotter.render.assert_not_called()


def test_shell_camera_callback_refreshes_material_and_renders() -> None:
    plotter = make_plotter()
    shell = make_shell()
    shell.refresh = Mock()
    shell.build(plotter)
    callback = shell._camera_callback

    callback()

    shell.refresh.assert_called_once_with()
    plotter.render.assert_called_once_with()


def test_detached_shell_camera_callback_ignores_events() -> None:
    plotter = make_plotter()
    shell = make_shell()
    shell.build(plotter)
    callback = shell._camera_callback
    shell.detach(render=False)
    shell.refresh = Mock()
    plotter.reset_mock()

    callback()

    shell.refresh.assert_not_called()
    plotter.render.assert_not_called()


def test_shell_camera_observer_is_optional_without_interactor() -> None:
    plotter = make_plotter()
    plotter.iren = None
    shell = make_shell()

    shell.build(plotter)

    assert shell.camera_observer_id is None
