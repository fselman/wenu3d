from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

import numpy as np

from .local_cartoon import LocalCartoonLayer
from .transforms import LocalCartoonTransform


ScaleComparisonMode = Literal[
    "surface",
    "small_cartoon",
    "observer_at_origin",
]


@dataclass(frozen=True)
class ScaleComparisonState:
    """One named, reproducible local-cartoon presentation state."""

    name: ScaleComparisonMode
    transform: LocalCartoonTransform
    description: str


class LocalScaleComparison:
    """Apply explicit local transforms while celestial geometry stays fixed."""

    def __init__(
        self,
        *,
        local_cartoon: LocalCartoonLayer,
        observer: str,
        anchor: str,
        surface_scale: float = 1.0,
        small_scale: float = 0.1,
        observer_origin_scale: float = 1.0,
    ) -> None:
        if not isinstance(local_cartoon, LocalCartoonLayer):
            raise TypeError("local_cartoon must be a LocalCartoonLayer.")
        observer_name = str(observer).strip()
        anchor_name = str(anchor).strip()
        if not observer_name:
            raise ValueError("observer must not be empty.")
        if not anchor_name:
            raise ValueError("anchor must not be empty.")
        composition = local_cartoon.get_observer(observer_name)
        anchor_position = composition.anchor(anchor_name)

        surface = LocalCartoonTransform(scale=surface_scale)
        small = LocalCartoonTransform(scale=small_scale)
        observer_origin = LocalCartoonTransform(
            translation=-float(observer_origin_scale) * anchor_position,
            scale=observer_origin_scale,
        )
        self.local_cartoon = local_cartoon
        self.observer = observer_name
        self.anchor = anchor_name
        self._states = MappingProxyType({
            "surface": ScaleComparisonState(
                name="surface",
                transform=surface,
                description="Local cartoon at explicit surface scale.",
            ),
            "small_cartoon": ScaleComparisonState(
                name="small_cartoon",
                transform=small,
                description=(
                    "Reduced local cartoon approaching the directional limit."
                ),
            ),
            "observer_at_origin": ScaleComparisonState(
                name="observer_at_origin",
                transform=observer_origin,
                description=(
                    "Selected observer anchor aligned with celestial origin."
                ),
            ),
        })

    @property
    def states(self) -> tuple[ScaleComparisonState, ...]:
        return tuple(self._states.values())

    def state(self, mode: ScaleComparisonMode) -> ScaleComparisonState:
        try:
            return self._states[mode]
        except KeyError as error:
            raise ValueError(f"Unknown scale-comparison mode: {mode}") from error

    def apply(
        self,
        mode: ScaleComparisonMode,
        *,
        render: bool = True,
    ) -> ScaleComparisonState:
        state = self.state(mode)
        self.local_cartoon.set_transform(state.transform, render=render)
        return state
