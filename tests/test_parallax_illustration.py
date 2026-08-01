import numpy as np
import pyvista as pv
import pytest

from wenu3d.annotations import AnnotationStyle
from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, PointObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.segments import SegmentStyle
from wenu3d.target_lines import ParallaxIllustration
from wenu3d.targets import CelestialTarget
from wenu3d.transforms import LocalCartoonTransform


def make_local_cartoon(scale: float = 1.0) -> LocalCartoonLayer:
    earth = EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=(0.0, 0.0, 1.0),
        observer_zenith=(1.0, 0.0, 0.0),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )
    local = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=LocalCartoonTransform(scale=scale),
    )
    frame = horizontal_frame()
    for name, position in (
        ("first", (-0.20, 0.0, 0.0)),
        ("second", (0.20, 0.0, 0.0)),
    ):
        observer = Observer(name=name, position=position, frame=frame)
        local.add_observer(
            ObserverComposition(
                name=f"{name}.composition",
                observer=observer,
                representation=PointObserverRepresentation(
                    name=f"{name}.point",
                    observer=observer,
                    radius=0.015,
                ),
            )
        )
    return local


def make_target() -> CelestialTarget:
    return CelestialTarget(
        name="displayed_star",
        direction=(0.0, 0.0, 1.0),
        shell_radius=2.0,
    )


def make_illustration(
    *,
    scale: float = 1.0,
    **kwargs,
) -> ParallaxIllustration:
    arguments = {
        "name": "parallax.star",
        "target": make_target(),
        "local_cartoon": make_local_cartoon(scale),
        "observer_anchors": {
            "first": "position",
            "second": "position",
        },
    }
    arguments.update(kwargs)
    return ParallaxIllustration(**arguments)


def test_parallax_illustration_owns_explicit_components_and_note() -> None:
    illustration = make_illustration()

    assert [obj.name for obj in illustration.objects] == [
        "parallax.star.target",
        "parallax.star.centered_direction",
        "parallax.star.sight_line.first",
        "parallax.star.sight_line.second",
        "parallax.star.interpretation_note",
    ]
    assert illustration.note_annotation.annotation.text == (
        illustration.interpretation_note
    )
    assert "not physical distance" in illustration.interpretation_note
    assert illustration.display_distance == illustration.target.shell_radius
    assert not hasattr(illustration, "physical_target_distance")


def test_sight_lines_share_displayed_endpoint_and_expose_baseline() -> None:
    illustration = make_illustration()
    first = illustration.sight_line_objects["first"].segment
    second = illustration.sight_line_objects["second"].segment

    assert first.end == second.end == illustration.target.display_position
    np.testing.assert_allclose(
        illustration.baseline("first", "second"),
        (0.4, 0.0, 0.0),
        atol=1e-12,
    )
    assert illustration.baseline_length("first", "second") == pytest.approx(
        0.4
    )


def test_convergence_angle_is_finite_and_decreases_with_baseline_scale() -> None:
    conspicuous = make_illustration(scale=1.0)
    negligible = make_illustration(scale=0.01)

    conspicuous_angle = conspicuous.convergence_angle_deg("first", "second")
    negligible_angle = negligible.convergence_angle_deg("first", "second")

    assert 0.0 < negligible_angle < conspicuous_angle < 180.0
    assert negligible.baseline_length("first", "second") == pytest.approx(
        0.004
    )
    assert conspicuous.target.direction == negligible.target.direction
    assert conspicuous.target.display_position == negligible.target.display_position


def test_note_and_line_styles_remain_configurable() -> None:
    direction_style = SegmentStyle(color="navy", width=5.0)
    sight_style = SegmentStyle(color="orange", width=3.0)
    note_style = AnnotationStyle(color="purple", font_size=16, bold=True)

    illustration = make_illustration(
        direction_style=direction_style,
        sight_line_style=sight_style,
        note_style=note_style,
    )

    assert illustration.direction_style is direction_style
    assert illustration.sight_line_style is sight_style
    assert illustration.note_style is note_style
    assert illustration.note_annotation.annotation.style is note_style


def test_interpretation_note_is_optional_without_removing_geometry() -> None:
    illustration = make_illustration(show_note=False)

    assert illustration.note_annotation is None
    assert len(illustration.sight_line_objects) == 2
    assert len(illustration.objects) == 4


def test_parallax_illustration_builds_off_screen() -> None:
    illustration = make_illustration()
    plotter = pv.Plotter(off_screen=True)

    try:
        illustration.build(plotter)

        assert len(illustration.objects) == 5
        assert len(illustration.actors) == 5
        assert illustration.marker_object.mesh is not None
        assert illustration.note_annotation.actors
    finally:
        illustration.detach(render=False)
        plotter.close()


def test_parallax_requires_multiple_observers_and_valid_note_options() -> None:
    local = make_local_cartoon()
    with pytest.raises(ValueError, match="at least two"):
        ParallaxIllustration(
            name="bad",
            target=make_target(),
            local_cartoon=local,
            observer_anchors={"first": "position"},
        )
    with pytest.raises(TypeError, match="mapping"):
        ParallaxIllustration(
            name="bad",
            target=make_target(),
            local_cartoon=local,
            observer_anchors=[],
        )
    with pytest.raises(TypeError, match="note_style"):
        make_illustration(note_style=object())
    with pytest.raises(TypeError, match="show_note"):
        make_illustration(show_note=1)


def test_parallax_pair_queries_validate_distinct_known_observers() -> None:
    illustration = make_illustration()

    with pytest.raises(ValueError, match="distinct"):
        illustration.baseline("first", "first")
    with pytest.raises(KeyError, match="Unknown parallax observer"):
        illustration.baseline("first", "missing")
