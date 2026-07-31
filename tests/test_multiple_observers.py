from unittest.mock import Mock

import numpy as np
import pytest

from wenu3d.earth import EarthObject
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, ObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.transforms import LocalCartoonTransform


class PointRepresentation(ObserverRepresentation):
    @property
    def anchors(self):
        return {"site": self.observer.position.copy()}

    def build(self, plotter) -> None:
        self._prepare_build(plotter)
        self.add_actor(Mock())


def make_composition(observer: Observer) -> ObserverComposition:
    return ObserverComposition(
        name=f"{observer.name}.composition",
        observer=observer,
        representation=PointRepresentation(
            name=f"{observer.name}.point",
            observer=observer,
        ),
    )


def make_earth() -> EarthObject:
    return EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=np.array([0.0, 0.0, 1.0]),
        observer_zenith=np.array([1.0, 0.0, 0.0]),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )


def test_geographic_observer_constructs_semantic_antipode() -> None:
    observer = Observer.at_geographic_site(
        "la_ligua",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    antipode = observer.antipode("la_ligua_antipode")

    assert antipode.latitude_deg == pytest.approx(32.4524)
    assert antipode.longitude_deg == pytest.approx(108.7689)
    np.testing.assert_allclose(antipode.position, -observer.position, atol=1e-12)
    np.testing.assert_allclose(
        antipode.frame.pole,
        -observer.frame.pole,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        antipode.frame.east,
        -observer.frame.east,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        antipode.frame.zero,
        observer.frame.zero,
        atol=1e-12,
    )


def test_explicit_observer_has_no_geographic_antipode() -> None:
    observer = Observer(
        name="explicit",
        position=np.array([0.0, 0.0, 0.25]),
        frame=Observer.at_geographic_site(
            "frame_source",
            latitude_deg=90.0,
            longitude_deg=0.0,
            earth_radius=0.25,
        ).frame,
    )

    with pytest.raises(ValueError, match="geographic"):
        observer.antipode("missing")


def test_antipodal_observers_have_distinct_oriented_ideal_horizons() -> None:
    observer = Observer.at_geographic_site(
        "first",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    antipode = observer.antipode("second")
    first = make_composition(observer)
    second = make_composition(antipode)

    assert first.ideal_horizon is not second.ideal_horizon
    np.testing.assert_allclose(
        second.ideal_horizon.normal,
        -first.ideal_horizon.normal,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        second.ideal_horizon.east,
        -first.ideal_horizon.east,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        second.ideal_horizon.north,
        first.ideal_horizon.north,
        atol=1e-12,
    )


def test_antipodal_compositions_share_one_earth_and_transform() -> None:
    observer = Observer.at_geographic_site(
        "first",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    antipode = observer.antipode("second")
    earth = make_earth()
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=0.4,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=transform,
    )
    first = make_composition(observer)
    second = make_composition(antipode)

    layer.add_observer(first)
    layer.add_observer(second)

    assert layer.earth is earth
    assert layer.objects == [earth, first, second]
    assert layer.observer_compositions == (first, second)
    translation = np.asarray(transform.translation)
    np.testing.assert_allclose(
        layer.observer_position("first") - translation,
        -(layer.observer_position("second") - translation),
        atol=1e-12,
    )
