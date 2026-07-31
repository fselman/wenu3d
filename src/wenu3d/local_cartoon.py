from __future__ import annotations

from collections.abc import Iterable

from .earth import EarthObject
from .layer import Layer
from .observer import ObserverComposition
from .scene_object import SceneObject


class LocalCartoonLayer(Layer):
    """The shared Earth and finite observer compositions in one graph layer."""

    def __init__(
        self,
        *,
        name: str,
        earth: EarthObject,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(earth, EarthObject):
            raise TypeError("earth must be an EarthObject.")
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.earth = earth
        self._observer_compositions: dict[str, ObserverComposition] = {}
        super().add(earth)

    def add(self, obj: SceneObject) -> SceneObject:
        if isinstance(obj, EarthObject):
            if obj is self.earth:
                raise ValueError("The shared Earth is already registered.")
            raise ValueError("LocalCartoonLayer owns exactly one shared Earth.")
        if isinstance(obj, ObserverComposition):
            return self.add_observer(obj)
        return super().add(obj)

    def extend(self, objects: Iterable[SceneObject]) -> None:
        for obj in objects:
            self.add(obj)

    @property
    def observer_compositions(self) -> tuple[ObserverComposition, ...]:
        return tuple(self._observer_compositions.values())

    def add_observer(
        self,
        composition: ObserverComposition,
    ) -> ObserverComposition:
        if not isinstance(composition, ObserverComposition):
            raise TypeError("composition must be an ObserverComposition.")
        observer_name = composition.observer.name
        if observer_name in self._observer_compositions:
            raise ValueError(f"Observer already exists: {observer_name}")
        self._observer_compositions[observer_name] = composition
        super().add(composition)
        return composition

    def get_observer(self, name: str) -> ObserverComposition:
        return self._observer_compositions[name]
