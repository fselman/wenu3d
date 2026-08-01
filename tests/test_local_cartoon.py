from unittest.mock import Mock

import numpy as np
import pytest

from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import (
    ObserverComposition,
    ObserverRepresentation,
    PointObserverRepresentation,
)
from wenu3d.observer_model import Observer
from wenu3d.transforms import LocalCartoonTransform


class DummyRepresentation(ObserverRepresentation):
    @property
    def anchors(self):
        return {"feet": self.observer.position.copy()}

    def build(self, plotter) -> None:
        self._prepare_build(plotter)
        self.add_actor(Mock())


def make_earth() -> EarthObject:
    return EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=np.array([0.0, 0.0, 1.0]),
        observer_zenith=np.array([1.0, 0.0, 0.0]),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )


def make_composition(
    name: str,
    position=(0.0, 0.0, 0.25),
) -> ObserverComposition:
    observer = Observer(
        name=name,
        position=np.asarray(position, dtype=float),
        frame=horizontal_frame(),
    )
    representation = DummyRepresentation(
        name=f"{name}.representation",
        observer=observer,
    )
    return ObserverComposition(
        name=f"{name}.composition",
        observer=observer,
        representation=representation,
    )


def test_local_cartoon_owns_one_shared_earth() -> None:
    earth = make_earth()
    layer = LocalCartoonLayer(name="local", earth=earth)

    assert layer.earth is earth
    assert layer.objects == [earth]
    assert layer.observer_compositions == ()

    with pytest.raises(ValueError, match="shared Earth"):
        layer.add(make_earth())


def test_local_cartoon_registers_observer_compositions() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    first = make_composition("first")
    second = make_composition("second")

    assert layer.add_observer(first) is first
    assert layer.add(second) is second

    assert layer.observer_compositions == (first, second)
    assert layer.get_observer("first") is first
    assert layer.get_observer("second") is second
    assert layer.objects == [layer.earth, first, second]


def test_local_cartoon_rejects_duplicate_observer_identity() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.add_observer(make_composition("observer"))

    with pytest.raises(ValueError, match="already exists"):
        layer.add_observer(make_composition("observer"))


@pytest.mark.parametrize(
    ("earth", "error", "message"),
    [
        (object(), TypeError, "EarthObject"),
    ],
)
def test_local_cartoon_validates_earth(earth, error, message) -> None:
    with pytest.raises(error, match=message):
        LocalCartoonLayer(name="local", earth=earth)


def test_local_cartoon_validates_observer_composition() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())

    with pytest.raises(TypeError, match="ObserverComposition"):
        layer.add_observer(object())


def test_local_cartoon_defaults_to_identity_transform() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())

    assert layer.transform == LocalCartoonTransform.identity()
    np.testing.assert_allclose(
        layer.transform_points([1.0, 2.0, 3.0]),
        [1.0, 2.0, 3.0],
    )


def test_transformed_observer_position_and_anchor_use_one_transform() -> None:
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=2.0,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=transform,
    )
    composition = make_composition("navigator")
    layer.add_observer(composition)

    expected = transform.apply_points(composition.observer.position)
    np.testing.assert_allclose(layer.observer_position("navigator"), expected)
    np.testing.assert_allclose(layer.observer_anchor("navigator", "feet"), expected)


def test_shared_transform_applies_to_multiple_observers() -> None:
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    first = make_composition("first")
    second = make_composition("second", position=(0.0, 0.0, -0.25))
    layer.add_observer(first)
    layer.add_observer(second)
    layer.set_transform(LocalCartoonTransform(translation=(1.0, 0.0, 0.0), scale=0.5))

    np.testing.assert_allclose(layer.observer_position("first"), [1.0, 0.0, 0.125])
    np.testing.assert_allclose(layer.observer_position("second"), [1.0, 0.0, -0.125])


def test_local_cartoon_validates_transform() -> None:
    with pytest.raises(TypeError, match="LocalCartoonTransform"):
        LocalCartoonLayer(name="local", earth=make_earth(), transform=object())

    layer = LocalCartoonLayer(name="local", earth=make_earth())
    with pytest.raises(TypeError, match="LocalCartoonTransform"):
        layer.set_transform(object())


def test_non_identity_transform_is_applied_to_every_built_actor() -> None:
    earth_actor = Mock()
    observer_actor = Mock()
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=LocalCartoonTransform(
            translation=(1.0, 2.0, 3.0),
            scale=0.5,
        ),
    )
    composition = make_composition("observer")
    layer.add_observer(composition)
    layer.earth.build = Mock(
        side_effect=lambda plotter: layer.earth.actors.append(earth_actor)
    )
    composition.build = Mock(
        side_effect=lambda plotter: composition.actors.append(observer_actor)
    )

    layer.build(Mock())

    np.testing.assert_allclose(earth_actor.user_matrix, layer.transform.matrix)
    np.testing.assert_allclose(observer_actor.user_matrix, layer.transform.matrix)


def test_attached_transform_update_changes_model_and_actor_together() -> None:
    actor = Mock()
    plotter = Mock()
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.earth.build = Mock(
        side_effect=lambda current_plotter: layer.earth.actors.append(actor)
    )
    layer.build(plotter)
    plotter.render.reset_mock()
    transform = LocalCartoonTransform(
        translation=(0.0, 1.0, 0.0),
        scale=0.25,
    )

    layer.set_transform(transform)

    assert layer.transform is transform
    np.testing.assert_allclose(actor.user_matrix, transform.matrix)
    plotter.render.assert_called_once_with()


def test_attached_transform_update_can_defer_render() -> None:
    actor = Mock()
    plotter = Mock()
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.earth.build = Mock(
        side_effect=lambda current_plotter: layer.earth.actors.append(actor)
    )
    layer.build(plotter)
    plotter.render.reset_mock()
    transform = LocalCartoonTransform(scale=0.75)

    layer.set_transform(transform, render=False)

    np.testing.assert_allclose(actor.user_matrix, transform.matrix)
    plotter.render.assert_not_called()


def test_set_scale_preserves_translation() -> None:
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=LocalCartoonTransform(
            translation=(1.0, 2.0, 3.0),
            scale=0.5,
        ),
    )

    layer.set_scale(0.25)

    assert layer.transform.translation == (1.0, 2.0, 3.0)
    assert layer.transform.scale == 0.25


def test_place_on_surface_restores_nominal_translation() -> None:
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=LocalCartoonTransform(
            translation=(1.0, 2.0, 3.0),
            scale=0.4,
        ),
    )
    layer.add_observer(make_composition("navigator"))

    layer.place_on_surface(observer="navigator")

    assert layer.transform == LocalCartoonTransform(scale=0.4)


def test_place_observer_anchor_at_origin_updates_model_and_actor() -> None:
    actor = Mock()
    plotter = Mock()
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=LocalCartoonTransform(scale=0.5),
    )
    layer.add_observer(make_composition("navigator"))
    layer.earth.build = Mock(
        side_effect=lambda current_plotter: layer.earth.actors.append(actor)
    )
    layer.build(plotter)
    plotter.render.reset_mock()

    layer.place_observer_anchor_at_origin(
        observer="navigator",
        anchor="feet",
    )

    np.testing.assert_allclose(
        layer.observer_anchor("navigator", "feet"),
        [0.0, 0.0, 0.0],
    )
    assert layer.transform.scale == 0.5
    np.testing.assert_allclose(actor.user_matrix, layer.transform.matrix)
    plotter.render.assert_called_once_with()


def test_observer_anchor_height_translates_only_along_requested_axis() -> None:
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=LocalCartoonTransform(
            translation=(0.2, -0.3, 0.4),
            scale=0.5,
        ),
    )
    layer.add_observer(make_composition("navigator"))
    before = np.asarray(layer.transform.translation)

    layer.set_observer_anchor_height(
        observer="navigator",
        anchor="feet",
        axis=(0.0, 0.0, 1.0),
        height=-0.1,
        render=False,
    )

    assert layer.observer_anchor_height(
        observer="navigator",
        anchor="feet",
        axis=(0.0, 0.0, 1.0),
    ) == pytest.approx(-0.1)
    after = np.asarray(layer.transform.translation)
    np.testing.assert_allclose(after[:2], before[:2])
    assert layer.transform.scale == 0.5


def test_placement_modes_validate_observer_and_anchor_before_update() -> None:
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=0.5,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=transform,
    )
    layer.add_observer(make_composition("navigator"))

    with pytest.raises(KeyError):
        layer.place_on_surface(observer="missing")
    with pytest.raises(KeyError, match="Unknown observer anchor"):
        layer.place_observer_anchor_at_origin(
            observer="navigator",
            anchor="missing",
        )

    assert layer.transform is transform


def test_attached_layer_adds_second_observer_without_rebuilding_earth() -> None:
    earth_actor = Mock()
    first_actor = Mock()
    second_actor = Mock()
    plotter = Mock()
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=0.5,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=transform,
    )
    first = make_composition("first")
    second = make_composition("second", position=(0.0, 0.0, -0.25))
    layer.add_observer(first)
    layer.earth.build = Mock(
        side_effect=lambda current_plotter: layer.earth.actors.append(
            earth_actor
        )
    )
    first.build = Mock(
        side_effect=lambda current_plotter: first.actors.append(first_actor)
    )
    second.build = Mock(
        side_effect=lambda current_plotter: second.actors.append(second_actor)
    )
    layer.build(plotter)
    plotter.render.reset_mock()

    assert layer.add_observer(second) is second

    layer.earth.build.assert_called_once_with(plotter)
    second.build.assert_called_once_with(plotter)
    assert layer.objects == [layer.earth, first, second]
    assert layer.observer_compositions == (first, second)
    assert layer.actors == [earth_actor, first_actor, second_actor]
    np.testing.assert_allclose(second_actor.user_matrix, transform.matrix)
    plotter.render.assert_called_once_with()


def test_dynamically_added_observer_inherits_hidden_layer_state() -> None:
    actor = Mock()
    plotter = Mock()
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        visible=False,
    )
    layer.earth.build = Mock()
    layer.build(plotter)
    composition = make_composition("observer")
    composition.representation.build = Mock(
        side_effect=lambda current_plotter: (
            composition.representation.actors.append(actor)
        )
    )

    layer.add_observer(composition)

    actor.SetVisibility.assert_called_with(False)


def test_dynamic_observer_addition_can_defer_render() -> None:
    plotter = Mock()
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    layer.earth.build = Mock()
    layer.build(plotter)
    plotter.render.reset_mock()
    composition = make_composition("observer")
    composition.build = Mock()

    layer.add_observer(composition, render=False)

    plotter.render.assert_not_called()


def test_attached_representation_replacement_preserves_model_and_transform(
    monkeypatch,
) -> None:
    earth_actor = Mock()
    point_actor = Mock()
    point_mesh = object()
    plotter = Mock()
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=0.5,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=make_earth(),
        transform=transform,
    )
    composition = make_composition("navigator")
    observer = composition.observer
    horizon = composition.ideal_horizon
    layer.add_observer(composition)
    layer.earth.build = Mock(
        side_effect=lambda current_plotter: layer.earth.actors.append(
            earth_actor
        )
    )
    layer.build(plotter)
    old_actor = composition.representation.actors[0]
    plotter.add_mesh.return_value = point_actor
    monkeypatch.setattr("wenu3d.observer.pv.Sphere", lambda **kwargs: point_mesh)
    replacement = PointObserverRepresentation(
        name="navigator.point",
        observer=observer,
        radius=0.01,
    )
    plotter.render.reset_mock()

    layer.set_observer_representation("navigator", replacement)

    assert composition.observer is observer
    assert composition.ideal_horizon is horizon
    assert composition.representation is replacement
    assert layer.actors == [earth_actor, point_actor]
    assert old_actor not in layer.actors
    np.testing.assert_allclose(point_actor.user_matrix, transform.matrix)
    np.testing.assert_allclose(
        layer.observer_anchor("navigator", "position"),
        transform.apply_points(observer.position),
    )
    plotter.render.assert_called_once_with()


def test_representation_replacement_can_defer_render() -> None:
    plotter = Mock()
    layer = LocalCartoonLayer(name="local", earth=make_earth())
    composition = make_composition("navigator")
    layer.add_observer(composition)
    layer.earth.build = Mock()
    layer.build(plotter)
    replacement = DummyRepresentation(
        name="navigator.replacement",
        observer=composition.observer,
    )
    plotter.render.reset_mock()

    layer.set_observer_representation(
        "navigator",
        replacement,
        render=False,
    )

    plotter.render.assert_not_called()
