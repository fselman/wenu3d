from unittest.mock import patch

import numpy as np
import pyvista as pv
import pytest

from wenu3d.comparisons import LocalScaleComparison
from wenu3d.coordinates import HorizontalCoordinateIllustration
from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, PointObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.targets import CelestialTarget
from wenu3d.transforms import LocalCartoonTransform


def make_comparison() -> tuple[
    LocalScaleComparison,
    HorizontalCoordinateIllustration,
]:
    earth = EarthObject(
        name="earth",
        radius=0.25,
        rotation_axis=(0.0, 0.0, 1.0),
        observer_zenith=(1.0, 0.0, 0.0),
        latitude_deg=0.0,
        longitude_deg=0.0,
    )
    observer = Observer(
        name="observer",
        position=(0.0, 0.0, 0.25),
        frame=horizontal_frame(),
    )
    composition = ObserverComposition(
        name="observer.composition",
        observer=observer,
        representation=PointObserverRepresentation(
            name="observer.point",
            observer=observer,
            radius=0.035,
            color="#b05d4b",
        ),
    )
    local = LocalCartoonLayer(
        name="local",
        earth=earth,
        transform=LocalCartoonTransform(
            translation=(0.05, -0.03, 0.02),
            scale=0.8,
        ),
    )
    local.add_observer(composition)
    target = CelestialTarget(
        name="star",
        direction=horizontal_frame().point(55.0, 32.0),
        shell_radius=1.25,
    )
    coordinates = HorizontalCoordinateIllustration(
        name="horizontal.star",
        target=target,
        frame=horizontal_frame(),
        samples=31,
        show_labels=False,
    )
    comparison = LocalScaleComparison(
        local_cartoon=local,
        observer="observer",
        anchor="position",
        surface_scale=1.0,
        small_scale=0.12,
        observer_origin_scale=0.7,
    )
    return comparison, coordinates


def build_comparison_scene(plotter):
    comparison, coordinates = make_comparison()

    def simple_earth(radius, **_kwargs):
        return pv.Sphere(radius=radius), None

    with patch("wenu3d.earth.realistic_earth", side_effect=simple_earth):
        comparison.local_cartoon.build(plotter)
    coordinates.build(plotter)
    plotter.camera_position = "iso"
    plotter.set_background("white")
    return comparison, coordinates


def test_three_comparison_presentations_export_and_restore_state(tmp_path) -> None:
    plotter = pv.Plotter(off_screen=True, window_size=(360, 270))
    comparison, coordinates = build_comparison_scene(plotter)
    original = comparison.local_cartoon.transform

    try:
        images = comparison.export(tmp_path, window_size=(360, 270))
    finally:
        comparison.local_cartoon.detach(render=False)
        coordinates.detach(render=False)
        plotter.close()

    assert tuple(images) == (
        "surface",
        "small_cartoon",
        "observer_at_origin",
    )
    assert comparison.local_cartoon.transform is original
    for mode, image in images.items():
        output = tmp_path / f"{mode}.png"
        assert output.is_file()
        assert output.stat().st_size > 0
        assert image.shape[:2] == (270, 360)
        assert image.shape[2] in (3, 4)
        assert np.any(image[..., :3] < 250)
    assert not np.array_equal(images["surface"], images["small_cartoon"])
    assert not np.array_equal(
        images["surface"],
        images["observer_at_origin"],
    )


def test_repeated_exports_are_pixel_deterministic_and_celestial_fixed(
    tmp_path,
) -> None:
    plotter = pv.Plotter(off_screen=True, window_size=(320, 240))
    comparison, coordinates = build_comparison_scene(plotter)
    marker_before = coordinates.marker_object.mesh.points.copy()
    altitude_before = coordinates.altitude_curve_object.mesh.points.copy()
    azimuth_before = coordinates.azimuth_curve_object.mesh.points.copy()

    try:
        first = comparison.export(tmp_path / "first", window_size=(320, 240))
        second = comparison.export(tmp_path / "second", window_size=(320, 240))
        marker_after = coordinates.marker_object.mesh.points.copy()
        altitude_after = coordinates.altitude_curve_object.mesh.points.copy()
        azimuth_after = coordinates.azimuth_curve_object.mesh.points.copy()
    finally:
        comparison.local_cartoon.detach(render=False)
        coordinates.detach(render=False)
        plotter.close()

    for mode in first:
        np.testing.assert_array_equal(first[mode], second[mode])
    np.testing.assert_allclose(marker_after, marker_before)
    np.testing.assert_allclose(altitude_after, altitude_before)
    np.testing.assert_allclose(azimuth_after, azimuth_before)


def test_export_can_select_one_mode_and_transparent_rgba(tmp_path) -> None:
    plotter = pv.Plotter(off_screen=True, window_size=(200, 150))
    comparison, coordinates = build_comparison_scene(plotter)

    try:
        images = comparison.export(
            tmp_path,
            modes=("small_cartoon",),
            window_size=(200, 150),
            transparent_background=True,
        )
    finally:
        comparison.local_cartoon.detach(render=False)
        coordinates.detach(render=False)
        plotter.close()

    assert tuple(images) == ("small_cartoon",)
    assert images["small_cartoon"].shape == (150, 200, 4)
    assert (tmp_path / "small_cartoon.png").is_file()
    assert not (tmp_path / "surface.png").exists()


def test_export_validates_attachment_modes_and_options(tmp_path) -> None:
    comparison, _coordinates = make_comparison()
    with pytest.raises(RuntimeError, match="built layer"):
        comparison.export(tmp_path)

    plotter = pv.Plotter(off_screen=True)
    comparison, coordinates = build_comparison_scene(plotter)
    try:
        for modes in ((), ["surface"], ("surface", "surface")):
            with pytest.raises(ValueError, match="modes"):
                comparison.export(tmp_path, modes=modes)
        with pytest.raises(ValueError, match="Unknown"):
            comparison.export(tmp_path, modes=("giant",))
        for window_size in ((0, 200), (200,), [200, 150], (200.5, 150)):
            with pytest.raises(ValueError, match="window_size"):
                comparison.export(tmp_path, window_size=window_size)
        with pytest.raises(TypeError, match="transparent_background"):
            comparison.export(tmp_path, transparent_background=1)
    finally:
        comparison.local_cartoon.detach(render=False)
        coordinates.detach(render=False)
        plotter.close()
