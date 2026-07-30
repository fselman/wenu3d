from __future__ import annotations

from dataclasses import dataclass, field

import pyvista as pv


@dataclass
class SceneObject:
    """
    Base class for a drawable scene object.

    A SceneObject owns its PyVista actors and exposes uniform visibility and
    opacity controls. Subclasses implement build().
    """

    name: str
    visible: bool = True
    opacity: float = 1.0
    actors: list[pv.Actor] = field(default_factory=list, init=False)
    _plotter: pv.Plotter | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _ancestor_visible: bool = field(
        default=True,
        init=False,
        repr=False,
    )

    def build(self, plotter: pv.Plotter) -> None:
        raise NotImplementedError

    @property
    def attached_plotter(self) -> pv.Plotter | None:
        return self._plotter

    @property
    def effective_visible(self) -> bool:
        return self.visible and self._ancestor_visible

    def _prepare_build(self, plotter: pv.Plotter) -> None:
        """Remove an earlier build and attach this object to ``plotter``."""
        self.detach(render=False)
        self._plotter = plotter

    def add_actor(self, actor: pv.Actor) -> pv.Actor:
        self.actors.append(actor)
        self._apply_actor_state(actor)
        return actor

    def detach(self, *, render: bool = True) -> None:
        """Remove all owned actors from the attached plotter."""
        plotter = self._plotter
        if plotter is not None:
            for actor in tuple(self.actors):
                plotter.remove_actor(actor, render=False)
        self.actors.clear()
        self._plotter = None
        if render and plotter is not None:
            plotter.render()

    def _request_render(self, render: bool) -> None:
        if render and self._plotter is not None:
            self._plotter.render()

    def _set_ancestor_visible(self, visible: bool) -> None:
        self._ancestor_visible = bool(visible)
        for actor in self.actors:
            actor.SetVisibility(self.effective_visible)

    def _apply_actor_state(self, actor: pv.Actor) -> None:
        actor.SetVisibility(self.effective_visible)
        prop = actor.GetProperty()
        if prop is not None:
            prop.SetOpacity(float(self.opacity))

    def set_visible(self, visible: bool, *, render: bool = True) -> None:
        self.visible = bool(visible)
        for actor in self.actors:
            actor.SetVisibility(self.effective_visible)
        self._request_render(render)

    def set_opacity(
        self,
        opacity: float,
        *,
        render: bool = True,
    ) -> None:
        self.opacity = float(opacity)
        for actor in self.actors:
            prop = actor.GetProperty()
            if prop is not None:
                prop.SetOpacity(self.opacity)
        self._request_render(render)
