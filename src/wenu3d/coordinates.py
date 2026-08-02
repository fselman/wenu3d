from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from .annotations import Annotation, AnnotationObject, AnnotationStyle
from .arcs import SphericalArc
from .curve_object import CurveObject
from .curves import CurveStyle, SampledCurve
from .frames import SphericalFrame
from .illustration import IllustrationLayer
from .marker_object import MarkerObject
from .targets import CelestialTarget


EquatorialLongitudeKind = Literal["diagrammatic", "right_ascension"]


@dataclass(frozen=True)
class HorizontalLabels:
    """Configurable terminology for horizontal-coordinate illustrations."""

    north: str = "N"
    east: str = "E"
    south: str = "S"
    west: str = "W"
    zenith: str = "Zenith"
    altitude: str = "Altitude"
    azimuth: str = "Azimuth (North through East)"

    def __post_init__(self) -> None:
        for field_name in (
            "north", "east", "south", "west", "zenith",
            "altitude", "azimuth",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Horizontal label {field_name} must be non-empty."
                )
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True)
class EquatorialLabels:
    """Configurable terminology for equatorial-coordinate illustrations."""

    right_ascension: str = "Right ascension"
    declination: str = "Declination"
    north_celestial_pole: str = "NCP"
    south_celestial_pole: str = "SCP"
    equator: str = "Celestial equator"
    zero: str = "RA zero"

    def __post_init__(self) -> None:
        for field_name in (
            "right_ascension",
            "declination",
            "north_celestial_pole",
            "south_celestial_pole",
            "equator",
            "zero",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Equatorial label {field_name} must be non-empty."
                )
            object.__setattr__(self, field_name, value.strip())


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

    @property
    def vertical_circle(self) -> SphericalArc:
        """Complete great circle through the target and Zenith."""
        foot = np.asarray(self._foot_direction)
        vertical_frame = SphericalFrame(
            name=f"{self.target.name}.vertical_circle",
            pole=np.cross(self.frame.pole, foot),
            zero=self.frame.pole,
            east=foot,
        )
        return SphericalArc.great_circle(
            vertical_frame,
            start_deg=0.0,
            end_deg=360.0,
            radius=self.target.shell_radius,
            samples=max(self.samples, 181),
        )

    @property
    def vertical_circle_points(self) -> np.ndarray:
        """Sample the complete vertical circle through exact key directions."""
        samples = max(self.samples, 181)
        half_samples = max(2, samples // 2 + 1)

        def interval(start: float, end: float) -> np.ndarray:
            fraction = abs(end - start) / 180.0
            count = max(2, int(np.ceil(fraction * (samples - 1))) + 1)
            return np.linspace(start, end, count)

        key_latitudes = sorted({
            -90.0,
            0.0,
            self.altitude_deg,
            90.0,
        })
        latitude_parts = [
            interval(start, end)
            for start, end in zip(key_latitudes[:-1], key_latitudes[1:])
        ]
        first_latitudes = np.concatenate((
            latitude_parts[0],
            *(part[1:] for part in latitude_parts[1:]),
        ))
        first_longitudes = np.full_like(
            first_latitudes,
            self.azimuth_deg,
        )
        second_latitudes = np.linspace(90.0, -90.0, half_samples)[1:]
        second_longitudes = np.full_like(
            second_latitudes,
            (self.azimuth_deg + 180.0) % 360.0,
        )
        return self.target.shell_radius * np.concatenate((
            self.frame.point(first_longitudes, first_latitudes),
            self.frame.point(second_longitudes, second_latitudes),
        ))


@dataclass(frozen=True)
class EquatorialCoordinateGeometry:
    """Centered declination and equatorial-longitude target geometry."""

    target: CelestialTarget
    frame: SphericalFrame
    longitude_kind: EquatorialLongitudeKind = "diagrammatic"
    right_ascension_origin: str | None = None
    samples: int = 101
    _longitude_deg: float = field(init=False, repr=False)
    _declination_deg: float = field(init=False, repr=False)
    _foot_direction: tuple[float, float, float] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.target, CelestialTarget):
            raise TypeError("Equatorial target must be a CelestialTarget.")
        if not isinstance(self.frame, SphericalFrame):
            raise TypeError("Equatorial frame must be a SphericalFrame.")
        if self.longitude_kind not in ("diagrammatic", "right_ascension"):
            raise ValueError(
                "longitude_kind must be 'diagrammatic' or 'right_ascension'."
            )
        origin = self.right_ascension_origin
        if self.longitude_kind == "right_ascension":
            if not isinstance(origin, str) or not origin.strip():
                raise ValueError(
                    "Right ascension requires a scientific origin description."
                )
            origin = origin.strip()
        elif origin is not None:
            raise ValueError(
                "right_ascension_origin requires right_ascension longitude."
            )
        if (
            isinstance(self.samples, (bool, np.bool_))
            or not isinstance(self.samples, (int, np.integer))
            or self.samples < 2
        ):
            raise ValueError(
                "Equatorial samples must be an integer greater than or "
                "equal to 2."
            )

        direction = np.asarray(self.target.direction)
        zero_component = float(direction @ self.frame.zero)
        east_component = float(direction @ self.frame.east)
        equatorial_norm = float(np.hypot(zero_component, east_component))
        if equatorial_norm < 1e-12:
            raise ValueError(
                "Equatorial longitude is undefined at a celestial pole."
            )
        longitude = np.rad2deg(np.arctan2(east_component, zero_component))
        longitude %= 360.0
        declination = np.rad2deg(
            np.arcsin(np.clip(direction @ self.frame.pole, -1.0, 1.0))
        )
        foot = (
            zero_component * self.frame.zero
            + east_component * self.frame.east
        ) / equatorial_norm

        object.__setattr__(self, "samples", int(self.samples))
        object.__setattr__(self, "right_ascension_origin", origin)
        object.__setattr__(self, "_longitude_deg", float(longitude))
        object.__setattr__(self, "_declination_deg", float(declination))
        object.__setattr__(
            self,
            "_foot_direction",
            tuple(float(component) for component in foot),
        )

    @property
    def longitude_deg(self) -> float:
        return self._longitude_deg

    @property
    def declination_deg(self) -> float:
        return self._declination_deg

    @property
    def longitude_label(self) -> str:
        if self.longitude_kind == "right_ascension":
            return f"Right ascension (origin: {self.right_ascension_origin})"
        return "Diagrammatic equatorial longitude"

    @property
    def right_ascension_hours(self) -> float | None:
        if self.longitude_kind != "right_ascension":
            return None
        return self.longitude_deg / 15.0

    @property
    def hour_circle_foot(self) -> np.ndarray:
        return self.target.shell_radius * np.asarray(self._foot_direction)

    @property
    def declination_arc(self) -> SphericalArc | None:
        if abs(self.declination_deg) < 1e-12:
            return None
        foot = np.asarray(self._foot_direction)
        hour_circle_frame = SphericalFrame(
            name=f"{self.target.name}.hour_circle",
            pole=np.cross(foot, self.frame.pole),
            zero=foot,
            east=self.frame.pole,
        )
        return SphericalArc.great_circle(
            hour_circle_frame,
            start_deg=0.0,
            end_deg=self.declination_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )

    @property
    def longitude_arc(self) -> SphericalArc | None:
        if self.longitude_deg < 1e-12 or 360.0 - self.longitude_deg < 1e-12:
            return None
        return SphericalArc.great_circle(
            self.frame,
            start_deg=0.0,
            end_deg=self.longitude_deg,
            radius=self.target.shell_radius,
            samples=self.samples,
        )

    @property
    def hour_circle(self) -> SphericalArc:
        """Complete great circle through the target and celestial poles."""
        foot = np.asarray(self._foot_direction)
        frame = SphericalFrame(
            name=f"{self.target.name}.hour_circle",
            pole=np.cross(self.frame.pole, foot),
            zero=self.frame.pole,
            east=foot,
        )
        return SphericalArc.great_circle(
            frame,
            start_deg=0.0,
            end_deg=360.0,
            radius=self.target.shell_radius,
            samples=max(self.samples, 181),
        )

    @property
    def declination_circle_points(self) -> np.ndarray:
        """Sample the target's complete small circle of declination."""
        longitudes = np.linspace(0.0, 360.0, max(self.samples, 181))
        latitudes = np.full_like(longitudes, self.declination_deg)
        return self.target.shell_radius * self.frame.point(
            longitudes,
            latitudes,
        )


class EquatorialCoordinateIllustration(IllustrationLayer):
    """Renderable target, declination, longitude, and convention labels."""

    def __init__(
        self,
        *,
        name: str,
        target: CelestialTarget,
        frame: SphericalFrame,
        longitude_kind: EquatorialLongitudeKind = "diagrammatic",
        right_ascension_origin: str | None = None,
        samples: int = 101,
        declination_style: CurveStyle | None = None,
        longitude_style: CurveStyle | None = None,
        annotation_style: AnnotationStyle | None = None,
        labels: EquatorialLabels | None = None,
        angle_decimals: int = 1,
        show_labels: bool = True,
        show_hour_circle: bool = False,
        show_declination_circle: bool = False,
        hour_circle_style: CurveStyle | None = None,
        declination_circle_style: CurveStyle | None = None,
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
        if declination_style is not None and not isinstance(
            declination_style,
            CurveStyle,
        ):
            raise TypeError("declination_style must be a CurveStyle.")
        if longitude_style is not None and not isinstance(
            longitude_style,
            CurveStyle,
        ):
            raise TypeError("longitude_style must be a CurveStyle.")
        if annotation_style is not None and not isinstance(
            annotation_style,
            AnnotationStyle,
        ):
            raise TypeError("annotation_style must be an AnnotationStyle.")
        if labels is not None and not isinstance(labels, EquatorialLabels):
            raise TypeError("labels must be EquatorialLabels.")
        for field_name, value in (
            ("show_hour_circle", show_hour_circle),
            ("show_declination_circle", show_declination_circle),
        ):
            if not isinstance(value, (bool, np.bool_)):
                raise TypeError(f"{field_name} must be a boolean.")
        for field_name, value in (
            ("hour_circle_style", hour_circle_style),
            ("declination_circle_style", declination_circle_style),
        ):
            if value is not None and not isinstance(value, CurveStyle):
                raise TypeError(f"{field_name} must be a CurveStyle.")

        super().__init__(name=name, visible=visible, opacity=opacity)
        self.target = target
        self.geometry = EquatorialCoordinateGeometry(
            target=target,
            frame=frame,
            longitude_kind=longitude_kind,
            right_ascension_origin=right_ascension_origin,
            samples=samples,
        )
        self.declination_style = declination_style or CurveStyle(
            color="#8b5fbf",
            width=4.0,
            arrowheads="end",
        )
        self.longitude_style = longitude_style or CurveStyle(
            color="#bd6f3f",
            width=4.0,
            arrowheads="end",
        )
        self.annotation_style = annotation_style or AnnotationStyle()
        self._custom_labels = labels is not None
        self.labels = labels or EquatorialLabels()
        self.angle_decimals = int(angle_decimals)
        self.show_labels = bool(show_labels)
        self.show_hour_circle = bool(show_hour_circle)
        self.show_declination_circle = bool(show_declination_circle)
        self.hour_circle_style = hour_circle_style or CurveStyle(
            color="#687784", width=1.0, opacity=0.24
        )
        self.declination_circle_style = declination_circle_style or CurveStyle(
            color="#687784", width=1.0, opacity=0.20
        )
        self._populate_target_objects()

    def _populate_target_objects(self) -> None:
        self.marker_object: MarkerObject = self.add_marker(
            f"{self.name}.target",
            self.target.as_marker(),
        )
        self.hour_circle_object: CurveObject | None = None
        self.declination_circle_object: CurveObject | None = None
        self.declination_curve_object: CurveObject | None = None
        self.longitude_curve_object: CurveObject | None = None
        self.declination_annotation: AnnotationObject | None = None
        self.longitude_annotation: AnnotationObject | None = None

        if self.show_hour_circle:
            self.hour_circle_object = self.add_curve(
                f"{self.name}.hour_circle",
                self.geometry.hour_circle.to_curve(style=self.hour_circle_style),
            )
        if self.show_declination_circle:
            self.declination_circle_object = self.add_curve(
                f"{self.name}.declination_circle",
                SampledCurve(
                    points=self.geometry.declination_circle_points,
                    style=self.declination_circle_style,
                ),
            )

        declination_arc = self.geometry.declination_arc
        if declination_arc is not None:
            self.declination_curve_object = self.add_curve(
                f"{self.name}.declination",
                declination_arc.to_curve(style=self.declination_style),
            )
            if self.show_labels:
                self.declination_annotation = self._add_angle_annotation(
                    name=f"{self.name}.declination.label",
                    text=(
                        f"{self.labels.declination} = "
                        f"{self.geometry.declination_deg:.{self.angle_decimals}f}°"
                    ),
                    curve_object=self.declination_curve_object,
                )

        longitude_arc = self.geometry.longitude_arc
        if longitude_arc is not None:
            self.longitude_curve_object = self.add_curve(
                f"{self.name}.longitude",
                longitude_arc.to_curve(style=self.longitude_style),
            )
            if self.show_labels:
                self.longitude_annotation = self._add_angle_annotation(
                    name=f"{self.name}.longitude.label",
                    text=self._longitude_annotation_text(),
                    curve_object=self.longitude_curve_object,
                )

    def _longitude_annotation_text(self) -> str:
        if self.geometry.longitude_kind == "right_ascension":
            label = (
                self.labels.right_ascension
                if self._custom_labels
                else self.geometry.longitude_label
            )
            return (
                f"{label} = "
                f"{self.geometry.right_ascension_hours:.{self.angle_decimals}f} h"
            )
        return (
            f"{self.geometry.longitude_label} = "
            f"{self.geometry.longitude_deg:.{self.angle_decimals}f}°"
        )

    def set_target_and_frame(
        self,
        *,
        target: CelestialTarget | None = None,
        frame: SphericalFrame | None = None,
        render: bool = True,
    ) -> None:
        """Refresh target-derived geometry after target or origin changes."""
        if target is not None and not isinstance(target, CelestialTarget):
            raise TypeError("target must be a CelestialTarget.")
        if frame is not None and not isinstance(frame, SphericalFrame):
            raise TypeError("frame must be a SphericalFrame.")
        plotter = self.attached_plotter
        self.detach(render=False)
        self.objects.clear()
        self.target = self.target if target is None else target
        current_frame = self.geometry.frame if frame is None else frame
        self.geometry = EquatorialCoordinateGeometry(
            target=self.target,
            frame=current_frame,
            longitude_kind=self.geometry.longitude_kind,
            right_ascension_origin=self.geometry.right_ascension_origin,
            samples=self.geometry.samples,
        )
        self._populate_target_objects()
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()

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


class EquatorialReferenceIllustration(IllustrationLayer):
    """Celestial equator, RA-zero tick, and celestial-pole labels."""

    def __init__(
        self,
        *,
        name: str,
        frame: SphericalFrame,
        radius: float,
        labels: EquatorialLabels | None = None,
        equator_style: CurveStyle | None = None,
        zero_tick_style: CurveStyle | None = None,
        zero_tick_half_angle_deg: float = 3.0,
        annotation_style: AnnotationStyle | None = None,
        samples: int = 361,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(frame, SphericalFrame):
            raise TypeError("frame must be a SphericalFrame.")
        radius = float(radius)
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError("radius must be finite and greater than zero.")
        if (
            isinstance(samples, (bool, np.bool_))
            or not isinstance(samples, (int, np.integer))
            or samples < 4
        ):
            raise ValueError("samples must be an integer of at least 4.")
        labels = labels or EquatorialLabels()
        if not isinstance(labels, EquatorialLabels):
            raise TypeError("labels must be EquatorialLabels.")
        for field_name, style, style_type in (
            ("equator_style", equator_style, CurveStyle),
            ("zero_tick_style", zero_tick_style, CurveStyle),
            ("annotation_style", annotation_style, AnnotationStyle),
        ):
            if style is not None and not isinstance(style, style_type):
                raise TypeError(f"{field_name} must be a {style_type.__name__}.")

        super().__init__(name=name, visible=visible, opacity=opacity)
        self.frame = frame
        self.radius = radius
        self.labels = labels
        self.samples = int(samples)
        self.equator_style = equator_style or CurveStyle(
            color="#665b78", width=2.0, opacity=0.62
        )
        self.zero_tick_style = zero_tick_style or CurveStyle(
            color="#463953", width=5.0, opacity=0.92
        )
        zero_tick_half_angle_deg = float(zero_tick_half_angle_deg)
        if (
            not np.isfinite(zero_tick_half_angle_deg)
            or not 0.0 < zero_tick_half_angle_deg < 90.0
        ):
            raise ValueError(
                "zero_tick_half_angle_deg must be finite and in (0, 90)."
            )
        self.zero_tick_half_angle_deg = zero_tick_half_angle_deg
        self.annotation_style = annotation_style or AnnotationStyle()
        self._populate_reference_objects()

    def _populate_reference_objects(self) -> None:
        equator = SphericalArc.great_circle(
            self.frame,
            start_deg=0.0,
            end_deg=360.0,
            radius=self.radius,
            samples=self.samples,
        )
        zero_hour_frame = SphericalFrame(
            name=f"{self.name}.zero_hour_circle",
            pole=self.frame.east,
            zero=self.frame.pole,
            east=self.frame.zero,
        )
        zero_tick = SphericalArc.great_circle(
            zero_hour_frame,
            start_deg=90.0 - self.zero_tick_half_angle_deg,
            end_deg=90.0 + self.zero_tick_half_angle_deg,
            radius=self.radius,
            samples=max(5, int(np.ceil(self.zero_tick_half_angle_deg)) * 2 + 1),
        )
        self.equator_object = self.add_curve(
            f"{self.name}.equator",
            equator.to_curve(style=self.equator_style),
        )
        self.zero_tick_object = self.add_curve(
            f"{self.name}.zero_tick",
            zero_tick.to_curve(style=self.zero_tick_style),
        )
        annotation_radius = 1.025 * self.radius
        self.north_pole_annotation = self.add_annotation(
            f"{self.name}.north_pole",
            Annotation(
                text=self.labels.north_celestial_pole,
                anchor=annotation_radius * self.frame.pole,
                style=self.annotation_style,
            ),
        )
        self.south_pole_annotation = self.add_annotation(
            f"{self.name}.south_pole",
            Annotation(
                text=self.labels.south_celestial_pole,
                anchor=-annotation_radius * self.frame.pole,
                style=self.annotation_style,
            ),
        )
        self.equator_annotation = self.add_annotation(
            f"{self.name}.equator.label",
            Annotation(
                text=self.labels.equator,
                anchor=annotation_radius * self.frame.point(135.0, 0.0),
                style=self.annotation_style,
                associated_with=self.equator_object.name,
            ),
        )

    def set_frame(
        self,
        frame: SphericalFrame,
        *,
        render: bool = True,
    ) -> None:
        """Replace the equatorial longitude origin and rebuild references."""
        if not isinstance(frame, SphericalFrame):
            raise TypeError("frame must be a SphericalFrame.")
        plotter = self.attached_plotter
        self.detach(render=False)
        self.objects.clear()
        self.frame = frame
        self._populate_reference_objects()
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()


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
        vertical_circle_style: CurveStyle | None = None,
        annotation_style: AnnotationStyle | None = None,
        labels: HorizontalLabels | None = None,
        angle_decimals: int = 1,
        show_labels: bool = True,
        show_vertical_circle: bool = False,
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
        if vertical_circle_style is not None and not isinstance(
            vertical_circle_style,
            CurveStyle,
        ):
            raise TypeError("vertical_circle_style must be a CurveStyle.")
        if annotation_style is not None and not isinstance(
            annotation_style,
            AnnotationStyle,
        ):
            raise TypeError("annotation_style must be an AnnotationStyle.")
        if labels is not None and not isinstance(labels, HorizontalLabels):
            raise TypeError("labels must be HorizontalLabels.")
        if not isinstance(show_vertical_circle, (bool, np.bool_)):
            raise TypeError("show_vertical_circle must be a boolean.")

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
        self.vertical_circle_style = vertical_circle_style or CurveStyle(
            color="#687784",
            width=1.0,
            opacity=0.28,
        )
        self.annotation_style = annotation_style or AnnotationStyle()
        self.labels = labels or HorizontalLabels()
        self.angle_decimals = int(angle_decimals)
        self.show_labels = bool(show_labels)
        self.show_vertical_circle = bool(show_vertical_circle)

        self._populate_target_objects()

    def _populate_target_objects(self) -> None:
        """Create renderer objects derived from the current target."""

        self.marker_object: MarkerObject = self.add_marker(
            f"{self.name}.target",
            self.target.as_marker(),
        )
        self.vertical_circle_object: CurveObject | None = None
        self.altitude_curve_object: CurveObject | None = None
        self.azimuth_curve_object: CurveObject | None = None
        self.altitude_annotation: AnnotationObject | None = None
        self.azimuth_annotation: AnnotationObject | None = None

        if self.show_vertical_circle:
            self.vertical_circle_object = self.add_curve(
                f"{self.name}.vertical_circle",
                SampledCurve(
                    points=self.geometry.vertical_circle_points,
                    style=self.vertical_circle_style,
                ),
            )

        altitude_arc = self.geometry.altitude_arc
        if altitude_arc is not None:
            self.altitude_curve_object = self.add_curve(
                f"{self.name}.altitude",
                altitude_arc.to_curve(style=self.altitude_style),
            )
            if self.show_labels:
                self.altitude_annotation = self._add_angle_annotation(
                    name=f"{self.name}.altitude.label",
                    text=(
                        f"{self.labels.altitude} = "
                        f"{self.geometry.altitude_deg:.{self.angle_decimals}f}°"
                    ),
                    curve_object=self.altitude_curve_object,
                )

        azimuth_arc = self.geometry.azimuth_arc
        if azimuth_arc is not None:
            self.azimuth_curve_object = self.add_curve(
                f"{self.name}.azimuth",
                azimuth_arc.to_curve(style=self.azimuth_style),
            )
            if self.show_labels:
                self.azimuth_annotation = self._add_angle_annotation(
                    name=f"{self.name}.azimuth.label",
                    text=(
                        f"{self.labels.azimuth} = "
                        f"{self.geometry.azimuth_deg:.{self.angle_decimals}f}°"
                    ),
                    curve_object=self.azimuth_curve_object,
                )

    def set_target(
        self,
        target: CelestialTarget,
        *,
        render: bool = True,
    ) -> None:
        """Replace the semantic target and refresh all derived components."""
        if not isinstance(target, CelestialTarget):
            raise TypeError("target must be a CelestialTarget.")
        plotter = self.attached_plotter
        self.detach(render=False)
        self.objects.clear()
        self.target = target
        self.geometry = HorizontalCoordinateGeometry(
            target=target,
            frame=self.geometry.frame,
            samples=self.geometry.samples,
        )
        self._populate_target_objects()
        if plotter is not None:
            self.build(plotter)
            if render:
                plotter.render()

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


class HorizontalReferenceIllustration(IllustrationLayer):
    """Geometric horizon, meridian, and named horizontal directions."""

    def __init__(
        self,
        *,
        name: str,
        frame: SphericalFrame,
        radius: float,
        labels: HorizontalLabels | None = None,
        horizon_style: CurveStyle | None = None,
        meridian_style: CurveStyle | None = None,
        annotation_style: AnnotationStyle | None = None,
        samples: int = 361,
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        if not isinstance(frame, SphericalFrame):
            raise TypeError("frame must be a SphericalFrame.")
        radius = float(radius)
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError("radius must be finite and greater than zero.")
        labels = labels or HorizontalLabels()
        if not isinstance(labels, HorizontalLabels):
            raise TypeError("labels must be HorizontalLabels.")
        for field_name, style, style_type in (
            ("horizon_style", horizon_style, CurveStyle),
            ("meridian_style", meridian_style, CurveStyle),
            ("annotation_style", annotation_style, AnnotationStyle),
        ):
            if style is not None and not isinstance(style, style_type):
                raise TypeError(f"{field_name} must be a {style_type.__name__}.")

        super().__init__(name=name, visible=visible, opacity=opacity)
        self.frame = frame
        self.radius = radius
        self.labels = labels
        self.horizon_style = horizon_style or CurveStyle(
            color="#40586c",
            width=2.4,
            opacity=0.72,
        )
        self.meridian_style = meridian_style or CurveStyle(
            color="#596773",
            width=1.5,
            opacity=0.48,
        )
        self.annotation_style = annotation_style or AnnotationStyle(
            color="#263746",
            font_size=16,
            bold=True,
        )

        self.horizon_object = self.add_curve(
            f"{name}.horizon",
            SphericalArc.great_circle(
                frame,
                0.0,
                360.0,
                radius=radius,
                samples=samples,
            ).to_curve(style=self.horizon_style),
        )
        meridian_frame = SphericalFrame(
            name=f"{name}.meridian",
            pole=frame.east,
            zero=frame.zero,
            east=frame.pole,
        )
        self.meridian_object = self.add_curve(
            f"{name}.meridian",
            SphericalArc.great_circle(
                meridian_frame,
                0.0,
                360.0,
                radius=radius,
                samples=samples,
            ).to_curve(style=self.meridian_style),
        )
        self.annotations: dict[str, AnnotationObject] = {}
        for key, text, direction in (
            ("north", labels.north, frame.zero),
            ("east", labels.east, frame.east),
            ("south", labels.south, -frame.zero),
            ("west", labels.west, -frame.east),
            ("zenith", labels.zenith, frame.pole),
        ):
            anchor = radius * direction
            self.annotations[key] = self.add_annotation(
                f"{name}.{key}.label",
                Annotation(
                    text=text,
                    anchor=anchor,
                    offset=0.045 * radius * direction,
                    style=self.annotation_style,
                    associated_with=(
                        self.meridian_object.name
                        if key == "zenith"
                        else self.horizon_object.name
                    ),
                ),
            )
