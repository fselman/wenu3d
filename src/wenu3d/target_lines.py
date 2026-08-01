from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from .annotations import Annotation, AnnotationObject, AnnotationStyle
from .illustration import IllustrationLayer
from .local_cartoon import LocalCartoonLayer
from .marker_object import MarkerObject
from .segment_object import SegmentObject
from .segments import LineSegment, SegmentStyle
from .targets import CelestialTarget


class TargetLineIllustration(IllustrationLayer):
    """Explicit centered direction and finite observer-to-target lines."""

    def __init__(
        self,
        *,
        name: str,
        target: CelestialTarget,
        local_cartoon: LocalCartoonLayer | None = None,
        observer_anchors: Mapping[str, str] | None = None,
        include_centered_direction: bool = True,
        direction_style: SegmentStyle | None = None,
        sight_line_style: SegmentStyle | None = None,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(target, CelestialTarget):
            raise TypeError("target must be a CelestialTarget.")
        if observer_anchors is None:
            observer_anchors = {}
        if not isinstance(observer_anchors, Mapping):
            raise TypeError("observer_anchors must be a mapping.")
        if not isinstance(include_centered_direction, (bool, np.bool_)):
            raise TypeError("include_centered_direction must be a boolean.")
        if direction_style is not None and not isinstance(
            direction_style,
            SegmentStyle,
        ):
            raise TypeError("direction_style must be a SegmentStyle.")
        if sight_line_style is not None and not isinstance(
            sight_line_style,
            SegmentStyle,
        ):
            raise TypeError("sight_line_style must be a SegmentStyle.")

        anchors: dict[str, str] = {}
        for observer, anchor in observer_anchors.items():
            if not isinstance(observer, str) or not observer.strip():
                raise ValueError("Observer names must be nonempty strings.")
            if not isinstance(anchor, str) or not anchor.strip():
                raise ValueError("Anchor names must be nonempty strings.")
            anchors[observer.strip()] = anchor.strip()
        if anchors and not isinstance(local_cartoon, LocalCartoonLayer):
            raise TypeError(
                "local_cartoon must be a LocalCartoonLayer for sight lines."
            )
        if not include_centered_direction and not anchors:
            raise ValueError("Target-line illustration must contain a line.")

        super().__init__(name=name, visible=visible, opacity=opacity)
        self.target = target
        self.local_cartoon = local_cartoon
        self.observer_anchors = anchors
        self.direction_style = direction_style or SegmentStyle(
            color="#656565",
            width=3.0,
            opacity=0.85,
        )
        self.sight_line_style = sight_line_style or SegmentStyle(
            color="#b05d4b",
            width=2.0,
            opacity=0.75,
        )
        self.include_centered_direction = bool(include_centered_direction)

        self.marker_object: MarkerObject = self.add_marker(
            f"{name}.target",
            target.as_marker(),
        )
        self.centered_direction_object: SegmentObject | None = None
        if self.include_centered_direction:
            self.centered_direction_object = self.add_segment(
                f"{name}.centered_direction",
                LineSegment(
                    start=(0.0, 0.0, 0.0),
                    end=target.display_position,
                    style=self.direction_style,
                ),
            )

        self.sight_line_objects: dict[str, SegmentObject] = {}
        if self.local_cartoon is not None:
            for observer, anchor in self.observer_anchors.items():
                obj = self.add_segment(
                    f"{name}.sight_line.{observer}",
                    self.local_cartoon.make_observer_sight_line(
                        observer=observer,
                        anchor=anchor,
                        target_position=target.display_position,
                        style=self.sight_line_style,
                    ),
                )
                self.sight_line_objects[observer] = obj

    def build(self, plotter) -> None:
        super().build(plotter)
        if self.local_cartoon is not None and self.observer_anchors:
            self.local_cartoon.register_transform_dependent(self)

    def detach(self, *, render: bool = True) -> None:
        if self.local_cartoon is not None:
            self.local_cartoon.unregister_transform_dependent(self)
        super().detach(render=render)

    def refresh_from_local_transform(
        self,
        *,
        render: bool = True,
    ) -> None:
        """Re-resolve finite sight-line origins after a local transform."""
        if self.local_cartoon is None:
            return
        for observer, anchor in self.observer_anchors.items():
            self.sight_line_objects[observer].segment = (
                self.local_cartoon.make_observer_sight_line(
                    observer=observer,
                    anchor=anchor,
                    target_position=self.target.display_position,
                    style=self.sight_line_style,
                )
            )
        plotter = self.attached_plotter
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()


class ParallaxIllustration(TargetLineIllustration):
    """Explicit finite-baseline convergence to an illustrative shell marker."""

    interpretation_note = (
        "Illustrative convergence to displayed shell marker; "
        "shell radius is not physical distance."
    )

    def __init__(
        self,
        *,
        name: str,
        target: CelestialTarget,
        local_cartoon: LocalCartoonLayer,
        observer_anchors: Mapping[str, str],
        include_centered_direction: bool = True,
        direction_style: SegmentStyle | None = None,
        sight_line_style: SegmentStyle | None = None,
        note_style: AnnotationStyle | None = None,
        show_note: bool = True,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(observer_anchors, Mapping):
            raise TypeError("observer_anchors must be a mapping.")
        if len(observer_anchors) < 2:
            raise ValueError("Parallax illustration requires at least two observers.")
        if note_style is not None and not isinstance(note_style, AnnotationStyle):
            raise TypeError("note_style must be an AnnotationStyle.")
        if not isinstance(show_note, (bool, np.bool_)):
            raise TypeError("show_note must be a boolean.")

        super().__init__(
            name=name,
            target=target,
            local_cartoon=local_cartoon,
            observer_anchors=observer_anchors,
            include_centered_direction=include_centered_direction,
            direction_style=direction_style,
            sight_line_style=sight_line_style,
            visible=visible,
            opacity=opacity,
        )
        self.note_style = note_style or AnnotationStyle(
            color="#6a4d3b",
            font_size=12,
        )
        self.show_note = bool(show_note)
        self.note_annotation: AnnotationObject | None = None
        if self.show_note:
            direction = np.asarray(self.target.direction)
            self.note_annotation = self.add_annotation(
                f"{name}.interpretation_note",
                Annotation(
                    text=self.interpretation_note,
                    anchor=self.target.display_position,
                    offset=0.07 * self.target.shell_radius * direction,
                    style=self.note_style,
                    associated_with=self.marker_object.name,
                ),
            )

    @property
    def display_distance(self) -> float:
        """Return the illustrative shell radius, never a physical distance."""
        return self.target.shell_radius

    def _observer_pair(self, first: str, second: str):
        if first == second:
            raise ValueError("Observer pair must contain two distinct names.")
        try:
            first_line = self.sight_line_objects[first].segment
            second_line = self.sight_line_objects[second].segment
        except KeyError as error:
            raise KeyError(f"Unknown parallax observer: {error.args[0]}") from error
        return first_line, second_line

    def baseline(self, first: str, second: str) -> np.ndarray:
        """Return the transformed finite baseline from first to second."""
        first_line, second_line = self._observer_pair(first, second)
        return np.asarray(second_line.start) - np.asarray(first_line.start)

    def baseline_length(self, first: str, second: str) -> float:
        return float(np.linalg.norm(self.baseline(first, second)))

    def convergence_angle_deg(self, first: str, second: str) -> float:
        """Return the angle between the two finite displayed sight lines."""
        first_line, second_line = self._observer_pair(first, second)
        first_direction = np.asarray(first_line.direction)
        second_direction = np.asarray(second_line.direction)
        cosine = np.clip(first_direction @ second_direction, -1.0, 1.0)
        return float(np.rad2deg(np.arccos(cosine)))
