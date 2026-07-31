import numpy as np
import pyvista as pv
import pytest

from wenu3d.annotations import AnnotationStyle
from wenu3d.coordinates import EquatorialCoordinateIllustration
from wenu3d.curves import CurveStyle
from wenu3d.frames import SphericalFrame
from wenu3d.targets import CelestialTarget


def equatorial_frame() -> SphericalFrame:
    return SphericalFrame(
        name="diagrammatic_equatorial",
        pole=(0.0, 0.0, 1.0),
        zero=(1.0, 0.0, 0.0),
        east=(0.0, 1.0, 0.0),
    )


def make_illustration(**kwargs) -> EquatorialCoordinateIllustration:
    frame = equatorial_frame()
    target = CelestialTarget(
        name="star",
        direction=frame.point(75.0, -20.0),
        shell_radius=2.0,
    )
    arguments = {
        "name": "equatorial.star",
        "target": target,
        "frame": frame,
        "samples": 11,
    }
    arguments.update(kwargs)
    return EquatorialCoordinateIllustration(**arguments)


def test_illustration_exposes_ordered_components_and_records() -> None:
    illustration = make_illustration()

    assert [obj.name for obj in illustration.objects] == [
        "equatorial.star.target",
        "equatorial.star.declination",
        "equatorial.star.declination.label",
        "equatorial.star.longitude",
        "equatorial.star.longitude.label",
    ]
    assert illustration.marker_object.marker.position == pytest.approx(
        illustration.target.display_position
    )
    assert illustration.declination_curve_object.curve.style is (
        illustration.declination_style
    )
    assert illustration.longitude_curve_object.curve.style is (
        illustration.longitude_style
    )


def test_diagrammatic_labels_state_values_and_convention() -> None:
    illustration = make_illustration(angle_decimals=2)

    declination = illustration.declination_annotation.annotation
    longitude = illustration.longitude_annotation.annotation
    assert declination.text == "Declination = -20.00°"
    assert longitude.text == "Diagrammatic equatorial longitude = 75.00°"
    assert declination.associated_with == (
        illustration.declination_curve_object.name
    )
    assert longitude.associated_with == illustration.longitude_curve_object.name


def test_right_ascension_label_uses_hours_and_reports_origin() -> None:
    illustration = make_illustration(
        longitude_kind="right_ascension",
        right_ascension_origin="ICRS vernal equinox direction",
        angle_decimals=2,
    )

    assert illustration.longitude_annotation.annotation.text == (
        "Right ascension (origin: ICRS vernal equinox direction) = 5.00 h"
    )


def test_styles_and_arrowheads_remain_caller_configurable() -> None:
    declination_style = CurveStyle(
        color="purple",
        width=7.0,
        arrowheads="both",
    )
    longitude_style = CurveStyle(
        color="orange",
        width=5.0,
        arrowheads="none",
    )
    annotation_style = AnnotationStyle(color="navy", font_size=18, bold=True)

    illustration = make_illustration(
        declination_style=declination_style,
        longitude_style=longitude_style,
        annotation_style=annotation_style,
    )

    assert illustration.declination_style is declination_style
    assert illustration.longitude_style is longitude_style
    assert illustration.annotation_style is annotation_style
    assert illustration.declination_annotation.annotation.style is (
        annotation_style
    )
    assert illustration.longitude_annotation.annotation.style is annotation_style


def test_labels_can_be_omitted_without_removing_coordinate_curves() -> None:
    illustration = make_illustration(show_labels=False)

    assert illustration.declination_curve_object is not None
    assert illustration.longitude_curve_object is not None
    assert illustration.declination_annotation is None
    assert illustration.longitude_annotation is None
    assert len(illustration.objects) == 3


def test_zero_span_components_are_omitted_independently() -> None:
    frame = equatorial_frame()
    target = CelestialTarget(
        name="origin",
        direction=frame.zero,
        shell_radius=2.0,
    )

    illustration = EquatorialCoordinateIllustration(
        name="origin",
        target=target,
        frame=frame,
    )

    assert illustration.marker_object is not None
    assert illustration.declination_curve_object is None
    assert illustration.longitude_curve_object is None
    assert illustration.declination_annotation is None
    assert illustration.longitude_annotation is None
    assert illustration.objects == [illustration.marker_object]


def test_illustration_builds_marker_curves_arrowheads_and_labels() -> None:
    illustration = make_illustration()
    plotter = pv.Plotter(off_screen=True)

    try:
        illustration.build(plotter)

        assert len(illustration.objects) == 5
        assert len(illustration.actors) == 7
        assert illustration.marker_object.mesh is not None
        assert len(illustration.declination_curve_object.arrow_meshes) == 1
        assert len(illustration.longitude_curve_object.arrow_meshes) == 1
    finally:
        illustration.detach(render=False)
        plotter.close()


def test_illustration_validates_styles_labels_and_precision() -> None:
    for field_name in (
        "declination_style",
        "longitude_style",
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
        illustration.declination_annotation,
        illustration.longitude_annotation,
    ):
        annotation = annotation_object.annotation
        assert np.all(np.isfinite(annotation.offset))
        assert np.dot(annotation.anchor, annotation.offset) > 0.0
