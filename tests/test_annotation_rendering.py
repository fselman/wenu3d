import numpy as np
import pyvista as pv
import pytest

from wenu3d import (
    Annotation,
    AnnotationLayer,
    AnnotationObject,
    AnnotationStyle,
)


def make_annotation(
    text: str = "Zenith",
    *,
    visible: bool = True,
) -> Annotation:
    return Annotation(
        text=text,
        anchor=(0.0, 0.0, 0.0),
        offset=(0.0, 0.0, 0.1),
        style=AnnotationStyle(
            color="#222222",
            font_size=18,
            bold=True,
        ),
        visible=visible,
    )


def test_annotation_object_requires_annotation() -> None:
    with pytest.raises(TypeError, match="Annotation"):
        AnnotationObject(name="invalid")


def test_annotation_object_builds_rebuilds_and_detaches() -> None:
    plotter = pv.Plotter(off_screen=True)
    obj = AnnotationObject(
        name="annotation.zenith",
        annotation=make_annotation(),
    )

    try:
        obj.build(plotter)
        first_actor = obj.actors[0]

        assert len(obj.actors) == 1
        assert obj.attached_plotter is plotter
        assert first_actor.GetVisibility()

        obj.build(plotter)

        assert len(obj.actors) == 1
        assert obj.actors[0] is not first_actor

        obj.detach(render=False)

        assert obj.actors == []
        assert obj.attached_plotter is None
    finally:
        plotter.close()


def test_annotation_visibility_and_layer_visibility() -> None:
    plotter = pv.Plotter(off_screen=True)
    layer = AnnotationLayer(name="annotations")
    hidden = layer.add_annotation(
        "annotation.hidden",
        make_annotation("Hidden", visible=False),
    )
    visible = layer.add_annotation(
        "annotation.visible",
        make_annotation("Visible"),
    )

    try:
        layer.build(plotter)

        assert not hidden.actors[0].GetVisibility()
        assert visible.actors[0].GetVisibility()

        layer.set_visible(False, render=False)
        assert not hidden.actors[0].GetVisibility()
        assert not visible.actors[0].GetVisibility()

        layer.set_visible(True, render=False)
        assert not hidden.actors[0].GetVisibility()
        assert visible.actors[0].GetVisibility()
    finally:
        plotter.close()


def test_annotation_layer_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "annotation.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )
    layer = AnnotationLayer(name="annotations")
    layer.add_annotation(
        "annotation.zenith",
        make_annotation(),
    )

    try:
        layer.build(plotter)
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
