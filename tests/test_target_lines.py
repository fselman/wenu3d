import numpy as np
import pyvista as pv
import pytest

from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, PointObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.segments import SegmentStyle, SightLine
from wenu3d.target_lines import TargetLineIllustration
from wenu3d.targets import CelestialTarget
from wenu3d.transforms import LocalCartoonTransform


def make_local_cartoon(
    transform: LocalCartoonTransform | None = None,
) -> LocalCartoonLayer:
    earth = EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=(0.0, 0.0, 1.0),
        observer_zenith=(1.0, 0.0, 0.0),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=transform,
    )
    frame = horizontal_frame()
    for name, position in (
        ("first", (0.0, 0.0, 0.25)),
        ("second", (0.0, 0.0, -0.25)),
    ):
        observer = Observer(name=name, position=position, frame=frame)
        layer.add_observer(
            ObserverComposition(
                name=f"{name}.composition",
                observer=observer,
                representation=PointObserverRepresentation(
                    name=f"{name}.point",
                    observer=observer,
                    radius=0.01,
                ),
            )
        )
    return layer


def make_target() -> CelestialTarget:
    return CelestialTarget(
        name="star",
        direction=(0.0, 1.0, 1.0),
        shell_radius=2.0,
    )


def make_illustration(**kwargs) -> TargetLineIllustration:
    arguments = {
        "name": "target_lines.star",
        "target": make_target(),
        "local_cartoon": make_local_cartoon(
            LocalCartoonTransform(
                translation=(0.3, -0.2, 0.1),
                scale=0.5,
            )
        ),
        "observer_anchors": {
            "first": "position",
            "second": "position",
        },
    }
    arguments.update(kwargs)
    return TargetLineIllustration(**arguments)


def test_target_line_illustration_exposes_ordered_components() -> None:
    illustration = make_illustration()

    assert [obj.name for obj in illustration.objects] == [
        "target_lines.star.target",
        "target_lines.star.centered_direction",
        "target_lines.star.sight_line.first",
        "target_lines.star.sight_line.second",
    ]
    assert illustration.marker_object.marker.position == pytest.approx(
        illustration.target.display_position
    )
    assert tuple(illustration.sight_line_objects) == ("first", "second")


def test_centered_direction_starts_at_origin_and_ends_at_marker() -> None:
    illustration = make_illustration()
    segment = illustration.centered_direction_object.segment

    assert segment.start == (0.0, 0.0, 0.0)
    assert segment.end == illustration.target.display_position
    np.testing.assert_allclose(
        segment.direction,
        illustration.target.direction,
        atol=1e-12,
    )


def test_sight_lines_resolve_transformed_anchors_and_share_endpoint() -> None:
    illustration = make_illustration()
    local = illustration.local_cartoon
    target_position = illustration.target.display_position

    for observer, obj in illustration.sight_line_objects.items():
        sight_line = obj.segment
        assert isinstance(sight_line, SightLine)
        np.testing.assert_allclose(
            sight_line.start,
            local.observer_anchor(observer, "position"),
            atol=1e-12,
        )
        assert sight_line.end == target_position


def test_centered_direction_is_optional_without_removing_sight_lines() -> None:
    illustration = make_illustration(include_centered_direction=False)

    assert illustration.centered_direction_object is None
    assert len(illustration.sight_line_objects) == 2
    assert len(illustration.objects) == 3


def test_sight_lines_are_explicit_snapshots_of_local_transform() -> None:
    local = make_local_cartoon(LocalCartoonTransform.identity())
    target = make_target()
    first = TargetLineIllustration(
        name="first_snapshot",
        target=target,
        local_cartoon=local,
        observer_anchors={"first": "position"},
    )
    local.set_transform(
        LocalCartoonTransform(translation=(1.0, 0.0, 0.0), scale=0.25),
        render=False,
    )
    second = TargetLineIllustration(
        name="second_snapshot",
        target=target,
        local_cartoon=local,
        observer_anchors={"first": "position"},
    )

    assert first.sight_line_objects["first"].segment.start != (
        second.sight_line_objects["first"].segment.start
    )
    assert first.marker_object.marker.position == target.display_position
    assert second.marker_object.marker.position == target.display_position
    assert first.centered_direction_object.segment.start == (0.0, 0.0, 0.0)
    assert second.centered_direction_object.segment.start == (0.0, 0.0, 0.0)


def test_styles_remain_caller_configurable_and_shared_by_role() -> None:
    direction_style = SegmentStyle(color="navy", width=6.0, opacity=0.9)
    sight_style = SegmentStyle(color="orange", width=4.0, opacity=0.6)

    illustration = make_illustration(
        direction_style=direction_style,
        sight_line_style=sight_style,
    )

    assert illustration.direction_style is direction_style
    assert illustration.sight_line_style is sight_style
    assert illustration.centered_direction_object.segment.style is (
        direction_style
    )
    assert all(
        obj.segment.style is sight_style
        for obj in illustration.sight_line_objects.values()
    )


def test_target_line_illustration_builds_real_marker_and_segments() -> None:
    illustration = make_illustration()
    plotter = pv.Plotter(off_screen=True)

    try:
        illustration.build(plotter)

        assert len(illustration.objects) == 4
        assert len(illustration.actors) == 4
        assert illustration.marker_object.mesh is not None
        assert all(
            obj.mesh is not None
            for obj in illustration.sight_line_objects.values()
        )
    finally:
        illustration.detach(render=False)
        plotter.close()


def test_built_sight_lines_follow_local_scale_without_actor_accumulation() -> None:
    illustration = make_illustration()
    local = illustration.local_cartoon
    plotter = pv.Plotter(off_screen=True)

    try:
        local.build(plotter)
        illustration.build(plotter)
        original_actor_count = len(plotter.actors)
        target_position = illustration.target.display_position
        centered = illustration.centered_direction_object.segment

        local.set_scale(0.1, render=False)

        assert len(plotter.actors) == original_actor_count
        assert len(illustration.actors) == len(illustration.objects)
        assert centered.start == (0.0, 0.0, 0.0)
        assert centered.end == target_position
        assert illustration.marker_object.marker.position == target_position
        for observer, obj in illustration.sight_line_objects.items():
            np.testing.assert_allclose(
                obj.segment.start,
                local.observer_anchor(observer, "position"),
                atol=1e-12,
            )
            assert obj.segment.end == target_position

        illustration.detach(render=False)
        starts_after_detach = {
            name: obj.segment.start
            for name, obj in illustration.sight_line_objects.items()
        }
        local.set_scale(0.2, render=False)
        assert {
            name: obj.segment.start
            for name, obj in illustration.sight_line_objects.items()
        } == starts_after_detach
    finally:
        illustration.detach(render=False)
        local.detach(render=False)
        plotter.close()


def test_target_line_illustration_validates_explicit_composition() -> None:
    with pytest.raises(TypeError, match="CelestialTarget"):
        TargetLineIllustration(name="bad", target=object())
    with pytest.raises(TypeError, match="mapping"):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            observer_anchors=[],
        )
    with pytest.raises(TypeError, match="LocalCartoonLayer"):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            observer_anchors={"first": "position"},
        )
    with pytest.raises(ValueError, match="contain a line"):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            include_centered_direction=False,
        )
    with pytest.raises(TypeError, match="boolean"):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            include_centered_direction=1,
        )
    for field_name in ("direction_style", "sight_line_style"):
        with pytest.raises(TypeError, match=field_name):
            TargetLineIllustration(
                name="bad",
                target=make_target(),
                **{field_name: object()},
            )


def test_target_line_illustration_rejects_invalid_or_unknown_anchors() -> None:
    local = make_local_cartoon()
    for observer_anchors in ({"": "position"}, {"first": ""}):
        with pytest.raises(ValueError, match="names"):
            TargetLineIllustration(
                name="bad",
                target=make_target(),
                local_cartoon=local,
                observer_anchors=observer_anchors,
            )
    with pytest.raises(KeyError):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            local_cartoon=local,
            observer_anchors={"missing": "position"},
        )
    with pytest.raises(KeyError, match="Unknown observer anchor"):
        TargetLineIllustration(
            name="bad",
            target=make_target(),
            local_cartoon=local,
            observer_anchors={"first": "missing"},
        )
