from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from wenu3d.controls import (
    ControlManager,
    GridControlPanel,
    PanelPlacement,
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

    def add(self) -> None:
        self.add_count += 1


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
