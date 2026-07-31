import numpy as np
import pyvista as pv
import pytest

from wenu3d import Marker, MarkerObject, MarkerStyle


def test_marker_object_requires_marker() -> None:
    with pytest.raises(TypeError, match="Marker"):
        MarkerObject(name="invalid")


def test_sphere_marker_builds_at_finite_position() -> None:
    plotter = pv.Plotter(off_screen=True)
    marker = Marker(
        position=(1.0, -2.0, 0.5),
        style=MarkerStyle(
            shape="sphere",
            color="gold",
            radius=0.2,
            opacity=0.65,
        ),
    )
    obj = MarkerObject(name="marker.sphere", marker=marker)

    try:
        obj.build(plotter)

        assert obj.attached_plotter is plotter
        assert obj.mesh is not None
        assert obj.actors == [plotter.renderer.actors[obj.name]]
        np.testing.assert_allclose(obj.mesh.center, marker.position)
        np.testing.assert_allclose(
            np.asarray(obj.mesh.bounds).reshape(3, 2),
            (
                (0.8, 1.2),
                (-2.2, -1.8),
                (0.3, 0.7),
            ),
            atol=5e-4,
        )
        assert obj.actors[0].GetProperty().GetOpacity() == 0.65
    finally:
        plotter.close()


def test_star_marker_is_camera_independent_finite_geometry() -> None:
    plotter = pv.Plotter(off_screen=True)
    position = np.array((0.4, -0.3, 1.2))
    radius = 0.25
    obj = MarkerObject(
        name="marker.star",
        marker=Marker(
            position=position,
            style=MarkerStyle(
                shape="star",
                color="#d4a72c",
                radius=radius,
            ),
        ),
    )

    try:
        obj.build(plotter)

        distances = np.linalg.norm(obj.mesh.points - position, axis=1)
        assert obj.mesh.n_points == 14
        assert obj.mesh.n_cells == 24
        assert np.count_nonzero(np.isclose(distances, radius)) == 8
        assert "Normals" in obj.mesh.point_data
    finally:
        plotter.close()


def test_marker_visibility_comes_from_marker_record() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = MarkerObject(
        name="marker.hidden",
        marker=Marker(
            position=(0.0, 0.0, 0.0),
            visible=False,
        ),
    )

    try:
        obj.build(plotter)

        assert obj.visible is False
        assert not obj.actors[0].GetVisibility()
    finally:
        plotter.close()


def test_marker_rebuild_and_detach_do_not_accumulate_actors() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    obj = MarkerObject(
        name="marker.lifecycle",
        marker=Marker(position=(0.0, 0.0, 0.0)),
    )

    try:
        obj.build(first_plotter)
        first_actor = obj.actors[0]
        obj.build(first_plotter)

        assert len(first_plotter.renderer.actors) == 1
        assert len(obj.actors) == 1
        assert obj.actors[0] is not first_actor

        obj.build(second_plotter)

        assert len(first_plotter.renderer.actors) == 0
        assert len(second_plotter.renderer.actors) == 1

        obj.detach(render=False)

        assert len(second_plotter.renderer.actors) == 0
        assert obj.actors == []
        assert obj.mesh is None
        assert obj.attached_plotter is None
    finally:
        first_plotter.close()
        second_plotter.close()


def test_marker_object_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "golden-star.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    obj = MarkerObject(
        name="marker.golden-star",
        marker=Marker(
            position=(0.0, 0.0, 0.0),
            style=MarkerStyle(
                shape="star",
                color="gold",
                radius=0.4,
            ),
        ),
    )

    try:
        obj.build(plotter)
        plotter.camera_position = "iso"
        image = plotter.screenshot(
            filename=str(output),
            return_img=True,
        )
    finally:
        plotter.close()

    assert output.is_file()
    assert output.stat().st_size > 0
    assert isinstance(image, np.ndarray)
    assert image.shape[:2] == (240, 320)
