from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable
import numpy as np
import pyvista as pv

from .grid import GridLabel


def _vtk_ascii(text: str) -> str:
    """Return a VTK-safe ASCII label string."""
    replacements = {
        "°": " deg",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("ascii", errors="replace").decode("ascii")


@dataclass
class LabelLayer:
    """
    A replaceable set of 3D point labels.

    PyVista point-label font size is not reliably mutable after creation,
    so the slider rebuilds only this lightweight actor.
    """

    plotter: pv.Plotter
    labels: list[GridLabel] = field(default_factory=list)
    font_size: int = 16
    text_color: str = "#222222"
    name: str = "labels"
    actor: object | None = None

    def extend(self, labels: Iterable[GridLabel]) -> None:
        self.labels.extend(labels)

    def clear(self) -> None:
        self.labels.clear()
        self._remove_actor()

    def _remove_actor(self) -> None:
        if self.actor is not None:
            try:
                self.plotter.remove_actor(self.actor, render=False)
            except Exception:
                pass
            self.actor = None

    def draw(self) -> None:
        self._remove_actor()

        if not self.labels:
            return

        points = np.array([label.position for label in self.labels])
        texts = [_vtk_ascii(label.text) for label in self.labels]

        dataset = pv.PolyData(points)
        dataset["labels"] = texts

        self.actor = self.plotter.add_point_labels(
            dataset,
            "labels",
            name=self.name,
            font_size=int(self.font_size),
            text_color=self.text_color,
            point_size=0,
            shape=None,
            always_visible=True,
            render=False,
        )

    def set_font_size(self, value: float) -> None:
        self.font_size = max(6, int(round(value)))
        self.draw()
        self.plotter.render()
