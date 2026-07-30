from __future__ import annotations

from dataclasses import dataclass

import pyvista as pv

from .grid import GridLayer


@dataclass
class GridControlPanel:
    """
    Generates one checkbox per meridian and parallel.

    PyVista checkboxes use pixel coordinates, so the panel is arranged in two
    compact columns. It is intentionally simple and proves that GridLayer
    objects can be controlled independently.
    """

    plotter: pv.Plotter
    grid: GridLayer
    origin_x: int = 20
    origin_y: int = 150
    row_height: int = 30
    checkbox_size: int = 22
    column_width: int = 150
    font_size: int = 10

    def add(self) -> None:
        self._add_column(
            title=f"{self.grid.name}: meridians",
            values=list(self.grid.meridians.keys()),
            x=self.origin_x,
            callback_factory=self._meridian_callback,
        )
        self._add_column(
            title=f"{self.grid.name}: parallels",
            values=list(self.grid.parallels.keys()),
            x=self.origin_x + self.column_width,
            callback_factory=self._parallel_callback,
        )

    def _add_column(self, *, title, values, x, callback_factory) -> None:
        title_y = self.origin_y + self.row_height
        self.plotter.add_text(
            title,
            position=(x, title_y),
            font_size=self.font_size,
        )

        for index, value in enumerate(values):
            y = self.origin_y - index * self.row_height

            self.plotter.add_checkbox_button_widget(
                callback=callback_factory(value),
                value=True,
                position=(x, y),
                size=self.checkbox_size,
                border_size=2,
                color_on=self.grid.style.color,
                color_off="#d8d8d8",
                background_color="#f7f6f2",
            )
            self.plotter.add_text(
                f"{value:g} deg",
                position=(x + self.checkbox_size + 8, y + 2),
                font_size=self.font_size,
            )

    def _meridian_callback(self, value: float):
        def callback(visible: bool) -> None:
            self.grid.set_meridian_visible(value, bool(visible))
            self.plotter.render()
        return callback

    def _parallel_callback(self, value: float):
        def callback(visible: bool) -> None:
            self.grid.set_parallel_visible(value, bool(visible))
            self.plotter.render()
        return callback
