from __future__ import annotations

from collections.abc import Iterable

from .earth import EarthObject
from .layer import Layer
from .observer import ObserverComposition, ObserverRepresentation
from .scene_object import SceneObject
from .segments import SegmentStyle, SightLine
from .transforms import LocalCartoonTransform


class LocalCartoonLayer(Layer):
    """The shared Earth and finite observer compositions in one graph layer."""

    def __init__(
        self,
        *,
        name: str,
        earth: EarthObject,
        transform: LocalCartoonTransform | None = None,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(earth, EarthObject):
            raise TypeError("earth must be an EarthObject.")
        if transform is None:
            transform = LocalCartoonTransform.identity()
        if not isinstance(transform, LocalCartoonTransform):
            raise TypeError("transform must be a LocalCartoonTransform.")
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.earth = earth
        self.transform = transform
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
        *,
        render: bool = True,
    ) -> ObserverComposition:
        if not isinstance(composition, ObserverComposition):
            raise TypeError("composition must be an ObserverComposition.")
        observer_name = composition.observer.name
        if observer_name in self._observer_compositions:
            raise ValueError(f"Observer already exists: {observer_name}")
        self._observer_compositions[observer_name] = composition
        super().add(composition)
        plotter = self.attached_plotter
        if plotter is not None:
            composition.build(plotter)
            composition._set_ancestor_visible(self.effective_visible)
            self._apply_actor_transform(composition.actors)
            self.actors.extend(composition.actors)
            if render:
                plotter.render()
        return composition

    def get_observer(self, name: str) -> ObserverComposition:
        return self._observer_compositions[name]

    def set_observer_representation(
        self,
        observer: str,
        representation: ObserverRepresentation,
        *,
        render: bool = True,
    ) -> None:
        composition = self.get_observer(observer)
        composition.set_representation(representation, render=False)
        if self.attached_plotter is not None:
            composition._set_ancestor_visible(self.effective_visible)
            self.actors = [
                actor
                for obj in self.objects
                for actor in obj.actors
            ]
            self._apply_actor_transform(composition.actors)
            self._request_render(render)

    def set_transform(
        self,
        transform: LocalCartoonTransform,
        *,
        render: bool = True,
    ) -> None:
        if not isinstance(transform, LocalCartoonTransform):
            raise TypeError("transform must be a LocalCartoonTransform.")
        self.transform = transform
        self._apply_actor_transform()
        self._request_render(render)

    def transform_points(self, points):
        return self.transform.apply_points(points)

    def observer_position(self, observer: str):
        composition = self.get_observer(observer)
        return self.transform.apply_points(composition.observer.position)

    def observer_anchor(self, observer: str, anchor: str):
        composition = self.get_observer(observer)
        return self.transform.apply_points(composition.anchor(anchor))

    def make_observer_sight_line(
        self,
        *,
        observer: str,
        anchor: str,
        target_position,
        style: SegmentStyle | None = None,
        visible: bool = True,
    ) -> SightLine:
        """Snapshot a finite sight line from one transformed named anchor."""
        return SightLine(
            observer_position=self.observer_anchor(observer, anchor),
            target_position=target_position,
            style=style or SegmentStyle(),
            visible=visible,
        )

    def set_scale(self, scale: float, *, render: bool = True) -> None:
        self.set_transform(
            LocalCartoonTransform(
                translation=self.transform.translation,
                scale=scale,
            ),
            render=render,
        )

    def place_on_surface(
        self,
        *,
        observer: str,
        render: bool = True,
    ) -> None:
        """Restore nominal Earth-relative placement for ``observer``."""
        self.get_observer(observer)
        self.set_transform(
            LocalCartoonTransform(scale=self.transform.scale),
            render=render,
        )

    def place_observer_anchor_at_origin(
        self,
        *,
        observer: str,
        anchor: str,
        render: bool = True,
    ) -> None:
        """Translate the local cartoon so a semantic anchor reaches origin."""
        composition = self.get_observer(observer)
        anchor_position = composition.anchor(anchor)
        transform = LocalCartoonTransform(
            translation=-self.transform.scale * anchor_position,
            scale=self.transform.scale,
        )
        self.set_transform(transform, render=render)

    def build(self, plotter) -> None:
        super().build(plotter)
        self._apply_actor_transform()

    def _apply_actor_transform(self, actors=None) -> None:
        matrix = self.transform.matrix
        for actor in self.actors if actors is None else actors:
            actor.user_matrix = matrix
