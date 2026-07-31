import numpy as np
import pytest

from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import (
    ObserverComposition,
    PointObserverRepresentation,
    StickFigureRepresentation,
)
from wenu3d.observer_model import Observer
from wenu3d.segments import SegmentStyle
from wenu3d.transforms import LocalCartoonTransform


def make_earth() -> EarthObject:
    return EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=np.array([0.0, 0.0, 1.0]),
        observer_zenith=np.array([1.0, 0.0, 0.0]),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )


def make_stick_composition(
    name: str,
    position,
) -> ObserverComposition:
    observer = Observer(
        name=name,
        position=np.asarray(position, dtype=float),
        frame=horizontal_frame(),
    )
    return ObserverComposition(
        name=f"{name}.composition",
        observer=observer,
        representation=StickFigureRepresentation(
            name=f"{name}.stick",
            observer=observer,
            height=0.2,
        ),
    )


def test_sight_line_origin_uses_transformed_named_anchor() -> None:
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=0.5,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=transform,
    )
    composition = make_stick_composition(
        "navigator",
        (0.0, 0.0, 0.25),
    )
    layer.add_observer(composition)
    target = np.array([0.4, -0.2, 1.0])

    sight_line = layer.make_observer_sight_line(
        observer="navigator",
        anchor="eye",
        target_position=target,
    )

    np.testing.assert_allclose(
        sight_line.observer_position,
        transform.apply_points(composition.anchor("eye")),
    )
    np.testing.assert_allclose(sight_line.target_position, target)


def test_sight_line_uses_replacement_representation_anchor() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    composition = make_stick_composition(
        "navigator",
        (0.0, 0.0, 0.25),
    )
    layer.add_observer(composition)
    replacement = PointObserverRepresentation(
        name="navigator.point",
        observer=composition.observer,
        radius=0.01,
    )
    layer.set_observer_representation("navigator", replacement)
    layer.set_transform(
        LocalCartoonTransform(
            translation=(-0.25, 0.5, 0.0),
            scale=0.2,
        )
    )

    sight_line = layer.make_observer_sight_line(
        observer="navigator",
        anchor="position",
        target_position=(0.0, 0.0, 1.0),
    )

    np.testing.assert_allclose(
        sight_line.observer_position,
        layer.observer_position("navigator"),
    )


def test_multiple_observer_sight_lines_share_fixed_target() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.add_observer(make_stick_composition("first", (-0.1, 0.0, 0.25)))
    layer.add_observer(make_stick_composition("second", (0.1, 0.0, 0.25)))
    target = (0.0, 0.0, 1.0)

    first = layer.make_observer_sight_line(
        observer="first",
        anchor="feet",
        target_position=target,
    )
    second = layer.make_observer_sight_line(
        observer="second",
        anchor="feet",
        target_position=target,
    )

    assert first.target_position == second.target_position == target
    assert first.observer_position != second.observer_position


def test_sight_line_factory_preserves_style_visibility_and_validation() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.add_observer(make_stick_composition("navigator", (0.0, 0.0, 0.25)))
    style = SegmentStyle(color="cyan", width=3.0, opacity=0.4)

    sight_line = layer.make_observer_sight_line(
        observer="navigator",
        anchor="feet",
        target_position=(0.0, 0.0, 1.0),
        style=style,
        visible=False,
    )

    assert sight_line.style is style
    assert sight_line.visible is False
    with pytest.raises(KeyError):
        layer.make_observer_sight_line(
            observer="missing",
            anchor="feet",
            target_position=(0.0, 0.0, 1.0),
        )
    with pytest.raises(KeyError, match="Unknown observer anchor"):
        layer.make_observer_sight_line(
            observer="navigator",
            anchor="missing",
            target_position=(0.0, 0.0, 1.0),
        )
