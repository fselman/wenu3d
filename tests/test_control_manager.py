from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from wenu3d.controls import (
    ChoiceControlPanel,
    ControlManager,
    GridControlPanel,
    PanelPlacement,
    ScalarControlPanel,
    VisibilityControlPanel,
)
from wenu3d.frames import horizontal_frame
from wenu3d.grid import GridLayer
from wenu3d.scene import CelestialScene


@dataclass
class FakePanel:
    origin_x: int = -1
    origin_y: int = -1
    control_size: tuple[int, int] = (100, 150)
    add_count: int = 0
    sync_count: int = 0
    widgets: tuple[object, ...] = ()
    text_actors: tuple[object, ...] = ()

    def add(self) -> None:
        self.add_count += 1

    def sync_from_model(self) -> None:
        self.sync_count += 1


def make_manager(
    *,
    window_size: tuple[int, int] = (500, 400),
) -> tuple[ControlManager, Mock]:
    plotter = Mock()
    manager = ControlManager(
        plotter=plotter,
        window_size=window_size,
        margin=20,
        top_margin=20,
        panel_gap=10,
        bottom_lane_height=0,
    )
    return manager, plotter


def make_grid() -> GridLayer:
    return GridLayer(
        name="horizontal",
        frame=horizontal_frame(),
        meridians_deg=(0.0, 90.0),
        parallels_deg=(0.0,),
    )


def test_grid_panel_reports_size_from_its_content() -> None:
    panel = GridControlPanel(
        plotter=Mock(),
        grid=make_grid(),
    )

    assert panel.control_size == (150, 188)


def test_scene_registers_grid_panel_without_coordinates() -> None:
    scene = object.__new__(CelestialScene)
    scene.plotter = Mock()
    scene.controls = Mock()
    scene.controls.register_panel.side_effect = lambda panel: panel

    panel = scene.add_grid_controls(make_grid())

    assert isinstance(panel, GridControlPanel)
    scene.controls.register_panel.assert_called_once_with(panel)


def test_manager_can_exchange_registered_panel_presentations() -> None:
    manager, plotter = make_manager()
    widget = Mock()
    text_actor = Mock()
    panel = FakePanel(
        widgets=(widget,),
        text_actors=(text_actor,),
    )
    manager.register_panel(panel)

    manager.set_panel_visible(panel, False, render=False)

    widget.SetEnabled.assert_called_with(False)
    text_actor.SetVisibility.assert_called_with(False)
    plotter.render.assert_not_called()
    with pytest.raises(ValueError, match="not registered"):
        manager.set_panel_visible(FakePanel(), True, render=False)


def test_visibility_panel_sets_and_synchronizes_caller_capability() -> None:
    plotter = Mock()
    widget = Mock()
    plotter.add_checkbox_button_widget.return_value = widget
    state = {"visible": True}
    panel = VisibilityControlPanel(
        plotter=plotter,
        set_visible=lambda value: state.__setitem__("visible", value),
        get_visible=lambda: state["visible"],
        label="Mostrar la Tierra",
        title="Contexto local",
    )

    panel.add()
    panel._set_visible(False)
    panel.sync_from_model()

    assert not state["visible"]
    widget.GetRepresentation().SetState.assert_called_with(0)


def test_choice_panel_sets_and_synchronizes_mutually_exclusive_model_value() -> None:
    plotter = Mock()
    widgets = [Mock(), Mock()]
    plotter.add_radio_button_widget.side_effect = widgets
    state = {"mode": "equatorial"}
    panel = ChoiceControlPanel(
        plotter=plotter,
        set_choice=lambda value: state.__setitem__("mode", value),
        get_choice=lambda: state["mode"],
        choices=(("horizontal", "Horizontal"), ("equatorial", "Ecuatorial")),
        title="Sistema",
        group="coordinates",
    )

    panel.add()
    panel._callback("horizontal")()
    panel.sync_from_model()

    assert state["mode"] == "horizontal"
    assert [call.kwargs["value"] for call in plotter.add_radio_button_widget.call_args_list] == [False, True]
    widgets[0].GetRepresentation().SetState.assert_called_with(1)
    widgets[1].GetRepresentation().SetState.assert_called_with(0)


def test_grid_panel_uses_initial_model_visibility() -> None:
    grid = make_grid()
    grid.set_visible(False, render=False)
    grid.set_meridian_visible(90.0, False)
    plotter = Mock()
    plotter.add_checkbox_button_widget.side_effect = [
        Mock()
        for _ in range(6)
    ]

    panel = GridControlPanel(plotter=plotter, grid=grid)
    panel.add()

    values = [
        call.kwargs["value"]
        for call in plotter.add_checkbox_button_widget.call_args_list
    ]
    assert values == [False, True, True, False, True, True]


def test_grid_panel_hides_layer_without_losing_curve_selections() -> None:
    grid = make_grid()
    grid.set_meridian_visible(90.0, False)
    panel = GridControlPanel(plotter=Mock(), grid=grid)

    panel._set_grid_enabled(False)

    assert not grid.visible
    assert grid.meridians[0.0].visible
    assert not grid.meridians[90.0].visible
    assert grid.parallels[0.0].visible
    panel.plotter.render.assert_called_once_with()


def test_grid_panel_syncs_external_grid_and_curve_changes() -> None:
    grid = make_grid()
    plotter = Mock()
    widgets = [Mock() for _ in range(6)]
    plotter.add_checkbox_button_widget.side_effect = widgets
    panel = GridControlPanel(plotter=plotter, grid=grid)
    panel.add()

    grid.set_visible(False, render=False)
    grid.set_meridian_visible(90.0, False)
    grid.set_parallel_visible(0.0, False)
    panel.sync_from_model()

    assert not panel.grid_enabled
    assert panel.meridian_states == {0.0: True, 90.0: False}
    assert panel.parallel_states == {0.0: False}
    widgets[0].GetRepresentation().SetState.assert_called_with(0)
    widgets[3].GetRepresentation().SetState.assert_called_with(0)
    widgets[5].GetRepresentation().SetState.assert_called_with(0)


def test_grid_panel_sync_preserves_disabled_family_selections() -> None:
    grid = make_grid()
    plotter = Mock()
    plotter.add_checkbox_button_widget.side_effect = [
        Mock()
        for _ in range(6)
    ]
    panel = GridControlPanel(plotter=plotter, grid=grid)
    panel.add()

    panel._set_meridians_enabled(False)
    panel.sync_from_model()
    panel._set_meridians_enabled(True)

    assert all(curve.visible for curve in grid.meridians.values())


def test_control_manager_stacks_then_wraps_panels() -> None:
    manager, _ = make_manager()
    first = FakePanel()
    second = FakePanel()
    third = FakePanel()

    third.control_size = (120, 100)

    manager.register_panel(first)
    manager.register_panel(second)
    manager.register_panel(third)

    assert (first.origin_x, first.origin_y) == (20, 380)
    assert (second.origin_x, second.origin_y) == (20, 220)
    assert (third.origin_x, third.origin_y) == (130, 380)
    assert manager.placements == [
        PanelPlacement(20, 380, 100, 150),
        PanelPlacement(20, 220, 100, 150),
        PanelPlacement(130, 380, 120, 100),
    ]
    assert manager.panels == [first, second, third]
    assert all(panel.add_count == 1 for panel in manager.panels)


def test_scalar_panels_fill_reserved_bottom_lane_left_to_right() -> None:
    plotter = Mock()
    plotter.window_size = (1600, 1150)
    plotter.add_slider_widget.side_effect = [Mock(), Mock(), Mock()]
    manager = ControlManager(
        plotter=plotter,
        window_size=(1600, 1150),
    )
    panels = [
        ScalarControlPanel(
            plotter=plotter,
            set_value=Mock(),
            get_value=lambda: 1.0,
            title=title,
            value_range=(0.0, 2.0),
        )
        for title in ("Acimut", "Altura", "Horizonte local")
    ]

    for panel in panels:
        manager.register_panel(panel)

    assert [(panel.origin_x, panel.origin_y) for panel in panels] == [
        (20, 138),
        (338, 138),
        (656, 138),
    ]
    assert all(
        placement.origin_y - placement.height == 20
        for placement in manager.placements
    )


def test_scalar_panel_can_rebind_to_another_model_capability() -> None:
    plotter = Mock()
    plotter.window_size = (900, 600)
    widget = Mock()
    plotter.add_slider_widget.return_value = widget
    first_setter = Mock()
    second_setter = Mock()
    panel = ScalarControlPanel(
        plotter=plotter,
        set_value=first_setter,
        get_value=lambda: 45.0,
        title="Acimut",
        value_range=(0.0, 359.0),
        value_format="%.0f°",
    )
    panel.add()

    panel.set_capability(
        set_value=second_setter,
        get_value=lambda: 5.5,
        title="RA",
        value_range=(0.0, 24.0),
        value_format="%.1f h",
    )
    panel._set_value(6.0)

    representation = widget.GetRepresentation.return_value
    representation.SetMinimumValue.assert_called_with(0.0)
    representation.SetMaximumValue.assert_called_with(24.0)
    representation.SetValue.assert_called_with(5.5)
    representation.SetTitleText.assert_called_with("RA")
    representation.SetLabelFormat.assert_called_with("%.1f h")
    second_setter.assert_called_once_with(6.0)
    first_setter.assert_not_called()


def test_side_panels_reserve_bottom_control_lane() -> None:
    manager, _ = make_manager(window_size=(500, 400))
    manager.bottom_lane_height = 145
    first = FakePanel(control_size=(100, 150))
    second = FakePanel(control_size=(100, 150))

    manager.register_panel(first)
    manager.register_panel(second)

    assert first.origin_x == 20
    assert second.origin_x == 130


def test_default_gap_and_reported_panel_sizes_prevent_dense_overlap() -> None:
    manager, _ = make_manager(window_size=(1600, 1150))
    panels = [
        FakePanel(control_size=(340, 260)),
        FakePanel(control_size=(260, 96)),
        FakePanel(control_size=(260, 96)),
        FakePanel(control_size=(260, 96)),
        FakePanel(control_size=(300, 118)),
        FakePanel(control_size=(300, 118)),
        FakePanel(control_size=(300, 118)),
        FakePanel(control_size=(300, 190)),
    ]
    manager.panel_gap = 18

    for panel in panels:
        manager.register_panel(panel)

    assert not any(
        first.overlaps(second)
        for index, first in enumerate(manager.placements)
        for second in manager.placements[index + 1:]
    )
    assert max(placement.origin_x for placement in manager.placements) > 20


def test_control_manager_rejects_duplicate_panel() -> None:
    manager, _ = make_manager()
    panel = FakePanel()
    manager.register_panel(panel)

    with pytest.raises(ValueError, match="already registered"):
        manager.register_panel(panel)

    assert panel.add_count == 1


def test_control_manager_rejects_panel_that_cannot_fit() -> None:
    manager, _ = make_manager(window_size=(200, 200))
    panel = FakePanel(control_size=(180, 100))

    with pytest.raises(ValueError, match="does not fit"):
        manager.register_panel(panel)

    assert panel.add_count == 0
    assert manager.panels == []


def test_control_manager_reserves_top_margin() -> None:
    plotter = Mock()
    manager = ControlManager(
        plotter=plotter,
        window_size=(500, 400),
        margin=20,
        top_margin=70,
    )
    panel = FakePanel(control_size=(100, 100))

    manager.register_panel(panel)

    assert panel.origin_y == 330


def test_panel_placement_detects_rectangle_overlap() -> None:
    first = PanelPlacement(20, 380, 100, 150)

    assert first.overlaps(
        PanelPlacement(80, 300, 100, 100)
    )
    assert not first.overlaps(
        PanelPlacement(130, 380, 100, 150)
    )
    assert not first.overlaps(
        PanelPlacement(20, 220, 100, 150)
    )


def test_control_manager_batches_nested_render_requests() -> None:
    manager, plotter = make_manager()

    with manager.batch_render():
        manager.request_render()
        with manager.batch_render():
            manager.request_render()
        manager.request_render()

    plotter.render.assert_called_once_with()


def test_control_manager_renders_immediately_outside_batch() -> None:
    manager, plotter = make_manager()

    manager.request_render()

    plotter.render.assert_called_once_with()


def test_control_manager_syncs_panels_with_one_render() -> None:
    manager, plotter = make_manager()
    first = manager.register_panel(FakePanel())
    second = manager.register_panel(FakePanel())
    plotter.reset_mock()

    manager.sync()

    assert first.sync_count == 1
    assert second.sync_count == 1
    plotter.render.assert_called_once_with()


def test_control_manager_hides_widgets_representations_and_text() -> None:
    manager, plotter = make_manager()
    widget = Mock()
    text = Mock(spec=["SetVisibility"])
    panel = FakePanel(widgets=(widget,), text_actors=(text,))
    manager.register_panel(panel)
    plotter.reset_mock()

    manager.set_visible(False)

    widget.SetEnabled.assert_called_once_with(False)
    widget.GetRepresentation.return_value.SetVisibility.assert_called_once_with(False)
    text.SetVisibility.assert_called_once_with(False)
    plotter.render.assert_called_once_with()


def test_control_manager_temporarily_hides_registered_external_widget() -> None:
    manager, _ = make_manager()
    widget = Mock()
    manager.register_widget(widget)

    with manager.hidden():
        widget.SetEnabled.assert_called_with(False)
        widget.GetRepresentation.return_value.SetVisibility.assert_called_with(False)

    widget.SetEnabled.assert_called_with(True)
    widget.GetRepresentation.return_value.SetVisibility.assert_called_with(True)


def test_control_manager_registers_radio_buttons_and_their_titles() -> None:
    manager, plotter = make_manager()
    first_button = Mock()
    second_button = Mock()
    first_title = Mock()
    second_title = Mock()
    plotter.widgets.radio_button_widget_dict = {
        "export": [first_button, second_button],
    }
    plotter.widgets.radio_button_title_dict = {
        "export": [first_title, second_title],
    }

    items = manager.register_radio_group("export")

    assert items == (
        first_button,
        second_button,
        first_title,
        second_title,
    )
    assert manager.external_widgets == list(items)


def test_control_manager_rejects_duplicate_external_widget() -> None:
    manager, _ = make_manager()
    widget = Mock()
    manager.register_widget(widget)
