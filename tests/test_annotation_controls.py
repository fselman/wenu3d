from unittest.mock import Mock

import pytest

from wenu3d import AnnotationControlPanel, AnnotationLayer
from wenu3d.scene import CelestialScene


def make_layers() -> tuple[AnnotationLayer, AnnotationLayer]:
    return (
        AnnotationLayer(name="grid.labels"),
        AnnotationLayer(name="scientific.callouts"),
    )


def make_plotter() -> Mock:
    plotter = Mock()
    plotter.window_size = (1800, 1200)
    plotter.add_text.return_value = object()
    plotter.add_checkbox_button_widget.return_value = object()
    plotter.add_slider_widget.return_value = object()
    return plotter


def test_annotation_panel_requires_layers() -> None:
    with pytest.raises(ValueError, match="at least one"):
        AnnotationControlPanel(
            plotter=make_plotter(),
            layers=(),
        )


def test_annotation_panel_reports_managed_size() -> None:
    panel = AnnotationControlPanel(
        plotter=make_plotter(),
        layers=make_layers(),
    )

    assert panel.control_size == (270, 140)


def test_annotation_panel_adds_controls_at_assigned_position() -> None:
    plotter = make_plotter()
    panel = AnnotationControlPanel(
        plotter=plotter,
        layers=make_layers(),
        origin_x=182,
        origin_y=1180,
    )

    panel.add()

    checkbox = plotter.add_checkbox_button_widget.call_args.kwargs
    slider = plotter.add_slider_widget.call_args.kwargs

    assert checkbox["position"] == (182, 1142)
    assert checkbox["value"] is True
    assert slider["pointa"] == pytest.approx(
        (192 / 1800, 1080 / 1200)
    )
    assert slider["pointb"] == pytest.approx(
        (442 / 1800, 1080 / 1200)
    )
    assert len(panel.widgets) == 4


def test_annotation_panel_updates_all_layers_with_one_render() -> None:
    plotter = make_plotter()
    layers = make_layers()
    panel = AnnotationControlPanel(
        plotter=plotter,
        layers=layers,
    )

    panel._set_visible(False)

    assert all(not layer.visible for layer in layers)
    plotter.render.assert_called_once_with()

    plotter.render.reset_mock()
    panel._set_font_size_scale(1.75)

    assert all(layer.font_size_scale == 1.75 for layer in layers)
    plotter.render.assert_called_once_with()


def test_scene_registers_annotation_panel_without_coordinates() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = make_plotter()
    scene.style = Mock(horizontal_grid_color="#506070")
    scene.controls = Mock()
    scene.controls.register_panel.side_effect = lambda panel: panel
    layers = make_layers()

    panel = scene.add_annotation_controls(*layers)

    assert isinstance(panel, AnnotationControlPanel)
    assert panel.layers == layers
    scene.controls.register_panel.assert_called_once_with(panel)
