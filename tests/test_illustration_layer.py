import numpy as np
import pyvista as pv

from wenu3d import (
    Annotation,
    AnnotationObject,
    CurveObject,
    IllustrationLayer,
    LineSegment,
    Marker,
    MarkerObject,
    PlaneSurface,
    SampledCurve,
    SegmentObject,
    SurfaceObject,
)


def make_illustration() -> IllustrationLayer:
    layer = IllustrationLayer(name="illustration.coordinates")
    layer.add_marker(
        "illustration.star",
        Marker(position=(0.0, 0.0, 1.0)),
    )
    layer.add_segment(
        "illustration.sight-line",
        LineSegment(
            start=(0.0, 0.0, 0.0),
            end=(0.0, 0.0, 1.0),
        ),
    )
    layer.add_curve(
        "illustration.arc",
        SampledCurve(
            points=((1.0, 0.0, 0.0), (0.7, 0.0, 0.7), (0.0, 0.0, 1.0)),
        ),
    )
    layer.add_surface(
        "illustration.horizon",
        PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=2.0,
            height=1.2,
        ),
    )
    layer.add_annotation(
        "illustration.label",
        Annotation(
            text="Star",
            anchor=(0.0, 0.0, 1.0),
            offset=(0.0, 0.0, 0.1),
        ),
    )
    return layer


def test_illustration_layer_creates_typed_objects_in_order() -> None:
    layer = make_illustration()

    assert [obj.name for obj in layer.objects] == [
        "illustration.star",
        "illustration.sight-line",
        "illustration.arc",
        "illustration.horizon",
        "illustration.label",
    ]
    assert isinstance(layer.objects[0], MarkerObject)
    assert isinstance(layer.objects[1], SegmentObject)
    assert isinstance(layer.objects[2], CurveObject)
    assert isinstance(layer.objects[3], SurfaceObject)
    assert isinstance(layer.objects[4], AnnotationObject)
    assert layer.get("illustration.arc") is layer.objects[2]


def test_illustration_helpers_preserve_supplied_records() -> None:
    layer = IllustrationLayer(name="illustration.records")
    marker = Marker(position=(0.0, 0.0, 1.0))
    segment = LineSegment(
        start=(0.0, 0.0, 0.0),
        end=(0.0, 0.0, 1.0),
    )
    curve = SampledCurve(
        points=((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )
    surface = PlaneSurface(
        center=(0.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
        axis_u=(1.0, 0.0, 0.0),
        width=2.0,
        height=1.0,
    )
    annotation = Annotation(
        text="Star",
        anchor=(0.0, 0.0, 1.0),
    )

    assert layer.add_marker("marker", marker).marker is marker
    assert layer.add_segment("segment", segment).segment is segment
    assert layer.add_curve("curve", curve).curve is curve
    assert layer.add_surface("surface", surface).surface is surface
    assert layer.add_annotation("annotation", annotation).annotation is annotation


def test_mixed_illustration_builds_in_one_layer() -> None:
    plotter = pv.Plotter(off_screen=True)
    layer = make_illustration()

    try:
        layer.build(plotter)

        assert layer.attached_plotter is plotter
        assert len(layer.objects) == 5
        assert len(layer.actors) == 5
        assert len(plotter.renderer.actors) == 5
        assert all(obj.attached_plotter is plotter for obj in layer.objects)
        assert all(len(obj.actors) == 1 for obj in layer.objects)
    finally:
        plotter.close()


def test_layer_visibility_preserves_mixed_child_selection() -> None:
    plotter = pv.Plotter(off_screen=True)
    layer = make_illustration()
    hidden = layer.get("illustration.sight-line")
    selected = layer.get("illustration.star")

    try:
        hidden.set_visible(False, render=False)
        layer.build(plotter)

        layer.set_visible(False, render=False)
        assert hidden.visible is False
        assert selected.visible is True
        assert all(not actor.GetVisibility() for actor in layer.actors)

        layer.set_visible(True, render=False)
        assert not hidden.actors[0].GetVisibility()
        assert selected.actors[0].GetVisibility()
    finally:
        plotter.close()


def test_illustration_rebuild_and_detach_do_not_accumulate_actors() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    layer = make_illustration()

    try:
        layer.build(first_plotter)
        first_actors = tuple(layer.actors)
        layer.build(first_plotter)

        assert len(first_plotter.renderer.actors) == 5
        assert len(layer.actors) == 5
        assert {id(actor) for actor in first_actors}.isdisjoint(
            id(actor) for actor in layer.actors
        )

        layer.build(second_plotter)

        assert len(first_plotter.renderer.actors) == 0
        assert len(second_plotter.renderer.actors) == 5

        layer.detach(render=False)

        assert len(second_plotter.renderer.actors) == 0
        assert layer.actors == []
        assert layer.attached_plotter is None
        assert all(obj.actors == [] for obj in layer.objects)
        assert all(obj.attached_plotter is None for obj in layer.objects)
    finally:
        first_plotter.close()
        second_plotter.close()


def test_mixed_illustration_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "scientific-illustration.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    layer = make_illustration()

    try:
        layer.build(plotter)
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
