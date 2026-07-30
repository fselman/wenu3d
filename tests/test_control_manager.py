from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from wenu3d.controls import ControlManager, PanelPlacement


@dataclass
class FakePanel:
    origin_x: int = -1
    origin_y: int = -1
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
        panel_gap=10,
    )
    return manager, plotter


def test_control_manager_stacks_then_wraps_panels() -> None:
    manager, _ = make_manager()
    first = FakePanel()
    second = FakePanel()
    third = FakePanel()

    manager.register_panel(first, width=100, height=150)
    manager.register_panel(second, width=100, height=150)
    manager.register_panel(third, width=120, height=100)

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
    manager.register_panel(panel, width=100, height=100)

    with pytest.raises(ValueError, match="already registered"):
        manager.register_panel(panel, width=100, height=100)

    assert panel.add_count == 1


def test_control_manager_rejects_panel_that_cannot_fit() -> None:
    manager, _ = make_manager(window_size=(200, 200))
    panel = FakePanel()

    with pytest.raises(ValueError, match="does not fit"):
        manager.register_panel(panel, width=180, height=100)

    assert panel.add_count == 0
    assert manager.panels == []


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
