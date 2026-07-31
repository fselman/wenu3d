from unittest.mock import Mock

import numpy as np
import pytest

from wenu3d.comparisons import LocalScaleComparison, ScaleComparisonState
from wenu3d.coordinates import HorizontalCoordinateGeometry
from wenu3d.earth import EarthObject
from wenu3d.frames import horizontal_frame
from wenu3d.local_cartoon import LocalCartoonLayer
from wenu3d.observer import ObserverComposition, PointObserverRepresentation
from wenu3d.observer_model import Observer
from wenu3d.targets import CelestialTarget


def make_local_cartoon() -> tuple[LocalCartoonLayer, ObserverComposition]:
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
            radius=0.01,
        ),
    )
    layer = LocalCartoonLayer(name="local", earth=earth)
    layer.add_observer(composition)
    return layer, composition


def make_comparison(**kwargs) -> LocalScaleComparison:
    local, _composition = make_local_cartoon()
    arguments = {
        "local_cartoon": local,
        "observer": "observer",
        "anchor": "position",
        "surface_scale": 1.0,
        "small_scale": 0.04,
        "observer_origin_scale": 0.75,
    }
    arguments.update(kwargs)
    return LocalScaleComparison(**arguments)


def test_comparison_exposes_three_ordered_documented_states() -> None:
    comparison = make_comparison()

    assert [state.name for state in comparison.states] == [
        "surface",
        "small_cartoon",
        "observer_at_origin",
    ]
    assert all(isinstance(state, ScaleComparisonState) for state in comparison.states)
    assert all(state.description for state in comparison.states)
    assert comparison.state("surface") is comparison.states[0]


def test_surface_and_small_states_are_explicit_reproducible_transforms() -> None:
    comparison = make_comparison()
    surface = comparison.state("surface").transform
    small = comparison.state("small_cartoon").transform

    assert surface.scale == 1.0
    assert surface.translation == (0.0, 0.0, 0.0)
    assert small.scale == 0.04
    assert small.translation == (0.0, 0.0, 0.0)

    comparison.local_cartoon.set_scale(0.3, render=False)
    assert comparison.state("surface").transform is surface
    assert comparison.state("small_cartoon").transform is small


def test_observer_origin_state_aligns_selected_anchor_exactly() -> None:
    comparison = make_comparison()

    state = comparison.apply("observer_at_origin", render=False)

    assert state.transform.scale == 0.75
    np.testing.assert_allclose(
        comparison.local_cartoon.observer_anchor("observer", "position"),
        np.zeros(3),
        atol=1e-12,
    )


def test_apply_changes_only_authoritative_local_transform() -> None:
    comparison = make_comparison()
    local = comparison.local_cartoon

    for mode in ("surface", "small_cartoon", "observer_at_origin"):
        state = comparison.apply(mode, render=False)
        assert local.transform is state.transform


def test_target_coordinate_curves_and_horizon_remain_fixed() -> None:
    comparison = make_comparison()
    composition = comparison.local_cartoon.get_observer("observer")
    target = CelestialTarget(
        name="star",
        direction=horizontal_frame().point(45.0, 30.0),
        shell_radius=2.0,
    )
    coordinates = HorizontalCoordinateGeometry(
        target=target,
        frame=horizontal_frame(),
        samples=11,
    )
    target_before = target.display_position
    altitude_before = coordinates.altitude_arc.points().copy()
    azimuth_before = coordinates.azimuth_arc.points().copy()
    horizon_origin_before = composition.ideal_horizon.origin.copy()
    horizon_normal_before = composition.ideal_horizon.normal.copy()

    for mode in ("surface", "small_cartoon", "observer_at_origin"):
        comparison.apply(mode, render=False)
        assert target.display_position == target_before
        np.testing.assert_allclose(coordinates.altitude_arc.points(), altitude_before)
        np.testing.assert_allclose(coordinates.azimuth_arc.points(), azimuth_before)
        np.testing.assert_allclose(
            composition.ideal_horizon.origin,
            horizon_origin_before,
        )
        np.testing.assert_allclose(
            composition.ideal_horizon.normal,
            horizon_normal_before,
        )


def test_attached_apply_updates_local_actors_and_can_defer_render() -> None:
    comparison = make_comparison()
    local = comparison.local_cartoon
    actor = Mock()
    local.actors.append(actor)
    local._plotter = Mock()

    state = comparison.apply("small_cartoon", render=False)

    np.testing.assert_allclose(actor.user_matrix, state.transform.matrix)
    local.attached_plotter.render.assert_not_called()


def test_comparison_validates_layer_observer_anchor_and_scales() -> None:
    local, _composition = make_local_cartoon()
    with pytest.raises(TypeError, match="LocalCartoonLayer"):
        LocalScaleComparison(
            local_cartoon=object(),
            observer="observer",
            anchor="position",
        )
    for observer, anchor in (("", "position"), ("observer", "")):
        with pytest.raises(ValueError):
            LocalScaleComparison(
                local_cartoon=local,
                observer=observer,
                anchor=anchor,
            )
    with pytest.raises(KeyError):
        LocalScaleComparison(
            local_cartoon=local,
            observer="missing",
            anchor="position",
        )
    with pytest.raises(KeyError, match="Unknown observer anchor"):
        LocalScaleComparison(
            local_cartoon=local,
            observer="observer",
            anchor="missing",
        )
    for field_name in (
        "surface_scale",
        "small_scale",
        "observer_origin_scale",
    ):
        with pytest.raises(ValueError):
            LocalScaleComparison(
                local_cartoon=local,
                observer="observer",
                anchor="position",
                **{field_name: 0.0},
            )


def test_comparison_rejects_unknown_mode_without_changing_transform() -> None:
    comparison = make_comparison()
    before = comparison.local_cartoon.transform

    with pytest.raises(ValueError, match="Unknown"):
        comparison.apply("giant_cartoon")

    assert comparison.local_cartoon.transform is before
