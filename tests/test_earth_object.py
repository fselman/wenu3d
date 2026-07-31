from unittest.mock import Mock, patch

import numpy as np
import pytest

from wenu3d import EarthObject


def make_earth(**overrides) -> EarthObject:
    arguments = {
        "name": "local_cartoon.earth",
        "radius": 0.25,
        "rotation_axis": np.array([0.0, 0.84, -0.54]),
        "observer_zenith": np.array([0.0, 0.0, 1.0]),
        "latitude_deg": -32.4524,
        "longitude_deg": -71.2311,
    }
    arguments.update(overrides)
    return EarthObject(**arguments)


def test_earth_object_build_owns_mesh_texture_and_actor() -> None:
    plotter = Mock()
    actor = plotter.add_mesh.return_value
    mesh = object()
    texture = object()
    earth = make_earth()

    with patch(
        "wenu3d.earth.realistic_earth",
        return_value=(mesh, texture),
    ) as realistic_earth:
        earth.build(plotter)

    realistic_earth.assert_called_once()
    arguments = realistic_earth.call_args
    assert arguments.args == (0.25,)
    np.testing.assert_allclose(
        arguments.kwargs["rotation_axis"],
        earth.rotation_axis,
    )
    np.testing.assert_allclose(
        arguments.kwargs["observer_zenith"],
        earth.observer_zenith,
    )
    assert arguments.kwargs["latitude_deg"] == -32.4524
    assert arguments.kwargs["longitude_deg"] == -71.2311
    plotter.add_mesh.assert_called_once_with(
        mesh,
        texture=texture,
        smooth_shading=True,
        ambient=0.28,
        diffuse=0.78,
        specular=0.10,
        specular_power=12.0,
    )
    assert earth.mesh is mesh
    assert earth.texture is texture
    assert earth.actors == [actor]
    assert earth.attached_plotter is plotter


def test_earth_object_rebuild_replaces_owned_actor() -> None:
    plotter = Mock()
    first_actor = Mock()
    second_actor = Mock()
    plotter.add_mesh.side_effect = [first_actor, second_actor]
    first_mesh, second_mesh = object(), object()
    first_texture, second_texture = object(), object()
    earth = make_earth()

    with patch(
        "wenu3d.earth.realistic_earth",
        side_effect=[
            (first_mesh, first_texture),
            (second_mesh, second_texture),
        ],
    ):
        earth.build(plotter)
        earth.build(plotter)

    plotter.remove_actor.assert_called_once_with(first_actor, render=False)
    assert earth.mesh is second_mesh
    assert earth.texture is second_texture
    assert earth.actors == [second_actor]


def test_earth_object_detach_releases_actor_mesh_and_texture() -> None:
    plotter = Mock()
    actor = plotter.add_mesh.return_value
    earth = make_earth()

    with patch(
        "wenu3d.earth.realistic_earth",
        return_value=(object(), object()),
    ):
        earth.build(plotter)

    earth.detach(render=False)

    plotter.remove_actor.assert_called_once_with(actor, render=False)
    assert earth.attached_plotter is None
    assert earth.actors == []
    assert earth.mesh is None
    assert earth.texture is None


@pytest.mark.parametrize("radius", [0.0, -1.0, np.inf, np.nan])
def test_earth_object_rejects_invalid_radius(radius: float) -> None:
    with pytest.raises(ValueError, match="radius"):
        make_earth(radius=radius)


@pytest.mark.parametrize("latitude_deg", [-90.0, 90.0, np.inf, np.nan])
def test_earth_object_characterizes_legacy_latitude_limit(
    latitude_deg: float,
) -> None:
    with pytest.raises(ValueError, match="latitude"):
        make_earth(latitude_deg=latitude_deg)


@pytest.mark.parametrize("longitude_deg", [np.inf, np.nan])
def test_earth_object_rejects_nonfinite_longitude(longitude_deg: float) -> None:
    with pytest.raises(ValueError, match="longitude"):
        make_earth(longitude_deg=longitude_deg)


@pytest.mark.parametrize(
    "rotation_axis",
    [np.zeros(3), np.array([0.0, np.nan, 1.0])],
)
def test_earth_object_rejects_invalid_rotation_axis(rotation_axis) -> None:
    with pytest.raises(ValueError):
        make_earth(rotation_axis=rotation_axis)
