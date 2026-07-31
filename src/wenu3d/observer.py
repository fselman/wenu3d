from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping

import numpy as np
import pyvista as pv

from .frames import SphericalFrame
from .geometry import unit
from .layer import Layer
from .observer_model import Observer
from .rendering import add_tube
from .scene_object import SceneObject


class ObserverRepresentation(SceneObject, ABC):
    """Replaceable drawable representation of one semantic observer."""

    def __init__(
        self,
        *,
        name: str,
        observer: Observer,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(observer, Observer):
            raise TypeError("observer must be an Observer.")
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.observer = observer

    @property
    @abstractmethod
    def anchors(self) -> Mapping[str, np.ndarray]:
        """Return representation-provided anchors in world coordinates."""

    def anchor(self, name: str) -> np.ndarray:
        key = str(name).strip()
        try:
            anchor = self.anchors[key]
        except KeyError as error:
            raise KeyError(f"Unknown observer anchor: {key}") from error
        return np.asarray(anchor, dtype=float).copy()


class StickFigureRepresentation(ObserverRepresentation):
    """The existing seven-actor observer figure with semantic anchors."""

    def __init__(
        self,
        *,
        name: str,
        observer: Observer,
        height: float,
        body_color: str = "#474747",
        head_color: str = "#d4af8a",
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        height = float(height)
        if not np.isfinite(height) or height <= 0.0:
            raise ValueError("Observer height must be finite and greater than zero.")
        super().__init__(
            name=name,
            observer=observer,
            visible=visible,
            opacity=opacity,
        )
        self.height = height
        self.body_color = str(body_color)
        self.head_color = str(head_color)

    @property
    def anchors(self) -> Mapping[str, np.ndarray]:
        feet = self.observer.position
        zenith = self.observer.frame.pole
        east = self.observer.frame.east
        height = self.height
        return {
            "feet": feet.copy(),
            "left_foot": feet - 0.10 * height * east,
            "right_foot": feet + 0.10 * height * east,
            "hips": feet + 0.38 * height * zenith,
            "shoulders": feet + 0.68 * height * zenith,
            "neck": feet + 0.78 * height * zenith,
            "head": feet + 0.90 * height * zenith,
            "eye": feet + 0.90 * height * zenith,
        }

    def build(self, plotter: pv.Plotter) -> None:
        self._prepare_build(plotter)
        anchors = self.anchors
        height = self.height
        east = self.observer.frame.east
        left_hand = anchors["shoulders"] - 0.20 * height * east
        right_hand = anchors["shoulders"] + 0.20 * height * east
        radius = 0.018 * height

        for start, end in (
            (anchors["hips"], anchors["shoulders"]),
            (anchors["hips"], anchors["left_foot"]),
            (anchors["hips"], anchors["right_foot"]),
            (anchors["shoulders"], left_hand),
            (anchors["shoulders"], right_hand),
            (anchors["shoulders"], anchors["neck"]),
        ):
            self.add_actor(
                add_tube(
                    plotter,
                    np.vstack([start, end]),
                    color=self.body_color,
                    radius=radius,
                )
            )

        self.add_actor(
            plotter.add_mesh(
                pv.Sphere(
                    radius=0.09 * height,
                    center=anchors["head"],
                ),
                color=self.head_color,
                smooth_shading=True,
            )
        )


class ObserverComposition(Layer):
    """A semantic observer, its replaceable representation, and context."""

    def __init__(
        self,
        *,
        name: str,
        observer: Observer,
        representation: ObserverRepresentation,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(observer, Observer):
            raise TypeError("observer must be an Observer.")
        self._validate_representation(observer, representation)
        super().__init__(name=name, visible=visible, opacity=opacity)
        self.observer = observer
        self.representation = representation
        self.add(representation)

    @staticmethod
    def _validate_representation(
        observer: Observer,
        representation: ObserverRepresentation,
    ) -> None:
        if not isinstance(representation, ObserverRepresentation):
            raise TypeError(
                "representation must be an ObserverRepresentation."
            )
        if representation.observer is not observer:
            raise ValueError(
                "Representation must reference the composition observer."
            )

    @property
    def anchors(self) -> Mapping[str, np.ndarray]:
        return self.representation.anchors

    def anchor(self, name: str) -> np.ndarray:
        return self.representation.anchor(name)

    def set_representation(
        self,
        representation: ObserverRepresentation,
        *,
        render: bool = True,
    ) -> None:
        self._validate_representation(self.observer, representation)
        index = self.objects.index(self.representation)
        plotter = self.attached_plotter
        previous = self.representation
        previous.detach(render=False)
        self.representation = representation
        self.objects[index] = representation
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()


def tangent_plane(center, east, north, *, width, depth) -> pv.PolyData:
    e = unit(east)
    n = unit(north)
    hw = width / 2
    hd = depth / 2

    points = np.array([
        center - hw * e - hd * n,
        center + hw * e - hd * n,
        center + hw * e + hd * n,
        center - hw * e + hd * n,
    ])
    return pv.PolyData(points, np.array([4, 0, 1, 2, 3]))


def add_observer(plotter, *, base, zenith, east, height) -> list[pv.Actor]:
    """Build the legacy stick figure through its representation object."""
    z = unit(zenith)
    e = unit(east)
    north = unit(np.cross(z, e))
    observer = Observer(
        name="legacy_observer",
        position=base,
        frame=SphericalFrame(
            name="legacy_observer_enu",
            pole=z,
            zero=north,
            east=e,
        ),
    )
    representation = StickFigureRepresentation(
        name="legacy_observer.stick_figure",
        observer=observer,
        height=height,
    )
    representation.build(plotter)
    return list(representation.actors)
