from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pyvista as pv

from .rendering import add_tube
from .scene_object import SceneObject


@dataclass
class CelestialAxisObject(SceneObject):
    """Lifecycle-managed finite rendering of one celestial rotation axis."""

    direction: Sequence[float] = (0.0, 0.0, 1.0)
    half_length: float = 1.1
    tube_radius: float = 0.006
    color: str = "#333333"

    def __post_init__(self) -> None:
        direction = np.asarray(self.direction, dtype=float)
        if direction.shape != (3,) or not np.all(np.isfinite(direction)):
            raise ValueError("Axis direction must contain three finite values.")
        norm = float(np.linalg.norm(direction))
        if norm == 0.0:
            raise ValueError("Axis direction must be non-zero.")

        half_length = float(self.half_length)
        tube_radius = float(self.tube_radius)
        opacity = float(self.opacity)
        if not np.isfinite(half_length) or half_length <= 0.0:
            raise ValueError("Axis half-length must be finite and positive.")
        if not np.isfinite(tube_radius) or tube_radius <= 0.0:
            raise ValueError("Axis tube radius must be finite and positive.")
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Axis color must be a non-empty string.")
        if not np.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
            raise ValueError("Axis opacity must be between zero and one.")

        self.direction = tuple(float(value) for value in direction / norm)
        self.half_length = half_length
        self.tube_radius = tube_radius
        self.color = self.color.strip()
        self.opacity = opacity

    @property
    def points(self) -> np.ndarray:
        direction = np.asarray(self.direction)
        return np.vstack([
            -self.half_length * direction,
            self.half_length * direction,
        ])

    def build(self, plotter: pv.Plotter) -> None:
        self._prepare_build(plotter)
        actor = add_tube(
            plotter,
            self.points,
            color=self.color,
            radius=self.tube_radius,
            opacity=self.opacity,
            name=self.name,
        )
        self.add_actor(actor)
