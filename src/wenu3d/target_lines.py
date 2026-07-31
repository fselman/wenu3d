from __future__ import annotations

from collections.abc import Mapping

import numpy as np

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
