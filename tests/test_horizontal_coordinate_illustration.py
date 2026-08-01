import numpy as np
import pyvista as pv
import pytest

from wenu3d.annotations import AnnotationStyle
from wenu3d.coordinates import HorizontalCoordinateIllustration
from wenu3d.coordinates import HorizontalLabels, HorizontalReferenceIllustration
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


def test_attached_target_replacement_refreshes_geometry_and_components() -> None:
    illustration = make_illustration()
    plotter = pv.Plotter(off_screen=True)
    frame = illustration.geometry.frame
    updated = illustration.target.with_direction(frame.point(45.0, 30.0))

    try:
        illustration.build(plotter)
        illustration.set_target(updated, render=False)

        assert illustration.target is updated
        assert illustration.geometry.azimuth_deg == pytest.approx(45.0)
        assert illustration.geometry.altitude_deg == pytest.approx(30.0)
        assert illustration.marker_object.marker.position == pytest.approx(
            updated.display_position
        )
        assert illustration.azimuth_annotation.annotation.text.endswith("45.0°")
        assert illustration.altitude_annotation.annotation.text.endswith("30.0°")
        assert illustration.attached_plotter is plotter
    finally:
        illustration.detach(render=False)
        plotter.close()


def test_target_replacement_validates_target_type() -> None:
    with pytest.raises(TypeError, match="target"):
        make_illustration().set_target(object())
        assert np.dot(annotation.anchor, annotation.offset) > 0.0


def test_spanish_labels_and_weak_vertical_circle_are_configurable() -> None:
    labels = HorizontalLabels(
        west="O",
        zenith="Cenit",
        altitude="Altura",
        azimuth="Acimut",
    )
    reference_style = CurveStyle(color="gray", width=1.0, opacity=0.2)
    illustration = make_illustration(
        labels=labels,
        angle_decimals=0,
        show_vertical_circle=True,
        vertical_circle_style=reference_style,
    )

    assert illustration.altitude_annotation.annotation.text == "Altura = 37°"
    assert illustration.azimuth_annotation.annotation.text == "Acimut = 123°"
    assert illustration.vertical_circle_object.curve.style is reference_style
    assert illustration.vertical_circle_object.curve.as_array().shape[0] >= 181


def test_horizontal_references_share_frame_and_label_cardinal_points() -> None:
    frame = horizontal_frame()
    labels = HorizontalLabels(west="O", zenith="Cenit")
    references = HorizontalReferenceIllustration(
        name="horizontal.references",
        frame=frame,
        radius=2.0,
        labels=labels,
        samples=181,
    )

    np.testing.assert_allclose(
        references.horizon_object.curve.as_array()[0],
        2.0 * frame.zero,
    )
    assert references.annotations["north"].annotation.text == "N"
    assert references.annotations["east"].annotation.text == "E"
    assert references.annotations["south"].annotation.text == "S"
    assert references.annotations["west"].annotation.text == "O"
    assert references.annotations["zenith"].annotation.text == "Cenit"
    np.testing.assert_allclose(
        references.annotations["zenith"].annotation.anchor,
        2.0 * frame.pole,
    )


def test_illustration_annotation_size_is_a_reusable_capability() -> None:
    illustration = make_illustration()

    illustration.set_font_size_scale(1.75, render=False)

    assert illustration.font_size_scale == pytest.approx(1.75)
    assert illustration.altitude_annotation.font_size_scale == pytest.approx(1.75)
    assert illustration.azimuth_annotation.font_size_scale == pytest.approx(1.75)
