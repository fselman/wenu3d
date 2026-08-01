from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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

    def export(
        self,
        directory: str | Path,
        *,
        modes: tuple[ScaleComparisonMode, ...] | None = None,
        window_size: tuple[int, int] | None = None,
        transparent_background: bool = False,
    ) -> dict[ScaleComparisonMode, np.ndarray]:
        """Save deterministic PNG snapshots and restore the prior transform."""
        plotter = self.local_cartoon.attached_plotter
        if plotter is None:
            raise RuntimeError("Scale-comparison export requires a built layer.")
        if modes is None:
            modes = tuple(state.name for state in self.states)
        if not isinstance(modes, tuple) or not modes:
            raise ValueError("modes must be a nonempty tuple.")
        if len(set(modes)) != len(modes):
            raise ValueError("modes must not contain duplicates.")
        selected = tuple(self.state(mode) for mode in modes)
        if window_size is not None:
            if (
                not isinstance(window_size, tuple)
                or len(window_size) != 2
                or any(
                    isinstance(value, (bool, np.bool_))
                    or not isinstance(value, (int, np.integer))
                    or value <= 0
                    for value in window_size
                )
            ):
                raise ValueError("window_size must contain two positive integers.")
        if not isinstance(transparent_background, (bool, np.bool_)):
            raise TypeError("transparent_background must be a boolean.")

        output_directory = Path(directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        original = self.local_cartoon.transform
        images: dict[ScaleComparisonMode, np.ndarray] = {}
        try:
            for state in selected:
                self.local_cartoon.set_transform(state.transform, render=False)
                plotter.render()
                options = {
                    "filename": output_directory / f"{state.name}.png",
                    "transparent_background": bool(transparent_background),
                    "return_img": True,
                }
                if window_size is not None:
                    options["window_size"] = window_size
                image = plotter.screenshot(**options)
                if image is None:
                    raise RuntimeError(
                        f"PyVista returned no image for state: {state.name}"
                    )
                images[state.name] = image
        finally:
            self.local_cartoon.set_transform(original, render=False)
            plotter.render()
        return images
