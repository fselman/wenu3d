from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .annotations import Annotation, AnnotationObject, AnnotationStyle
from .arcs import SphericalArc
from .curve_object import CurveObject
from .curves import CurveStyle
from .frames import SphericalFrame
from .illustration import IllustrationLayer
from .marker_object import MarkerObject
from .targets import CelestialTarget


@dataclass(frozen=True)
class HorizontalCoordinateGeometry:
    """Centered altitude and azimuth geometry for one celestial target."""

    target: CelestialTarget
    frame: SphericalFrame
    samples: int = 101
    _azimuth_deg: float = field(init=False, repr=False)
    _altitude_deg: float = field(init=False, repr=False)
    _foot_direction: tuple[float, float, float] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.target, CelestialTarget):
            raise TypeError("Horizontal target must be a CelestialTarget.")
        if not isinstance(self.frame, SphericalFrame):
            raise TypeError("Horizontal frame must be a SphericalFrame.")
        if (
            isinstance(self.samples, (bool, np.bool_))
            or not isinstance(self.samples, (int, np.integer))
            or self.samples < 2
        ):
            raise ValueError(
                "Horizontal samples must be an integer greater than or "
                "equal to 2."
            )

        direction = np.asarray(self.target.direction)
        north_component = float(direction @ self.frame.zero)
        east_component = float(direction @ self.frame.east)
        horizontal_norm = float(np.hypot(north_component, east_component))
        if horizontal_norm < 1e-12:
            raise ValueError(
                "Horizontal azimuth is undefined at Zenith or Nadir."
            )

        azimuth = np.rad2deg(np.arctan2(east_component, north_component))
        azimuth %= 360.0
        altitude = np.rad2deg(
            np.arcsin(np.clip(direction @ self.frame.pole, -1.0, 1.0))
        )
        foot = (
            north_component * self.frame.zero
            + east_component * self.frame.east
        ) / horizontal_norm

        object.__setattr__(self, "samples", int(self.samples))
        object.__setattr__(self, "_azimuth_deg", float(azimuth))
        object.__setattr__(self, "_altitude_deg", float(altitude))
        object.__setattr__(
            self,
            "_foot_direction",
            tuple(float(component) for component in foot),
        )

    @property
    def azimuth_deg(self) -> float:
        """Azimuth measured from North through East in [0, 360)."""
        return self._azimuth_deg

    @property
    def altitude_deg(self) -> float:
        return self._altitude_deg

    @property
    def vertical_circle_foot(self) -> np.ndarray:
        return self.target.shell_radius * np.asarray(self._foot_direction)

    @property
    def altitude_arc(self) -> SphericalArc | None:
        """Arc from the ideal horizon to the target along its vertical."""
        if abs(self.altitude_deg) < 1e-12:
            return None
        foot = np.asarray(self._foot_direction)
        vertical_frame = SphericalFrame(
            name=f"{self.target.name}.vertical_circle",
            pole=np.cross(foot, self.frame.pole),
            zero=foot,
            east=self.frame.pole,
        )
        return SphericalArc.great_circle(
            vertical_frame,
            start_deg=0.0,
            end_deg=self.altitude_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )

    @property
    def azimuth_arc(self) -> SphericalArc | None:
        """Arc on the ideal horizon from North to the vertical foot."""
        if self.azimuth_deg < 1e-12 or 360.0 - self.azimuth_deg < 1e-12:
            return None
        return SphericalArc.great_circle(
            self.frame,
            start_deg=0.0,
            end_deg=self.azimuth_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )


class HorizontalCoordinateIllustration(IllustrationLayer):
    """Renderable target, altitude, azimuth, and convention labels."""

    def __init__(
        self,
        *,
        name: str,
        target: CelestialTarget,
        frame: SphericalFrame,
        samples: int = 101,
        altitude_style: CurveStyle | None = None,
        azimuth_style: CurveStyle | None = None,
        annotation_style: AnnotationStyle | None = None,
        angle_decimals: int = 1,
        show_labels: bool = True,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if (
            isinstance(angle_decimals, (bool, np.bool_))
            or not isinstance(angle_decimals, (int, np.integer))
            or angle_decimals < 0
        ):
            raise ValueError("angle_decimals must be a non-negative integer.")
        if not isinstance(show_labels, (bool, np.bool_)):
            raise TypeError("show_labels must be a boolean.")
        if altitude_style is not None and not isinstance(
            altitude_style,
            CurveStyle,
        ):
            raise TypeError("altitude_style must be a CurveStyle.")
        if azimuth_style is not None and not isinstance(
            azimuth_style,
            CurveStyle,
        ):
            raise TypeError("azimuth_style must be a CurveStyle.")
        if annotation_style is not None and not isinstance(
            annotation_style,
            AnnotationStyle,
        ):
            raise TypeError("annotation_style must be an AnnotationStyle.")

        super().__init__(name=name, visible=visible, opacity=opacity)
        self.target = target
        self.geometry = HorizontalCoordinateGeometry(
            target=target,
            frame=frame,
            samples=samples,
        )
        self.altitude_style = altitude_style or CurveStyle(
            color="#3f78b5",
            width=4.0,
            arrowheads="end",
        )
        self.azimuth_style = azimuth_style or CurveStyle(
            color="#4f8a5b",
            width=4.0,
            arrowheads="end",
        )
        self.annotation_style = annotation_style or AnnotationStyle()
        self.angle_decimals = int(angle_decimals)
        self.show_labels = bool(show_labels)

        self.marker_object: MarkerObject = self.add_marker(
            f"{name}.target",
            target.as_marker(),
        )
        self.altitude_curve_object: CurveObject | None = None
        self.azimuth_curve_object: CurveObject | None = None
        self.altitude_annotation: AnnotationObject | None = None
        self.azimuth_annotation: AnnotationObject | None = None

        altitude_arc = self.geometry.altitude_arc
        if altitude_arc is not None:
            self.altitude_curve_object = self.add_curve(
                f"{name}.altitude",
                altitude_arc.to_curve(style=self.altitude_style),
            )
            if self.show_labels:
                self.altitude_annotation = self._add_angle_annotation(
                    name=f"{name}.altitude.label",
                    text=(
                        "Altitude = "
                        f"{self.geometry.altitude_deg:.{self.angle_decimals}f}°"
                    ),
                    curve_object=self.altitude_curve_object,
                )

        azimuth_arc = self.geometry.azimuth_arc
        if azimuth_arc is not None:
            self.azimuth_curve_object = self.add_curve(
                f"{name}.azimuth",
                azimuth_arc.to_curve(style=self.azimuth_style),
            )
            if self.show_labels:
                self.azimuth_annotation = self._add_angle_annotation(
                    name=f"{name}.azimuth.label",
                    text=(
                        "Azimuth (North through East) = "
                        f"{self.geometry.azimuth_deg:.{self.angle_decimals}f}°"
                    ),
                    curve_object=self.azimuth_curve_object,
                )

    def _add_angle_annotation(
        self,
        *,
        name: str,
        text: str,
        curve_object: CurveObject,
    ) -> AnnotationObject:
        points = curve_object.curve.as_array()
        anchor = points[len(points) // 2]
        offset = 0.035 * self.target.shell_radius * anchor / np.linalg.norm(anchor)
        return self.add_annotation(
            name,
            Annotation(
                text=text,
                anchor=anchor,
                offset=offset,
                style=self.annotation_style,
                associated_with=curve_object.name,
            ),
        )
