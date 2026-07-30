from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

import pyvista as pv

from .grid import GridLayer


CheckboxCallback = Callable[[bool], None]

PanelT = TypeVar("PanelT", bound="ControlPanel")


class ControlPanel(Protocol):
    origin_x: int
    origin_y: int

    @property
    def control_size(self) -> tuple[int, int]: ...

    def add(self) -> None: ...


@dataclass
class GridControlPanel:
    """
    Vertical controls for one spherical grid.

    Visibility is represented at three levels:

    1. Entire grid.
    2. Meridian or parallel family.
    3. Individual meridian or parallel.

    Disabling a family hides all its curves but preserves the individual
    selections. Re-enabling it restores those selections.
    """

    plotter: pv.Plotter
    grid: GridLayer

    origin_x: int = 20
    origin_y: int = 960

    row_height: int = 23
    checkbox_size: int = 18
    indent: int = 20
    font_size: int = 9

    grid_enabled: bool = field(default=True, init=False)
    meridians_enabled: bool = field(default=True, init=False)
    parallels_enabled: bool = field(default=True, init=False)

    meridian_states: dict[float, bool] = field(
        default_factory=dict,
        init=False,
    )
    parallel_states: dict[float, bool] = field(
        default_factory=dict,
        init=False,
    )

    # Keep explicit references to VTK widgets for the lifetime of the panel.
    widgets: list[object] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        self.meridian_states = {
            float(value): True
            for value in self.grid.meridians
        }

        self.parallel_states = {
            float(value): True
            for value in self.grid.parallels
        }

    @property
    def control_size(self) -> tuple[int, int]:
        """Return the pixel width and height required by this panel."""
        row_count = (
            3
            + len(self.meridian_states)
            + len(self.parallel_states)
        )
        height = (
            34
            + row_count * self.row_height
            + 16
        )
        width = (
            self.indent
            + self.checkbox_size
            + 112
        )
        return width, height

    def add(self) -> None:
        y = self.origin_y

        self.plotter.add_text(
            f"{self.grid.name.title()} grid",
            position=(self.origin_x, y),
            font_size=self.font_size + 2,
            color="#202020",
        )
        y -= 34

        y = self._add_checkbox_row(
            title="Show grid",
            y=y,
            callback=self._set_grid_enabled,
            indent=0,
            border_size=2,
        )

        y -= 7

        y = self._add_family(
            title="All meridians",
            values=list(self.grid.meridians),
            y=y,
            master_callback=self._set_meridians_enabled,
            item_callback_factory=self._meridian_callback,
        )

        y -= 9

        self._add_family(
            title="All parallels",
            values=list(self.grid.parallels),
            y=y,
            master_callback=self._set_parallels_enabled,
            item_callback_factory=self._parallel_callback,
        )

    def _add_checkbox_row(
        self,
        *,
        title: str,
        y: int,
        callback: CheckboxCallback,
        indent: int,
        border_size: int,
    ) -> int:
        x = self.origin_x + indent

        widget = self.plotter.add_checkbox_button_widget(
            callback=callback,
            value=True,
            position=(x, y),
            size=self.checkbox_size,
            border_size=border_size,
            color_on=self.grid.style.color,
            color_off="#d4d4d4",
            background_color="#f7f6f2",
        )

        self.widgets.append(widget)

        self.plotter.add_text(
            title,
            position=(
                x + self.checkbox_size + 7,
                y,
            ),
            font_size=self.font_size,
            color="#202020",
        )

        return y - self.row_height

    def _add_family(
        self,
        *,
        title: str,
        values: list[float],
        y: int,
        master_callback: CheckboxCallback,
        item_callback_factory: Callable[
            [float],
            CheckboxCallback,
        ],
    ) -> int:
        y = self._add_checkbox_row(
            title=title,
            y=y,
            callback=master_callback,
            indent=0,
            border_size=2,
        )

        for raw_value in values:
            value = float(raw_value)

            y = self._add_checkbox_row(
                title=f"{value:g} deg",
                y=y,
                callback=item_callback_factory(value),
                indent=self.indent,
                border_size=1,
            )

        return y

    def _set_grid_enabled(self, enabled: bool) -> None:
        self.grid_enabled = bool(enabled)
        self._apply_all_visibility()

    def _set_meridians_enabled(self, enabled: bool) -> None:
        self.meridians_enabled = bool(enabled)
        self._apply_meridian_visibility()

    def _set_parallels_enabled(self, enabled: bool) -> None:
        self.parallels_enabled = bool(enabled)
        self._apply_parallel_visibility()

    def _meridian_callback(
        self,
        value: float,
    ) -> CheckboxCallback:
        def callback(selected: bool) -> None:
            self.meridian_states[value] = bool(selected)
            self._apply_one_meridian(value)

        return callback

    def _parallel_callback(
        self,
        value: float,
    ) -> CheckboxCallback:
        def callback(selected: bool) -> None:
            self.parallel_states[value] = bool(selected)
            self._apply_one_parallel(value)

        return callback

    def _apply_all_visibility(self) -> None:
        self._apply_meridian_visibility(render=False)
        self._apply_parallel_visibility(render=False)
        self.plotter.render()

    def _apply_meridian_visibility(
        self,
        *,
        render: bool = True,
    ) -> None:
        for value in self.meridian_states:
            self._apply_one_meridian(
                value,
                render=False,
            )

        if render:
            self.plotter.render()

    def _apply_parallel_visibility(
        self,
        *,
        render: bool = True,
    ) -> None:
        for value in self.parallel_states:
            self._apply_one_parallel(
                value,
                render=False,
            )

        if render:
            self.plotter.render()

    def _apply_one_meridian(
        self,
        value: float,
        *,
        render: bool = True,
    ) -> None:
        visible = (
            self.grid_enabled
            and self.meridians_enabled
            and self.meridian_states[value]
        )

        self.grid.set_meridian_visible(
            value,
            visible,
        )

        if render:
            self.plotter.render()

    def _apply_one_parallel(
        self,
        value: float,
        *,
        render: bool = True,
    ) -> None:
        visible = (
            self.grid_enabled
            and self.parallels_enabled
            and self.parallel_states[value]
        )

        self.grid.set_parallel_visible(
            value,
            visible,
        )

        if render:
            self.plotter.render()


@dataclass(frozen=True)
class PanelPlacement:
    """Pixel-space placement assigned to a registered control panel."""

    origin_x: int
    origin_y: int
    width: int
    height: int


@dataclass
class ControlManager:
    """
    Own control panels, assign their layout, and coalesce render requests.

    This first M5 increment deliberately manages existing panels without
    changing their contents. Panel migration can therefore remain incremental.
    """

    plotter: pv.Plotter
    window_size: tuple[int, int] | None = None
    margin: int = 20
    panel_gap: int = 12

    panels: list[ControlPanel] = field(
        default_factory=list,
        init=False,
    )
    placements: list[PanelPlacement] = field(
        default_factory=list,
        init=False,
    )

    _cursor_x: int = field(default=0, init=False, repr=False)
    _cursor_y: int = field(default=0, init=False, repr=False)
    _column_width: int = field(default=0, init=False, repr=False)
    _batch_depth: int = field(default=0, init=False, repr=False)
    _render_pending: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.window_size is None:
            self.window_size = tuple(
                int(value)
                for value in self.plotter.window_size
            )

        if (
            len(self.window_size) != 2
            or any(value <= 0 for value in self.window_size)
        ):
            raise ValueError(
                "Control window_size must contain two positive values."
            )
        if self.margin < 0:
            raise ValueError("Control margin cannot be negative.")
        if self.panel_gap < 0:
            raise ValueError("Control panel_gap cannot be negative.")

        self._cursor_x = self.margin
        self._cursor_y = self.window_size[1] - self.margin

    def register_panel(
        self,
        panel: PanelT,
    ) -> PanelT:
        """Place, add, and retain one panel for the scene lifetime."""
        if any(existing is panel for existing in self.panels):
            raise ValueError("Control panel is already registered.")
        width, height = panel.control_size
        if width <= 0 or height <= 0:
            raise ValueError(
                "Control panel width and height must be positive."
            )

        window_width, window_height = self.window_size
        available_width = window_width - 2 * self.margin
        available_height = window_height - 2 * self.margin
        if width > available_width or height > available_height:
            raise ValueError(
                "Control panel does not fit within the configured window."
            )

        origin_x = self._cursor_x
        origin_y = self._cursor_y
        column_width = self._column_width

        if (
            self.panels
            and origin_y - height < self.margin
        ):
            origin_x += column_width + self.panel_gap
            origin_y = window_height - self.margin
            column_width = 0

        if origin_x + width > window_width - self.margin:
            raise ValueError(
                "No control-panel space remains in the configured window."
            )

        panel.origin_x = origin_x
        panel.origin_y = origin_y
        panel.add()

        placement = PanelPlacement(
            origin_x=origin_x,
            origin_y=origin_y,
            width=width,
            height=height,
        )
        self.panels.append(panel)
        self.placements.append(placement)

        self._cursor_x = origin_x
        self._cursor_y = origin_y - height - self.panel_gap
        self._column_width = max(column_width, width)
        return panel

    def request_render(self) -> None:
        """Render immediately, or once when the current batch completes."""
        if self._batch_depth:
            self._render_pending = True
            return
        self.plotter.render()

    @contextmanager
    def batch_render(self) -> Iterator[None]:
        """Coalesce any number of nested render requests into one render."""
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0 and self._render_pending:
                self._render_pending = False
                self.plotter.render()
