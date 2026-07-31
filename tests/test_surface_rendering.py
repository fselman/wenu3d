import numpy as np
import pyvista as pv
import pytest

from wenu3d import PlaneSurface, SurfaceObject, SurfaceStyle


def test_surface_object_requires_plane_surface() -> None:
    with pytest.raises(TypeError, match="PlaneSurface"):
        SurfaceObject(name="invalid")


def test_plane_surface_builds_one_finite_quadrilateral() -> None:
    plotter = pv.Plotter(off_screen=True)
    surface = PlaneSurface(
        center=(1.0, -2.0, 0.5),
        normal=(0.0, 0.0, 1.0),
        axis_u=(1.0, 0.0, 0.0),
        width=4.0,
        height=2.0,
        style=SurfaceStyle(
            color="silver",
            opacity=0.65,
            show_edges=True,
            edge_color="navy",
            edge_width=5.0,
        ),
    )
    obj = SurfaceObject(name="surface.plane", surface=surface)

    try:
        obj.build(plotter)

        assert obj.attached_plotter is plotter
        assert obj.mesh is not None
        assert obj.mesh.n_points == 4
        assert obj.mesh.n_cells == 1
        np.testing.assert_allclose(obj.mesh.points, surface.corners())
        np.testing.assert_array_equal(obj.mesh.faces, (4, 0, 1, 2, 3))
        assert obj.actors == [plotter.renderer.actors[obj.name]]
        prop = obj.actors[0].GetProperty()
        assert prop.GetOpacity() == 0.65
        assert prop.GetEdgeVisibility() == 1
        assert prop.GetLineWidth() == 5.0
    finally:
        plotter.close()


def test_surface_style_can_hide_edges() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = SurfaceObject(
        name="surface.no-edges",
        surface=PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=2.0,
            height=1.0,
            style=SurfaceStyle(show_edges=False),
        ),
    )

    try:
        obj.build(plotter)

        assert obj.actors[0].GetProperty().GetEdgeVisibility() == 0
    finally:
        plotter.close()


def test_surface_visibility_comes_from_record() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = SurfaceObject(
        name="surface.hidden",
        surface=PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=2.0,
            height=1.0,
            visible=False,
        ),
    )

    try:
        obj.build(plotter)

        assert obj.visible is False
        assert not obj.actors[0].GetVisibility()
    finally:
        plotter.close()


def test_surface_rebuild_and_detach_do_not_accumulate_actors() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    obj = SurfaceObject(
        name="surface.lifecycle",
        surface=PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=2.0,
            height=1.0,
        ),
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


def test_semi_opaque_plane_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "plane-surface.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    obj = SurfaceObject(
        name="surface.horizon",
        surface=PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=2.0,
            height=1.2,
            style=SurfaceStyle(
                color="silver",
                opacity=0.52,
                show_edges=True,
                edge_color="#777777",
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
