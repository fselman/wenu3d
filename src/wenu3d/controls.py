from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

import pyvista as pv

from .annotations import AnnotationLayer
from .grid import GridLayer


CheckboxCallback = Callable[[bool], None]
SliderCallback = Callable[[float], None]

PanelT = TypeVar("PanelT", bound="ControlPanel")


class ControlPanel(Protocol):
    origin_x: int
    origin_y: int

    @property
    def control_size(self) -> tuple[int, int]: ...

    def add(self) -> None: ...


def _configure_slider_text(widget: object) -> None:
    """Keep the numeric label inside the panel's declared footprint."""
    representation = widget.GetRepresentation()
    representation.SetLabelHeight(0.014)


@dataclass
class AnnotationControlPanel:
    """Managed visibility and text-size controls for annotation layers."""

    plotter: pv.Plotter
    layers: Sequence[AnnotationLayer]

    origin_x: int = 20
    origin_y: int = 960

    width: int = 300
    height: int = 160
    checkbox_size: int = 22
    font_size: int = 11
    color: str = "#506070"

    widgets: list[object] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        self.layers = tuple(self.layers)
        if not self.layers:
            raise ValueError(
                "AnnotationControlPanel requires at least one layer."
            )
        if not all(
            isinstance(layer, AnnotationLayer)
            for layer in self.layers
        ):
            raise TypeError(
                "Annotation controls require AnnotationLayer instances."
            )

    @property
    def control_size(self) -> tuple[int, int]:
        return self.width, self.height

    def add(self) -> None:
        title = self.plotter.add_text(
            "Anotaciones",
            position=(self.origin_x, self.origin_y),
            font_size=self.font_size + 2,
            color="#202020",
        )
        self.widgets.append(title)

        checkbox_y = self.origin_y - 38
        checkbox = self.plotter.add_checkbox_button_widget(
            callback=self._set_visible,
            value=all(layer.visible for layer in self.layers),
            position=(self.origin_x, checkbox_y),
            size=self.checkbox_size,
            border_size=2,
            color_on=self.color,
            color_off="#d4d4d4",
            background_color="#f7f6f2",
        )
        self.widgets.append(checkbox)

        label = self.plotter.add_text(
            "Mostrar anotaciones",
            position=(
                self.origin_x + self.checkbox_size + 7,
                checkbox_y,
            ),
            font_size=self.font_size,
            color="#202020",
        )
        self.widgets.append(label)

        window_width, window_height = (
            float(value)
            for value in self.plotter.window_size
        )
        slider_y = self.origin_y - 112
        slider = self.plotter.add_slider_widget(
            callback=self._set_font_size_scale,
            rng=(0.75, 2.50),
            value=self.layers[0].font_size_scale,
            title="Tamaño de anotaciones",
            pointa=(
                (self.origin_x + 10) / window_width,
                slider_y / window_height,
            ),
            pointb=(
                (self.origin_x + self.width - 10) / window_width,
                slider_y / window_height,
            ),
            style="modern",
            fmt="%.2f x",
            title_height=0.014,
            slider_width=0.018,
            tube_width=0.008,
        )
        _configure_slider_text(slider)
        self.widgets.append(slider)

    def _set_visible(self, visible: bool) -> None:
        for layer in self.layers:
            layer.set_visible(visible, render=False)
        self.plotter.render()

    def _set_font_size_scale(self, scale: float) -> None:
        for layer in self.layers:
            layer.set_font_size_scale(scale, render=False)
        self.plotter.render()


@dataclass
class GlobalControlPanel:
    """Managed controls for the celestial shell and local illustration."""

    plotter: pv.Plotter
    set_sphere_presence: SliderCallback
    set_local_scale: SliderCallback

    origin_x: int = 20
    origin_y: int = 960

    width: int = 340
    height: int = 230
    font_size: int = 11
    sphere_presence: float = 1.0
    local_scale: float = 1.0

    widgets: list[object] = field(
        default_factory=list,
        init=False,
    )

    @property
    def control_size(self) -> tuple[int, int]:
        return self.width, self.height

    def add(self) -> None:
        title = self.plotter.add_text(
            "Scene controls",
            position=(self.origin_x, self.origin_y),
            font_size=self.font_size + 2,
            color="#202020",
        )
        self.widgets.append(title)

        first_y = self.origin_y - 78
        sphere_slider = self._add_slider(
            callback=self.set_sphere_presence,
            value=self.sphere_presence,
            rng=(0.20, 3.00),
            title="Celestial sphere",
            y=first_y,
        )
        self.widgets.append(sphere_slider)

        second_y = self.origin_y - 175
        local_slider = self._add_slider(
            callback=self.set_local_scale,
            value=self.local_scale,
            rng=(0.05, 2.00),
            title="Earth / plane / observer",
            y=second_y,
        )
        self.widgets.append(local_slider)

    def _add_slider(
        self,
        *,
        callback: SliderCallback,
        value: float,
        rng: tuple[float, float],
        title: str,
        y: int,
    ) -> object:
        slider = self.plotter.add_slider_widget(
            callback=callback,
            rng=rng,
            value=value,
            title=title,
            pointa=self._normalized_point(
                self.origin_x + 15,
                y,
            ),
            pointb=self._normalized_point(
                self.origin_x + self.width - 15,
                y,
            ),
            style="modern",
            fmt="%.2f x",
            title_height=0.014,
            slider_width=0.018,
            tube_width=0.008,
        )
        _configure_slider_text(slider)
        return slider

    def _normalized_point(
        self,
        x: int,
        y: int,
    ) -> tuple[float, float]:
        window_width, window_height = (
            float(value)
            for value in self.plotter.window_size
        )
        return x / window_width, y / window_height


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

    def overlaps(self, other: PanelPlacement) -> bool:
        """Return whether two declared panel rectangles intersect."""
        return not (
            self.origin_x + self.width <= other.origin_x
            or other.origin_x + other.width <= self.origin_x
            or self.origin_y - self.height >= other.origin_y
            or other.origin_y - other.height >= self.origin_y
        )


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
    top_margin: int = 80
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
        if self.top_margin < 0:
            raise ValueError("Control top_margin cannot be negative.")
        if self.panel_gap < 0:
            raise ValueError("Control panel_gap cannot be negative.")

        self._cursor_x = self.margin
        self._cursor_y = self.window_size[1] - self.top_margin

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
        available_height = (
            window_height
            - self.top_margin
            - self.margin
        )
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
            origin_y = window_height - self.top_margin
            column_width = 0

        if origin_x + width > window_width - self.margin:
            raise ValueError(
                "No control-panel space remains in the configured window."
            )

        placement = PanelPlacement(
            origin_x=origin_x,
            origin_y=origin_y,
            width=width,
            height=height,
        )
        if any(
            placement.overlaps(existing)
            for existing in self.placements
        ):
            raise RuntimeError(
                "Calculated control-panel placement overlaps an existing panel."
            )

        panel.origin_x = origin_x
        panel.origin_y = origin_y
        panel.add()

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
