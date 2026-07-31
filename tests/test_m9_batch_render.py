from unittest.mock import patch

import numpy as np
import pyvista as pv

from wenu3d.earth import EarthObject
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, PointObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.platforms import LocalPlatform
from wenu3d.surface_object import SurfaceObject
from wenu3d.surfaces import PlaneSurface, SurfaceStyle
from wenu3d.transforms import LocalCartoonTransform


def make_earth() -> EarthObject:
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


def make_composition(
    observer: Observer,
    *,
    color: str,
) -> ObserverComposition:
    platform = LocalPlatform(
        name=f"{observer.name}.platform",
        surface=SurfaceObject(
            name=f"{observer.name}.platform.surface",
            surface=PlaneSurface(
                center=observer.position,
                normal=observer.frame.pole,
                axis_u=observer.frame.east,
                width=0.14,
                height=0.10,
                style=SurfaceStyle(
                    color=color,
                    opacity=0.70,
                    show_edges=True,
                ),
            ),
        ),
    )
    return ObserverComposition(
        name=f"{observer.name}.composition",
        observer=observer,
        representation=PointObserverRepresentation(
            name=f"{observer.name}.point",
            observer=observer,
            radius=0.018,
            color=color,
        ),
        context=(platform,),
    )


def test_m9_antipodal_composition_renders_off_screen(tmp_path) -> None:
    output = tmp_path / "m9-antipodal-composition.png"
    earth = make_earth()
    geographic = Observer.at_geographic_site(
        "la_ligua",
        latitude_deg=-32.4524,
        longitude_deg=-71.2311,
        earth_radius=earth.radius,
    )
    observers = (
        earth.display_observer(geographic),
        earth.display_observer(geographic.antipode("antipode")),
    )
    compositions = (
        make_composition(observers[0], color="#d4af37"),
        make_composition(observers[1], color="#4f81bd"),
    )
    transform = LocalCartoonTransform(
        translation=(0.04, -0.03, 0.02),
        scale=0.82,
    )
    local = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=transform,
    )
    for composition in compositions:
        local.add_observer(composition)

    horizons = tuple(
        SurfaceObject(
            name=f"{composition.observer.name}.ideal_horizon",
            surface=composition.ideal_horizon.as_surface(
                width=0.85,
                style=SurfaceStyle(
                    color="#8aa6c1",
                    opacity=0.12,
                    show_edges=True,
                ),
                visible=True,
            ),
        )
        for composition in compositions
    )
    plotter = pv.Plotter(off_screen=True, window_size=(400, 300))

    def simple_earth(radius, **_kwargs):
        return pv.Sphere(radius=radius), None

    try:
        with patch("wenu3d.earth.realistic_earth", side_effect=simple_earth):
            local.build(plotter)
        for horizon in horizons:
            horizon.build(plotter)
        plotter.camera_position = "iso"
        plotter.set_background("white")
        image = plotter.screenshot(
            filename=str(output),
            return_img=True,
        )
    finally:
        local.detach(render=False)
        for horizon in horizons:
            horizon.detach(render=False)
        plotter.close()

    assert output.is_file()
    assert output.stat().st_size > 0
    assert isinstance(image, np.ndarray)
    assert image.shape[:2] == (300, 400)
    assert image.shape[2] in (3, 4)
    assert np.any(image[..., :3] < 250)
    assert len(local.observer_compositions) == 2
    assert len(local.actors) == 0
    assert all(horizon.actors == [] for horizon in horizons)
    np.testing.assert_allclose(
        observers[1].position,
        -observers[0].position,
        atol=1e-12,
    )
    assert all(horizon not in local.objects for horizon in horizons)
