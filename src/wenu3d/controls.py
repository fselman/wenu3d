from __future__ import annotations

from dataclasses import dataclass, field

import pyvista as pv

from .grid import GridLayer


@dataclass
class GridControlPanel:
    """
    Vertically aligned controls for one selected grid.

    The master controls show or hide all meridians or parallels.
    Individual curves can be changed while their family is enabled.
    """

    plotter: pv.Plotter
    grid: GridLayer
    origin_x: int = 20
    origin_y: int = 930
    row_height: int = 27
    checkbox_size: int = 20
    indent: int = 24
    font_size: int = 10

    meridians_enabled: bool = field(default=True, init=False)
    parallels_enabled: bool = field(default=True, init=False)

    def add(self) -> None:
        y = self.origin_y

        self.plotter.add_text(
            f"{self.grid.name.title()} grid",
            position=(self.origin_x, y),
            font_size=self.font_size + 2,
            color="#202020",
        )
        y -= 40

        y = self._add_family(
            title="All meridians",
            values=list(self.grid.meridians),
            y=y,
            master_callback=self._set_all_meridians,
            callback_factory=self._meridian_callback,
        )

        y -= 12

        self._add_family(
            title="All parallels",
            values=list(self.grid.parallels),
            y=y,
            master_callback=self._set_all_parallels,
            callback_factory=self._parallel_callback,
        )

    def _add_family(
        self,
        *,
        title: str,
        values: list[float],
        y: int,
        master_callback,
        callback_factory,
    ) -> int:
        self.plotter.add_checkbox_button_widget(
            callback=master_callback,
            value=True,
            position=(self.origin_x, y),
            size=self.checkbox_size,
            border_size=2,
            color_on=self.grid.style.color,
            color_off="#d8d8d8",
            background_color="#f7f6f2",
        )

        self.plotter.add_text(
            title,
            position=(self.origin_x + self.checkbox_size + 8, y + 1),
            font_size=self.font_size,
            color="#202020",
        )

        y -= self.row_height

        for value in values:
            self.plotter.add_checkbox_button_widget(
                callback=callback_factory(float(value)),
                value=True,
                position=(self.origin_x + self.indent, y),
                size=self.checkbox_size,
                border_size=2,
                color_on=self.grid.style.color,
                color_off="#d8d8d8",
                background_color="#f7f6f2",
            )

            self.plotter.add_text(
                f"{value:g} deg",
                position=(
                    self.origin_x
                    + self.indent
                    + self.checkbox_size
                    + 8,
                    y + 1,
                ),
                font_size=self.font_size,
                color="#202020",
            )

            y -= self.row_height

        return y

    def _set_all_meridians(self, visible: bool) -> None:
        self.meridians_enabled = bool(visible)
        self.grid.set_all_meridians_visible(self.meridians_enabled)
        self.plotter.render()

    def _set_all_parallels(self, visible: bool) -> None:
        self.parallels_enabled = bool(visible)
        self.grid.set_all_parallels_visible(self.parallels_enabled)
        self.plotter.render()

    def _meridian_callback(self, value: float):
        def callback(visible: bool) -> None:
            if not self.meridians_enabled:
                return

            self.grid.set_meridian_visible(value, bool(visible))
            self.plotter.render()

        return callback

    def _parallel_callback(self, value: float):
        def callback(visible: bool) -> None:
            if not self.parallels_enabled:
                return

            self.grid.set_parallel_visible(value, bool(visible))
            self.plotter.render()

        return callback
