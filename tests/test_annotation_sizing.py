from unittest.mock import patch

import pyvista as pv
import pytest

from wenu3d import Annotation, AnnotationLayer, AnnotationStyle


def make_layer() -> AnnotationLayer:
    layer = AnnotationLayer(name="annotations")
    layer.add_annotation(
        "annotations.pole",
        Annotation(
            text="Polo sur celeste",
            anchor=(0.0, 0.0, -1.0),
            style=AnnotationStyle(font_size=20),
        ),
    )
    return layer


def test_annotation_layer_applies_font_size_scale_when_building() -> None:
    plotter = pv.Plotter(off_screen=True)
    layer = make_layer()

    try:
        with patch.object(
            plotter,
            "add_point_labels",
            wraps=plotter.add_point_labels,
        ) as add_point_labels:
            layer.build(plotter)
            first_actor = layer.actors[0]

            layer.set_font_size_scale(1.5, render=False)

        assert layer.font_size_scale == 1.5
        assert layer.objects[0].font_size_scale == 1.5
        assert layer.actors[0] is not first_actor
        assert add_point_labels.call_args.kwargs["font_size"] == 30
    finally:
        plotter.close()


def test_annotation_size_scale_survives_detached_updates() -> None:
    plotter = pv.Plotter(off_screen=True)
    layer = make_layer()

    try:
        layer.set_font_size_scale(2.0)

        with patch.object(
            plotter,
            "add_point_labels",
            wraps=plotter.add_point_labels,
        ) as add_point_labels:
            layer.build(plotter)

        assert add_point_labels.call_args.kwargs["font_size"] == 40
    finally:
        plotter.close()


@pytest.mark.parametrize("scale", [0.0, -1.0, float("nan")])
def test_annotation_layer_rejects_invalid_font_size_scale(scale) -> None:
    layer = make_layer()

    with pytest.raises(ValueError, match="scale"):
        layer.set_font_size_scale(scale)
