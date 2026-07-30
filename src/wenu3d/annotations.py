from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
import pyvista as pv

from .layer import Layer
from .scene_object import SceneObject


Vector3 = tuple[float, float, float]


def _vector3(value: Sequence[float], *, field_name: str) -> Vector3:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{field_name} must contain exactly three values.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return tuple(float(component) for component in vector)


@dataclass(frozen=True)
class AnnotationStyle:
    """Renderer-neutral text styling for an annotation."""

    color: str = "#222222"
    font_size: int = 14
    bold: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Annotation color must be a non-empty string.")
        if (
            not isinstance(self.font_size, int)
            or isinstance(self.font_size, bool)
            or self.font_size <= 0
        ):
            raise ValueError("Annotation font_size must be a positive integer.")
        if not isinstance(self.bold, bool):
            raise TypeError("Annotation bold must be a boolean.")
        object.__setattr__(self, "color", self.color.strip())


@dataclass(frozen=True)
class Annotation:
    """
    Renderer-neutral description of text anchored in a 3D scene.

    ``offset`` is a world-coordinate displacement from ``anchor`` to the text
    position. ``associated_with`` may name the scene object being described.
    """

    text: str
    anchor: Sequence[float]
    offset: Sequence[float] = (0.0, 0.0, 0.0)
    style: AnnotationStyle = field(default_factory=AnnotationStyle)
    visible: bool = True
    associated_with: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Annotation text must be a non-empty string.")
        if not isinstance(self.style, AnnotationStyle):
            raise TypeError("Annotation style must be an AnnotationStyle.")
        if not isinstance(self.visible, (bool, np.bool_)):
            raise TypeError("Annotation visible must be a boolean.")

        association = self.associated_with
        if association is not None:
            if not isinstance(association, str) or not association.strip():
                raise ValueError(
                    "associated_with must be a non-empty string or None."
                )
            association = association.strip()

        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(
            self,
            "anchor",
            _vector3(self.anchor, field_name="anchor"),
        )
        object.__setattr__(
            self,
            "offset",
            _vector3(self.offset, field_name="offset"),
        )
        object.__setattr__(self, "visible", bool(self.visible))
        object.__setattr__(self, "associated_with", association)

    @property
    def position(self) -> Vector3:
        """Return the world-coordinate text position."""
        return tuple(
            anchor + offset
            for anchor, offset in zip(self.anchor, self.offset, strict=True)
        )


@dataclass
class AnnotationObject(SceneObject):
    """Lifecycle-managed PyVista representation of one annotation."""

    annotation: Annotation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.annotation, Annotation):
            raise TypeError(
                "AnnotationObject annotation must be an Annotation."
            )
        self.visible = self.visible and self.annotation.visible

    def build(self, plotter: pv.Plotter) -> None:
        if self.annotation is None:
            raise TypeError(
                "AnnotationObject annotation must be an Annotation."
            )

        self._prepare_build(plotter)
        actor = plotter.add_point_labels(
            [self.annotation.position],
            [self.annotation.text],
            bold=self.annotation.style.bold,
            font_size=self.annotation.style.font_size,
            text_color=self.annotation.style.color,
            show_points=False,
            shape=None,
            always_visible=True,
            name=self.name,
            reset_camera=False,
            render=False,
        )
        self.add_actor(actor)


@dataclass
class AnnotationLayer(Layer):
    """A layer of independently addressable annotation objects."""

    def add_annotation(
        self,
        name: str,
        annotation: Annotation,
    ) -> AnnotationObject:
        obj = AnnotationObject(
            name=name,
            annotation=annotation,
        )
        self.add(obj)
        return obj
