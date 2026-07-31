from unittest.mock import Mock

import numpy as np
import pytest

from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, ObserverRepresentation
from wenu3d.observer_model import Observer


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
        observer_zenith=np.array([0.0, 0.0, 1.0]),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )


def make_composition(name: str) -> ObserverComposition:
    observer = Observer(
        name=name,
        position=np.array([0.0, 0.0, 0.25]),
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
