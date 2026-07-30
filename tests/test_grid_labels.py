import numpy as np
import pyvista as pv
import pytest

from wenu3d.annotations import AnnotationStyle
from wenu3d.frames import horizontal_frame
from wenu3d.grid import GridLayer, GridStyle


def make_grid() -> GridLayer:
    return GridLayer(
        name="horizontal",
        frame=horizontal_frame(),
        meridians_deg=(0.0, 90.0),
        parallels_deg=(-30.0, 0.0),
        style=GridStyle(
            color="#345678",
            label_format="{value:+g} deg",
            label_offset=0.05,
        ),
        radius=0.9,
    )


def test_grid_label_layer_selects_curves_and_anchors() -> None:
    grid = make_grid()
    labels = grid.make_label_layer(
        meridian_anchors={90.0: 20.0},
        parallel_anchors={-30.0: 45.0},
    )

    assert labels.name == "horizontal.labels"
    assert len(labels.objects) == 2

    meridian = labels.get("horizontal.labels.meridian.90")
    parallel = labels.get("horizontal.labels.parallel.-30")

    assert meridian.annotation.text == "+90 deg"
    assert meridian.annotation.associated_with == (
        "horizontal.meridian.90"
    )
    np.testing.assert_allclose(
        meridian.annotation.anchor,
        grid.frame.point(90.0, 20.0, radius=0.9),
    )
    np.testing.assert_allclose(
        meridian.annotation.position,
        grid.frame.point(90.0, 20.0, radius=0.95),
    )

    assert parallel.annotation.text == "-30 deg"
    assert parallel.annotation.associated_with == (
        "horizontal.parallel.-30"
    )
    np.testing.assert_allclose(
        parallel.annotation.position,
        grid.frame.point(45.0, -30.0, radius=0.95),
    )


def test_grid_label_layer_accepts_independent_name_and_style() -> None:
    grid = make_grid()
    style = AnnotationStyle(
        color="#abcdef",
        font_size=20,
        bold=True,
    )
    labels = grid.make_label_layer(
        name="selected.labels",
        meridian_anchors={0.0: 30.0},
        annotation_style=style,
    )

    label = labels.get("selected.labels.meridian.0")
    assert label.annotation.style is style
    assert len(labels.objects) == 1


def test_grid_label_layer_rejects_curve_not_in_grid() -> None:
    grid = make_grid()

    with pytest.raises(KeyError):
        grid.make_label_layer(meridian_anchors={180.0: 0.0})

    with pytest.raises(KeyError):
        grid.make_label_layer(parallel_anchors={60.0: 0.0})


def test_grid_labels_and_curves_have_independent_visibility() -> None:
    plotter = pv.Plotter(off_screen=True)
    grid = make_grid()
    labels = grid.make_label_layer(
        meridian_anchors={0.0: 30.0},
    )
    curve = grid.meridians[0.0]
    label = labels.get("horizontal.labels.meridian.0")

    try:
        grid.build(plotter)
        labels.build(plotter)

        curve.set_visible(False, render=False)
        assert not curve.actors[0].GetVisibility()
        assert label.actors[0].GetVisibility()

        curve.set_visible(True, render=False)
        label.set_visible(False, render=False)
        assert curve.actors[0].GetVisibility()
        assert not label.actors[0].GetVisibility()
    finally:
        plotter.close()
