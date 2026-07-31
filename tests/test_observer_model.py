from unittest.mock import Mock, patch

import numpy as np
import pytest

from wenu3d.frames import SphericalFrame, horizontal_frame
from wenu3d.geography import geographic_position, local_enu_frame
from wenu3d.horizons import IdealHorizon
from wenu3d.observer import (
    Observer,
    ObserverComposition,
    ObserverRepresentation,
    StickFigureRepresentation,
    add_observer,
)


def explicit_observer(name: str = "observer") -> Observer:
    return Observer(
        name=name,
        position=np.array([0.0, 0.0, 0.262]),
        frame=horizontal_frame(),
    )


class DummyRepresentation(ObserverRepresentation):
    def __init__(self, *, name: str, observer: Observer) -> None:
        super().__init__(name=name, observer=observer)
        self.actor = Mock()

    @property
    def anchors(self):
        return {
            "feet": self.observer.position.copy(),
            "instrument": self.observer.position
            + 0.1 * self.observer.frame.pole,
        }

    def build(self, plotter) -> None:
        self._prepare_build(plotter)
        self.add_actor(self.actor)


def test_observer_validates_identity_and_copies_position() -> None:
    position = np.array([1.0, 2.0, 3.0])
    observer = Observer(
        name="  navigator  ",
        position=position,
        frame=horizontal_frame(),
    )
    position[0] = 99.0

    assert observer.name == "navigator"
    np.testing.assert_allclose(observer.position, [1.0, 2.0, 3.0])
    assert observer.position.flags.writeable is False


@pytest.mark.parametrize(
    ("name", "position", "error", "message"),
    [
        (" ", [0.0, 0.0, 0.0], ValueError, "name"),
        ("observer", [0.0, 0.0], ValueError, "position"),
        ("observer", [0.0, np.nan, 0.0], ValueError, "position"),
        ("observer", [0.0, 0.0, 0.0], TypeError, "frame"),
    ],
)
def test_observer_rejects_invalid_core_state(
    name,
    position,
    error,
    message,
) -> None:
    frame = object() if error is TypeError else horizontal_frame()
    with pytest.raises(error, match=message):
        Observer(name=name, position=position, frame=frame)


def test_geographic_observer_uses_earth_fixed_position_and_frame() -> None:
    observer = Observer.at_geographic_site(
        "La Ligua",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )

    np.testing.assert_allclose(
        observer.position,
        geographic_position(-32.4524, -71.2311, radius=0.25),
    )
    expected_frame = local_enu_frame(-32.4524, -71.2311)
    np.testing.assert_allclose(observer.frame.east, expected_frame.east)
    np.testing.assert_allclose(observer.frame.zero, expected_frame.zero)
    np.testing.assert_allclose(observer.frame.pole, expected_frame.pole)
    assert observer.latitude_deg == -32.4524
    assert observer.longitude_deg == -71.2311


def test_geographic_observer_rejects_inconsistent_position() -> None:
    with pytest.raises(ValueError, match="position"):
        Observer(
            name="inconsistent",
            position=np.array([0.25, 0.0, 0.0]),
            frame=local_enu_frame(30.0, 40.0),
            latitude_deg=30.0,
            longitude_deg=40.0,
        )


def test_geographic_observer_rejects_inconsistent_frame() -> None:
    with pytest.raises(ValueError, match="frame"):
        Observer(
            name="inconsistent",
            position=geographic_position(30.0, 40.0, radius=0.25),
            frame=horizontal_frame(),
            latitude_deg=30.0,
            longitude_deg=40.0,
        )


def test_stick_figure_exposes_semantic_anchors() -> None:
    observer = explicit_observer()
    representation = StickFigureRepresentation(
        name="observer.stick",
        observer=observer,
        height=0.23,
    )

    np.testing.assert_allclose(representation.anchor("feet"), observer.position)
    np.testing.assert_allclose(
        representation.anchor("left_foot"),
        observer.position - 0.023 * observer.frame.east,
    )
    np.testing.assert_allclose(
        representation.anchor("right_foot"),
        observer.position + 0.023 * observer.frame.east,
    )
    np.testing.assert_allclose(
        representation.anchor("hips"),
        observer.position + 0.0874 * observer.frame.pole,
    )
    np.testing.assert_allclose(
        representation.anchor("eye"),
        observer.position + 0.207 * observer.frame.pole,
    )
    np.testing.assert_allclose(
        representation.anchor("eye"),
        representation.anchor("head"),
    )


def test_representation_anchor_is_returned_as_a_copy() -> None:
    representation = StickFigureRepresentation(
        name="observer.stick",
        observer=explicit_observer(),
        height=0.23,
    )
    anchor = representation.anchor("feet")
    anchor[0] = 99.0

    np.testing.assert_allclose(
        representation.anchor("feet"),
        [0.0, 0.0, 0.262],
    )
    with pytest.raises(KeyError, match="Unknown observer anchor"):
        representation.anchor("missing")


@pytest.mark.parametrize("height", [0.0, -1.0, np.inf, np.nan])
def test_stick_figure_rejects_invalid_height(height: float) -> None:
    with pytest.raises(ValueError, match="height"):
        StickFigureRepresentation(
            name="observer.stick",
            observer=explicit_observer(),
            height=height,
        )


def test_stick_figure_preserves_existing_seven_actor_geometry() -> None:
    plotter = Mock()
    tube_actors = [Mock() for _ in range(6)]
    head_actor = Mock()
    head_mesh = object()
    plotter.add_mesh.return_value = head_actor
    representation = StickFigureRepresentation(
        name="observer.stick",
        observer=explicit_observer(),
        height=0.23,
    )

    with (
        patch("wenu3d.observer.add_tube", side_effect=tube_actors) as add_tube,
        patch("wenu3d.observer.pv.Sphere", return_value=head_mesh) as sphere,
    ):
        representation.build(plotter)

    assert add_tube.call_count == 6
    sphere.assert_called_once()
    plotter.add_mesh.assert_called_once_with(
        head_mesh,
        color="#d4af8a",
        smooth_shading=True,
    )
    assert representation.actors == tube_actors + [head_actor]


def test_stick_figure_rebuild_removes_previous_actors() -> None:
    plotter = Mock()
    first_actors = [Mock() for _ in range(7)]
    second_actors = [Mock() for _ in range(7)]
    tubes = first_actors[:6] + second_actors[:6]
    heads = [first_actors[6], second_actors[6]]
    plotter.add_mesh.side_effect = heads
    representation = StickFigureRepresentation(
        name="observer.stick",
        observer=explicit_observer(),
        height=0.23,
    )

    with (
        patch("wenu3d.observer.add_tube", side_effect=tubes),
        patch("wenu3d.observer.pv.Sphere"),
    ):
        representation.build(plotter)
        representation.build(plotter)

    assert representation.actors == second_actors
    assert plotter.remove_actor.call_count == 7


def test_observer_composition_associates_representation_and_context() -> None:
    observer = explicit_observer()
    representation = DummyRepresentation(
        name="observer.first",
        observer=observer,
    )
    composition = ObserverComposition(
        name="observer.composition",
        observer=observer,
        representation=representation,
    )
    context = Mock()
    context.name = "observer.context"
    composition.add(context)

    assert composition.observer is observer
    assert composition.representation is representation
    assert composition.ideal_horizon.observer is observer
    assert composition.objects == [representation, context]
    np.testing.assert_allclose(composition.anchor("feet"), observer.position)


def test_observer_composition_replaces_representation_and_retains_context() -> None:
    observer = explicit_observer()
    first = DummyRepresentation(name="observer.first", observer=observer)
    second = DummyRepresentation(name="observer.second", observer=observer)
    composition = ObserverComposition(
        name="observer.composition",
        observer=observer,
        representation=first,
    )
    context = Mock()
    composition.add(context)

    composition.set_representation(second)

    assert composition.representation is second
    assert composition.objects == [second, context]
    np.testing.assert_allclose(
        composition.anchor("instrument"),
        observer.position + 0.1 * observer.frame.pole,
    )


def test_attached_composition_replacement_removes_old_representation() -> None:
    observer = explicit_observer()
    first = DummyRepresentation(name="observer.first", observer=observer)
    second = DummyRepresentation(name="observer.second", observer=observer)
    composition = ObserverComposition(
        name="observer.composition",
        observer=observer,
        representation=first,
    )
    plotter = Mock()
    composition.build(plotter)

    composition.set_representation(second)

    plotter.remove_actor.assert_called_once_with(first.actor, render=False)
    assert composition.actors == [second.actor]
    plotter.render.assert_called_once_with()


def test_composition_rejects_representation_for_another_observer() -> None:
    observer = explicit_observer("first")
    other = explicit_observer("other")
    representation = DummyRepresentation(
        name="observer.other",
        observer=other,
    )

    with pytest.raises(ValueError, match="composition observer"):
        ObserverComposition(
            name="observer.composition",
            observer=observer,
            representation=representation,
        )


def test_composition_validates_explicit_ideal_horizon() -> None:
    observer = explicit_observer("first")
    other = explicit_observer("other")
    representation = DummyRepresentation(
        name="observer.first",
        observer=observer,
    )

    with pytest.raises(ValueError, match="composition observer"):
        ObserverComposition(
            name="observer.composition",
            observer=observer,
            representation=representation,
            ideal_horizon=IdealHorizon(other),
        )

    with pytest.raises(TypeError, match="IdealHorizon"):
        ObserverComposition(
            name="observer.composition",
            observer=observer,
            representation=representation,
            ideal_horizon=object(),
        )


def test_legacy_add_observer_returns_existing_seven_actor_shape() -> None:
    plotter = Mock()
    tube_actors = [Mock() for _ in range(6)]
    head_actor = Mock()
    plotter.add_mesh.return_value = head_actor

    with (
        patch("wenu3d.observer.add_tube", side_effect=tube_actors),
        patch("wenu3d.observer.pv.Sphere"),
    ):
        actors = add_observer(
            plotter,
            base=np.array([0.0, -0.0125, 0.262]),
            zenith=np.array([0.0, 0.0, 1.0]),
            east=np.array([1.0, 0.0, 0.0]),
            height=0.23,
        )

    assert actors == tube_actors + [head_actor]
