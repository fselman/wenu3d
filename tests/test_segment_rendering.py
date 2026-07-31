import numpy as np
import pyvista as pv
import pytest

from wenu3d import LineSegment, SegmentObject, SegmentStyle, SightLine


def test_segment_object_requires_supported_record() -> None:
    with pytest.raises(TypeError, match="LineSegment or SightLine"):
        SegmentObject(name="invalid")


@pytest.mark.parametrize(
    "record",
    [
        LineSegment(
            start=(1.0, -2.0, 0.5),
            end=(2.0, 1.0, 4.5),
            style=SegmentStyle(
                color="navy",
                width=5.0,
                opacity=0.65,
            ),
        ),
        SightLine(
            observer_position=(1.0, -2.0, 0.5),
            target_position=(2.0, 1.0, 4.5),
            style=SegmentStyle(
                color="navy",
                width=5.0,
                opacity=0.65,
            ),
        ),
    ],
)
def test_segment_records_use_one_finite_renderer(record) -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = SegmentObject(name="segment.finite", segment=record)

    try:
        obj.build(plotter)

        assert obj.attached_plotter is plotter
        assert obj.mesh is not None
        assert obj.mesh.n_points == 2
        assert obj.mesh.n_cells == 1
        np.testing.assert_allclose(obj.mesh.points[0], record.start)
        np.testing.assert_allclose(obj.mesh.points[1], record.end)
        assert obj.actors == [plotter.renderer.actors[obj.name]]
        prop = obj.actors[0].GetProperty()
        assert prop.GetLineWidth() == 5.0
        assert prop.GetOpacity() == 0.65
    finally:
        plotter.close()


def test_segment_visibility_comes_from_record() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = SegmentObject(
        name="segment.hidden",
        segment=LineSegment(
            start=(0.0, 0.0, 0.0),
            end=(1.0, 0.0, 0.0),
            visible=False,
        ),
    )

    try:
        obj.build(plotter)

        assert obj.visible is False
        assert not obj.actors[0].GetVisibility()
    finally:
        plotter.close()


def test_segment_rebuild_and_detach_do_not_accumulate_actors() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    obj = SegmentObject(
        name="segment.lifecycle",
        segment=SightLine(
            observer_position=(-0.2, 0.0, 0.0),
            target_position=(0.0, 0.0, 1.0),
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


def test_sight_line_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "sight-line.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    obj = SegmentObject(
        name="segment.sight-line",
        segment=SightLine(
            observer_position=(-0.5, -0.2, 0.0),
            target_position=(0.5, 0.2, 1.0),
            style=SegmentStyle(
                color="gold",
                width=8.0,
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
