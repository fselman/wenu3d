from unittest.mock import Mock, call, patch

import numpy as np
import pytest

from wenu3d.earth import orient_earth_to_observer
from wenu3d.frames import equatorial_frame, horizontal_frame
from wenu3d.observer import add_observer
from wenu3d.scene import CelestialScene


def source_sphere_point(latitude_deg: float, longitude_deg: float) -> np.ndarray:
    latitude = np.deg2rad(latitude_deg)
    longitude = np.deg2rad(longitude_deg)
    return np.array([
        np.cos(latitude) * np.cos(longitude),
        np.cos(latitude) * np.sin(longitude),
        np.sin(latitude),
    ])


def mesh_with_points(*points: np.ndarray) -> Mock:
    result = Mock()
    result.points = np.asarray(points, dtype=float)
    mesh = Mock()
    mesh.copy.return_value = result
    return mesh


def make_local_scene() -> CelestialScene:
    scene = object.__new__(CelestialScene)
    scene.latitude_deg = -32.4524
    scene.longitude_deg = -71.2311
    scene.earth_radius = 0.25
    scene.sphere_radius = 1.0
    scene.horizontal = horizontal_frame()
    scene.equatorial = equatorial_frame(scene.latitude_deg)
    scene.style = Mock(plane_color="#d8d2c4")
    scene.plotter = Mock()
    scene.local_group = Mock()
    return scene


def test_earth_orientation_places_corrected_site_at_fixed_zenith() -> None:
    latitude_deg = -32.4524
    longitude_deg = -71.2311
    correction_deg = 180.0
    zenith = np.array([0.0, 0.0, 1.0])
    rotation_axis = equatorial_frame(latitude_deg).pole
    site = source_sphere_point(
        latitude_deg,
        longitude_deg + correction_deg,
    )
    north_pole = np.array([0.0, 0.0, 1.0])
    mesh = mesh_with_points(site, north_pole)

    result = orient_earth_to_observer(
        mesh,
        rotation_axis=rotation_axis,
        observer_zenith=zenith,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
    )

    mesh.copy.assert_called_once_with(deep=True)
    np.testing.assert_allclose(result.points[0], zenith, atol=1e-12)
    np.testing.assert_allclose(result.points[1], rotation_axis, atol=1e-12)


def test_current_earth_orientation_is_singular_at_geographic_pole() -> None:
    mesh = mesh_with_points(np.array([1.0, 0.0, 0.0]))
    pole = np.array([0.0, 0.0, 1.0])

    with pytest.raises(ValueError, match="zero vector"):
        orient_earth_to_observer(
            mesh,
            rotation_axis=pole,
            observer_zenith=pole,
            latitude_deg=90.0,
            longitude_deg=0.0,
        )


def test_current_local_composition_uses_fixed_frame_and_raw_actors() -> None:
    scene = make_local_scene()
    earth = object()
    texture = object()
    platform = object()
    arrows = [object() for _ in range(4)]
    observer_actors = [object() for _ in range(7)]

    with (
        patch(
            "wenu3d.scene.realistic_earth",
            return_value=(earth, texture),
        ) as realistic_earth,
        patch(
            "wenu3d.scene.tangent_plane",
            return_value=platform,
        ) as tangent_plane,
        patch(
            "wenu3d.scene.add_arrow",
            side_effect=arrows,
        ) as add_arrow,
        patch(
            "wenu3d.scene.add_observer",
            return_value=observer_actors,
        ) as add_observer,
    ):
        scene._add_earth_and_observer()

    zenith = np.array([0.0, 0.0, 1.0])
    east = np.array([1.0, 0.0, 0.0])
    north = np.array([0.0, 1.0, 0.0])
    platform_center = 0.262 * zenith

    assert realistic_earth.call_count == 1
    earth_arguments = realistic_earth.call_args
    assert earth_arguments.args == (0.25,)
    np.testing.assert_allclose(
        earth_arguments.kwargs["rotation_axis"],
        scene.equatorial.pole,
    )
    np.testing.assert_allclose(
        earth_arguments.kwargs["observer_zenith"],
        zenith,
    )
    assert earth_arguments.kwargs["latitude_deg"] == -32.4524
    assert earth_arguments.kwargs["longitude_deg"] == -71.2311
    tangent_plane.assert_called_once()
    arguments = tangent_plane.call_args
    np.testing.assert_allclose(arguments.args[0], platform_center)
    np.testing.assert_allclose(arguments.args[1], east)
    np.testing.assert_allclose(arguments.args[2], north)
    assert arguments.kwargs == {"width": 0.4625, "depth": 0.3}

    expected_directions = (east, -east, north, -north)
    assert add_arrow.call_count == 4
    for actual, direction in zip(
        add_arrow.call_args_list,
        expected_directions,
    ):
        assert actual.args[0] is scene.plotter
        np.testing.assert_allclose(actual.args[1], platform_center)
        np.testing.assert_allclose(actual.args[2], direction)
        assert actual.kwargs == {"scale": 0.07, "color": "#59645d"}

    add_observer.assert_called_once()
    observer_arguments = add_observer.call_args
    np.testing.assert_allclose(
        observer_arguments.kwargs["base"],
        platform_center - 0.0125 * north,
    )
    np.testing.assert_allclose(observer_arguments.kwargs["zenith"], zenith)
    np.testing.assert_allclose(observer_arguments.kwargs["east"], east)
    assert observer_arguments.kwargs["height"] == pytest.approx(0.23)

    assert scene.plotter.add_mesh.call_args_list == [
        call(
            earth,
            texture=texture,
            smooth_shading=True,
            ambient=0.28,
            diffuse=0.78,
            specular=0.10,
            specular_power=12,
        ),
        call(
            platform,
            color="#d8d2c4",
            opacity=0.52,
            show_edges=True,
            edge_color="#777777",
        ),
    ]
    assert scene.local_group.add.call_count == 6
    scene.local_group.extend.assert_called_once_with(observer_actors)


def test_current_stick_figure_builds_seven_raw_actors() -> None:
    plotter = Mock()
    tube_actors = [object() for _ in range(6)]
    head_mesh = object()
    head_actor = object()
    plotter.add_mesh.return_value = head_actor

    with (
        patch(
            "wenu3d.observer.add_tube",
            side_effect=tube_actors,
        ) as add_tube,
        patch(
            "wenu3d.observer.pv.Sphere",
            return_value=head_mesh,
        ) as sphere,
    ):
        actors = add_observer(
            plotter,
            base=np.array([0.0, 0.0, 0.25]),
            zenith=np.array([0.0, 0.0, 1.0]),
            east=np.array([1.0, 0.0, 0.0]),
            height=0.23,
        )

    assert add_tube.call_count == 6
    sphere.assert_called_once()
    plotter.add_mesh.assert_called_once_with(
        head_mesh,
        color="#d4af8a",
        smooth_shading=True,
    )
    assert actors == tube_actors + [head_actor]


def test_current_celestial_axis_is_not_in_local_scale_group() -> None:
    scene = make_local_scene()

    with patch("wenu3d.scene.add_tube") as add_tube:
        scene._add_axis()

    add_tube.assert_called_once()
    points = add_tube.call_args.args[1]
    np.testing.assert_allclose(points[0], -1.10 * scene.equatorial.pole)
    np.testing.assert_allclose(points[1], 1.10 * scene.equatorial.pole)
    scene.local_group.add.assert_not_called()
    scene.local_group.extend.assert_not_called()


def test_current_local_scale_does_not_modify_centered_grid_model() -> None:
    scene = make_local_scene()
    scene._local_scale = 1.0
    grid_before = scene.make_horizontal_grid(name="before")

    scene._set_local_scale(0.35)
    grid_after = scene.make_horizontal_grid(name="after")

    scene.local_group.set_scale.assert_called_once_with(0.35)
    scene.plotter.render.assert_called_once_with()
    assert scene._local_scale == 0.35
    assert grid_before.radius == pytest.approx(0.992)
    assert grid_after.radius == pytest.approx(0.992)
    np.testing.assert_allclose(grid_before.frame.pole, [0.0, 0.0, 1.0])
    np.testing.assert_allclose(grid_after.frame.pole, [0.0, 0.0, 1.0])
