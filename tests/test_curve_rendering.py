import numpy as np
import pyvista as pv
import pytest

from wenu3d import CurveObject, CurveStyle, SampledCurve


def test_curve_object_requires_sampled_curve() -> None:
    with pytest.raises(TypeError, match="SampledCurve"):
        CurveObject(name="invalid")


def test_curve_builds_one_connected_polyline() -> None:
    plotter = pv.Plotter(off_screen=True)
    curve = SampledCurve(
        points=(
            (0.0, 0.0, 0.0),
            (0.5, 0.5, 0.0),
            (1.0, 0.0, 0.0),
        ),
        style=CurveStyle(
            color="navy",
            width=7.0,
            opacity=0.65,
        ),
    )
    obj = CurveObject(name="curve.polyline", curve=curve)

    try:
        obj.build(plotter)

        assert obj.attached_plotter is plotter
        assert obj.mesh is not None
        assert obj.mesh.n_points == 3
        assert obj.mesh.n_cells == 1
        np.testing.assert_allclose(obj.mesh.points, curve.as_array())
        assert obj.arrow_meshes == ()
        assert obj.actors == [plotter.renderer.actors[obj.name]]
        prop = obj.actors[0].GetProperty()
        assert prop.GetLineWidth() == 7.0
        assert prop.GetOpacity() == 0.65
    finally:
        plotter.close()


@pytest.mark.parametrize(
    ("placement", "expected_suffixes"),
    [
        ("none", ()),
        ("start", ("start",)),
        ("end", ("end",)),
        ("both", ("start", "end")),
    ],
)
def test_curve_builds_selected_arrowheads(
    placement: str,
    expected_suffixes: tuple[str, ...],
) -> None:
    plotter = pv.Plotter(off_screen=True)
    curve = SampledCurve(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
        ),
        style=CurveStyle(
            arrowheads=placement,
            arrow_size=0.2,
        ),
    )
    obj = CurveObject(name=f"curve.arrow.{placement}", curve=curve)

    try:
        obj.build(plotter)

        assert len(obj.arrow_meshes) == len(expected_suffixes)
        assert len(obj.actors) == 1 + len(expected_suffixes)
        for suffix in expected_suffixes:
            assert f"{obj.name}.arrow.{suffix}" in plotter.renderer.actors
    finally:
        plotter.close()


def test_arrowhead_tips_coincide_with_curve_endpoints() -> None:
    plotter = pv.Plotter(off_screen=True)
    curve = SampledCurve(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
        ),
        style=CurveStyle(
            arrowheads="both",
            arrow_size=0.2,
        ),
    )
    obj = CurveObject(name="curve.arrow.tips", curve=curve)

    try:
        obj.build(plotter)

        start_direction = np.array((-1.0, 0.0, 0.0))
        end_direction = np.array((0.0, 1.0, 0.0))
        start_projection = obj.arrow_meshes[0].points @ start_direction
        end_projection = obj.arrow_meshes[1].points @ end_direction

        assert np.max(start_projection) == pytest.approx(0.0, abs=1e-6)
        assert np.max(end_projection) == pytest.approx(1.0, abs=1e-6)
    finally:
        plotter.close()


def test_curve_visibility_comes_from_record_and_reaches_arrowheads() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = CurveObject(
        name="curve.hidden",
        curve=SampledCurve(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
            style=CurveStyle(arrowheads="both"),
            visible=False,
        ),
    )

    try:
        obj.build(plotter)

        assert obj.visible is False
        assert len(obj.actors) == 3
        assert all(not actor.GetVisibility() for actor in obj.actors)
    finally:
        plotter.close()


def test_curve_rebuild_and_detach_do_not_accumulate_actors() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    obj = CurveObject(
        name="curve.lifecycle",
        curve=SampledCurve(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
            style=CurveStyle(arrowheads="both"),
        ),
    )

    try:
        obj.build(first_plotter)
        first_actors = tuple(obj.actors)
        obj.build(first_plotter)

        assert len(first_plotter.renderer.actors) == 3
        assert len(obj.actors) == 3
        assert not any(actor in obj.actors for actor in first_actors)

        obj.build(second_plotter)

        assert len(first_plotter.renderer.actors) == 0
        assert len(second_plotter.renderer.actors) == 3

        obj.detach(render=False)

        assert len(second_plotter.renderer.actors) == 0
        assert obj.actors == []
        assert obj.mesh is None
        assert obj.arrow_meshes == ()
        assert obj.attached_plotter is None
    finally:
        first_plotter.close()
        second_plotter.close()


def test_thick_arrowed_curve_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "arrowed-curve.png"
    angles = np.linspace(0.0, 0.75 * np.pi, 80)
    points = np.column_stack(
        (
            np.cos(angles),
            np.sin(angles),
            np.zeros_like(angles),
        )
    )
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    obj = CurveObject(
        name="curve.arrowed",
        curve=SampledCurve(
            points=points,
            style=CurveStyle(
                color="gold",
                width=9.0,
                arrowheads="both",
                arrow_size=0.15,
            ),
        ),
    )

    try:
        obj.build(plotter)
        plotter.camera_position = "xy"
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
