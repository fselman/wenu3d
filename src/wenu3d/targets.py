from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace

import numpy as np

from .markers import Marker, MarkerStyle


Vector3 = tuple[float, float, float]


def _unit_direction(value: Sequence[float]) -> Vector3:
    direction = np.asarray(value, dtype=float)
    if direction.shape != (3,):
        raise ValueError("Target direction must contain exactly three values.")
    if not np.all(np.isfinite(direction)):
        raise ValueError("Target direction must contain only finite values.")
    norm = float(np.linalg.norm(direction))
    if norm == 0.0:
        raise ValueError("Target direction must be non-zero.")
    return tuple(float(component) for component in direction / norm)


@dataclass(frozen=True)
class CelestialTarget:
    """A celestial direction with one derived finite shell marker."""

    name: str
    direction: Sequence[float]
    shell_radius: float = 1.0
    marker_style: MarkerStyle = field(default_factory=MarkerStyle)
    visible: bool = True

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("Target name must not be empty.")
        radius = float(self.shell_radius)
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError(
                "Target shell radius must be finite and greater than zero."
            )
        if not isinstance(self.marker_style, MarkerStyle):
            raise TypeError("Target marker_style must be a MarkerStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("Target visible must be a boolean.")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "direction", _unit_direction(self.direction))
        object.__setattr__(self, "shell_radius", radius)
        object.__setattr__(self, "visible", bool(self.visible))

    @property
    def display_position(self) -> Vector3:
        return tuple(
            self.shell_radius * component for component in self.direction
        )

    def as_marker(self) -> Marker:
        """Return the finite marker derived from this target."""
        return Marker(
            position=self.display_position,
            style=self.marker_style,
            visible=self.visible,
        )

    def at_shell_radius(self, shell_radius: float) -> CelestialTarget:
        """Return this target displayed at another illustrative radius."""
        return replace(self, shell_radius=shell_radius)
