from unittest.mock import Mock, call, patch

import numpy as np
import pytest

from wenu3d.earth import orient_earth_to_observer
from wenu3d.frames import equatorial_frame, horizontal_frame
from wenu3d.observer import (
    ObserverComposition,
    StickFigureRepresentation,
    add_observer,
)
from wenu3d.scene import CelestialScene, SceneGraph
from wenu3d.transforms import LocalCartoonTransform


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
    scene.graph = SceneGraph()
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


def test_current_local_composition_uses_fixed_frame_and_graph_objects() -> None:
    scene = make_local_scene()
    earth = object()
    texture = object()
    head_mesh = object()
    arrows = [Mock() for _ in range(4)]
    observer_actors = [Mock() for _ in range(7)]

    with (
        patch(
            "wenu3d.earth.realistic_earth",
            return_value=(earth, texture),
        ) as realistic_earth,
        patch(
            "wenu3d.vector_object.add_arrow",
            side_effect=arrows,
        ) as add_arrow,
        patch(
            "wenu3d.observer.add_tube",
            side_effect=observer_actors[:6],
        ),
        patch(
            "wenu3d.observer.pv.Sphere",
            return_value=head_mesh,
        ),
    ):
        scene.plotter.add_mesh.side_effect = [
            Mock(),
            Mock(),
            observer_actors[6],
        ]
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
    np.testing.assert_allclose(scene.platform.surface.center, platform_center)
    np.testing.assert_allclose(scene.platform.surface.normal, zenith)
    np.testing.assert_allclose(scene.platform.surface.axis_u, east)
    np.testing.assert_allclose(scene.platform.surface.axis_v, north)
    assert scene.platform.surface.width == pytest.approx(0.4625)
    assert scene.platform.surface.height == pytest.approx(0.3)

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

    assert scene.observer.position.shape == (3,)
    np.testing.assert_allclose(
        scene.observer.position,
        platform_center - 0.0125 * north,
    )
    np.testing.assert_allclose(scene.observer.frame.pole, zenith)
    np.testing.assert_allclose(scene.observer.frame.east, east)
    assert isinstance(scene.observer_composition, ObserverComposition)
    assert isinstance(
        scene.observer_representation,
        StickFigureRepresentation,
    )
    assert scene.observer_representation.observer is scene.observer
    assert scene.observer_representation.height == pytest.approx(0.23)
    assert scene.ideal_horizon is scene.observer_composition.ideal_horizon
    np.testing.assert_allclose(scene.ideal_horizon.origin, [0.0, 0.0, 0.0])
    np.testing.assert_allclose(scene.ideal_horizon.normal, zenith)
    assert not np.allclose(scene.ideal_horizon.origin, scene.platform.surface.center)

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
            scene.platform.mesh,
            color="#d8d2c4",
            opacity=0.52,
            show_edges=True,
            edge_color="#777777",
            line_width=1.0,
            name="local_cartoon.platform",
            render=False,
        ),
        call(
            head_mesh,
            color="#d4af8a",
            smooth_shading=True,
        ),
    ]
    local_cartoon = scene.local_cartoon
    assert scene.graph.get("local_cartoon") is local_cartoon
    assert local_cartoon.get("local_cartoon.earth") is scene.earth
    assert local_cartoon.objects == [scene.earth, scene.observer_composition]
    assert local_cartoon.observer_compositions == (
        scene.observer_composition,
    )
    assert (
        local_cartoon.get_observer("canonical_observer")
        is scene.observer_composition
    )
    assert (
        scene.local_platform.get("local_cartoon.platform")
        is scene.platform
    )
    assert scene.observer_composition.context_objects == (scene.local_platform,)
    assert scene.observer_composition.objects == [
        scene.local_platform,
        scene.observer_representation,
    ]
    assert scene.local_platform.surface is scene.platform
    assert scene.local_platform.decoration is scene.platform_decoration
    assert scene.local_platform.objects == [
        scene.platform,
        scene.platform_decoration,
    ]
    assert scene.platform_decoration.vectors == scene.cardinal_vectors
    assert scene.platform_decoration.objects == list(scene.cardinal_vectors)
    assert scene.earth.attached_plotter is scene.plotter
    assert local_cartoon.actors[-7:] == observer_actors
    assert local_cartoon.transform.scale == 1.0
    np.testing.assert_allclose(
        local_cartoon.observer_anchor("canonical_observer", "feet"),
        scene.observer.position,
    )


def test_current_stick_figure_builds_seven_raw_actors() -> None:
    plotter = Mock()
    tube_actors = [Mock() for _ in range(6)]
    head_mesh = object()
    head_actor = Mock()
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


def test_current_celestial_axis_remains_outside_local_cartoon() -> None:
    scene = make_local_scene()

    with patch("wenu3d.scene.add_tube") as add_tube:
        scene._add_axis()

    add_tube.assert_called_once()
    points = add_tube.call_args.args[1]
    np.testing.assert_allclose(points[0], -1.10 * scene.equatorial.pole)
    np.testing.assert_allclose(points[1], 1.10 * scene.equatorial.pole)
    assert len(scene.graph) == 0


def test_current_local_scale_does_not_modify_centered_grid_model() -> None:
    scene = make_local_scene()
    scene._local_scale = 1.0
    scene.local_cartoon = Mock()
    scene.local_cartoon.transform = LocalCartoonTransform(
        translation=(0.1, 0.2, 0.3),
    )
    grid_before = scene.make_horizontal_grid(name="before")

    scene._set_local_scale(0.35)
    grid_after = scene.make_horizontal_grid(name="after")

    transform = scene.local_cartoon.set_transform.call_args.args[0]
    assert transform.translation == (0.1, 0.2, 0.3)
    assert transform.scale == 0.35
    scene.plotter.render.assert_not_called()
    assert scene._local_scale == 0.35
    assert grid_before.radius == pytest.approx(0.992)
    assert grid_after.radius == pytest.approx(0.992)
    np.testing.assert_allclose(grid_before.frame.pole, [0.0, 0.0, 1.0])
    np.testing.assert_allclose(grid_after.frame.pole, [0.0, 0.0, 1.0])
