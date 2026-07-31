import numpy as np
import pyvista as pv
import pytest

from wenu3d.annotations import AnnotationStyle
from wenu3d.coordinates import HorizontalCoordinateIllustration
from wenu3d.curves import CurveStyle
from wenu3d.frames import horizontal_frame
from wenu3d.targets import CelestialTarget


def make_illustration(**kwargs) -> HorizontalCoordinateIllustration:
    frame = horizontal_frame()
    target = CelestialTarget(
        name="star",
        direction=frame.point(123.0, 37.0),
        shell_radius=2.0,
    )
    arguments = {
        "name": "horizontal.star",
        "target": target,
        "frame": frame,
        "samples": 11,
    }
    arguments.update(kwargs)
    return HorizontalCoordinateIllustration(**arguments)


def test_illustration_exposes_ordered_components_and_records() -> None:
    illustration = make_illustration()

    assert [obj.name for obj in illustration.objects] == [
        "horizontal.star.target",
        "horizontal.star.altitude",
        "horizontal.star.altitude.label",
        "horizontal.star.azimuth",
        "horizontal.star.azimuth.label",
    ]
    assert illustration.marker_object.marker.position == pytest.approx(
        illustration.target.display_position
    )
    assert illustration.altitude_curve_object.curve.style is (
        illustration.altitude_style
    )
    assert illustration.azimuth_curve_object.curve.style is (
        illustration.azimuth_style
    )


def test_coordinate_labels_state_values_and_azimuth_convention() -> None:
    illustration = make_illustration(angle_decimals=2)

    altitude = illustration.altitude_annotation.annotation
    azimuth = illustration.azimuth_annotation.annotation
    assert altitude.text == "Altitude = 37.00°"
    assert azimuth.text == "Azimuth (North through East) = 123.00°"
    assert altitude.associated_with == illustration.altitude_curve_object.name
    assert azimuth.associated_with == illustration.azimuth_curve_object.name


def test_styles_and_arrowheads_remain_caller_configurable() -> None:
    altitude_style = CurveStyle(
        color="purple",
        width=7.0,
        arrowheads="both",
    )
    azimuth_style = CurveStyle(
        color="orange",
        width=5.0,
        arrowheads="none",
    )
    annotation_style = AnnotationStyle(color="navy", font_size=18, bold=True)

    illustration = make_illustration(
        altitude_style=altitude_style,
        azimuth_style=azimuth_style,
        annotation_style=annotation_style,
    )

    assert illustration.altitude_style is altitude_style
    assert illustration.azimuth_style is azimuth_style
    assert illustration.annotation_style is annotation_style
    assert illustration.altitude_annotation.annotation.style is annotation_style
    assert illustration.azimuth_annotation.annotation.style is annotation_style


def test_labels_can_be_omitted_without_removing_coordinate_curves() -> None:
    illustration = make_illustration(show_labels=False)

    assert illustration.altitude_curve_object is not None
    assert illustration.azimuth_curve_object is not None
    assert illustration.altitude_annotation is None
    assert illustration.azimuth_annotation is None
    assert len(illustration.objects) == 3


def test_zero_span_components_are_omitted_independently() -> None:
    frame = horizontal_frame()
    target = CelestialTarget(
        name="north_horizon",
        direction=frame.zero,
        shell_radius=2.0,
    )

    illustration = HorizontalCoordinateIllustration(
        name="north",
        target=target,
        frame=frame,
    )

    assert illustration.marker_object is not None
    assert illustration.altitude_curve_object is None
    assert illustration.azimuth_curve_object is None
    assert illustration.altitude_annotation is None
    assert illustration.azimuth_annotation is None
    assert illustration.objects == [illustration.marker_object]


def test_illustration_builds_marker_curves_arrowheads_and_labels() -> None:
    illustration = make_illustration()
    plotter = pv.Plotter(off_screen=True)

    try:
        illustration.build(plotter)

        assert len(illustration.objects) == 5
        assert len(illustration.actors) == 7
        assert illustration.marker_object.mesh is not None
        assert len(illustration.altitude_curve_object.arrow_meshes) == 1
        assert len(illustration.azimuth_curve_object.arrow_meshes) == 1
    finally:
        illustration.detach(render=False)
        plotter.close()


def test_illustration_validates_styles_labels_and_precision() -> None:
    for field_name in (
        "altitude_style",
        "azimuth_style",
        "annotation_style",
    ):
        with pytest.raises(TypeError, match=field_name):
            make_illustration(**{field_name: object()})
    for angle_decimals in (-1, 1.5, True):
        with pytest.raises(ValueError, match="angle_decimals"):
            make_illustration(angle_decimals=angle_decimals)
    with pytest.raises(TypeError, match="show_labels"):
        make_illustration(show_labels=1)


def test_annotation_offsets_are_radial_and_finite() -> None:
    illustration = make_illustration()

    for annotation_object in (
        illustration.altitude_annotation,
        illustration.azimuth_annotation,
    ):
        annotation = annotation_object.annotation
        assert np.all(np.isfinite(annotation.offset))
        assert np.dot(annotation.anchor, annotation.offset) > 0.0
