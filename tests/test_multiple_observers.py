from unittest.mock import Mock

import numpy as np
import pytest

from wenu3d.earth import EarthObject
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import (
    ObserverComposition,
    ObserverRepresentation,
    PointObserverRepresentation,
)
from wenu3d.observer_model import Observer
from wenu3d.platforms import LocalPlatform
from wenu3d.surface_object import SurfaceObject
from wenu3d.surfaces import PlaneSurface
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


def make_platform(observer: Observer) -> LocalPlatform:
    return LocalPlatform(
        name=f"{observer.name}.platform",
        surface=SurfaceObject(
            name=f"{observer.name}.platform.surface",
            surface=PlaneSurface(
                center=observer.position,
                normal=observer.frame.pole,
                axis_u=observer.frame.east,
                width=0.12,
                height=0.09,
            ),
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


def make_la_ligua_earth() -> EarthObject:
    latitude_deg = -32.4524
    latitude = np.deg2rad(latitude_deg)
    return EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=(0.0, np.cos(latitude), np.sin(latitude)),
        observer_zenith=(0.0, 0.0, 1.0),
        observer_north=(0.0, 1.0, 0.0),
        latitude_deg=latitude_deg,
        longitude_deg=-71.2311,
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


def test_rendered_earth_maps_geographic_site_into_display_frame() -> None:
    geographic = Observer.at_geographic_site(
        "site",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    earth = make_la_ligua_earth()

    displayed = earth.display_observer(geographic)

    np.testing.assert_allclose(
        displayed.position,
        0.25 * earth.observer_zenith,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        displayed.frame.pole,
        earth.observer_zenith,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        displayed.frame.zero,
        earth.observer_north,
        atol=1e-12,
    )


def test_displayed_antipodes_own_independent_platforms_and_horizons() -> None:
    geographic = Observer.at_geographic_site(
        "first",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    earth = make_la_ligua_earth()
    first_observer = earth.display_observer(geographic)
    second_observer = earth.display_observer(geographic.antipode("second"))
    first_platform = make_platform(first_observer)
    second_platform = make_platform(second_observer)
    first = ObserverComposition(
        name="first.composition",
        observer=first_observer,
        representation=PointRepresentation(
            name="first.point",
            observer=first_observer,
        ),
        context=(first_platform,),
    )
    second = ObserverComposition(
        name="second.composition",
        observer=second_observer,
        representation=PointRepresentation(
            name="second.point",
            observer=second_observer,
        ),
        context=(second_platform,),
    )
    layer = LocalCartoonLayer(name="local", earth=earth)

    layer.add_observer(first)
    layer.add_observer(second)

    assert first.context_objects == (first_platform,)
    assert second.context_objects == (second_platform,)
    assert first_platform is not second_platform
    np.testing.assert_allclose(
        second_platform.surface.surface.center,
        -np.asarray(first_platform.surface.surface.center),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        second.ideal_horizon.normal,
        -first.ideal_horizon.normal,
        atol=1e-12,
    )
    np.testing.assert_allclose(first.ideal_horizon.origin, np.zeros(3))
    np.testing.assert_allclose(second.ideal_horizon.origin, np.zeros(3))


def test_display_observer_validates_geography_and_radius() -> None:
    earth = make_earth()
    explicit = Observer(
        name="explicit",
        position=(0.25, 0.0, 0.0),
        frame=Observer.at_geographic_site(
            "frame",
            latitude_deg=0.0,
            longitude_deg=0.0,
            earth_radius=0.25,
        ).frame,
    )
    wrong_radius = Observer.at_geographic_site(
        "wrong_radius",
        latitude_deg=0.0,
        longitude_deg=0.0,
        earth_radius=0.5,
    )

    with pytest.raises(TypeError, match="Observer"):
        earth.display_observer(object())
    with pytest.raises(ValueError, match="geographic"):
        earth.display_observer(explicit)
    with pytest.raises(ValueError, match="radius"):
        earth.display_observer(wrong_radius)


def test_antipodal_observers_and_platforms_build_under_shared_transform() -> None:
    geographic = Observer.at_geographic_site(
        "first",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=0.25,
    )
    earth = make_la_ligua_earth()
    first_observer = earth.display_observer(geographic)
    second_observer = earth.display_observer(geographic.antipode("second"))
    compositions = []
    for observer in (first_observer, second_observer):
        compositions.append(
            ObserverComposition(
                name=f"{observer.name}.composition",
                observer=observer,
                representation=PointObserverRepresentation(
                    name=f"{observer.name}.point",
                    observer=observer,
                    radius=0.01,
                ),
                context=(make_platform(observer),),
            )
        )
    transform = LocalCartoonTransform(
        translation=(0.3, -0.2, 0.1),
        scale=0.6,
    )
    layer = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=transform,
    )
    for composition in compositions:
        layer.add_observer(composition)
    earth.build = Mock()
    plotter = Mock()
    plotter.add_mesh.side_effect = [Mock() for _ in range(4)]

    layer.build(plotter)

    assert earth.build.call_count == 1
    assert len(layer.actors) == 4
    assert all(
        composition.context_objects[0].surface.mesh is not None
        for composition in compositions
    )
    for actor in layer.actors:
        np.testing.assert_allclose(actor.user_matrix, transform.matrix)
