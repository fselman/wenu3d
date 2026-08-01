import wenu3d


def test_stable_public_api_is_explicit_unique_and_resolvable() -> None:
    exported = wenu3d.__all__

    assert isinstance(exported, list)
    assert len(exported) == len(set(exported))
    assert all(not name.startswith("_") for name in exported)
    assert all(hasattr(wenu3d, name) for name in exported)


def test_representative_horizon_a_types_are_stable_package_exports() -> None:
    expected = {
        "CelestialScene",
        "SceneObject",
        "Layer",
        "IllustrationLayer",
        "Annotation",
        "ControlManager",
        "CelestialShellObject",
        "LocalCartoonLayer",
        "Observer",
        "CelestialTarget",
        "HorizontalCoordinateIllustration",
        "EquatorialCoordinateIllustration",
        "TargetLineIllustration",
        "ParallaxIllustration",
        "LocalScaleComparison",
    }

    assert expected <= set(wenu3d.__all__)


def test_advanced_renderer_helpers_are_not_promoted_to_package_root() -> None:
    advanced = {
        "ControlPanel",
        "GridControlPanel",
        "orient_earth_to_observer",
        "realistic_earth",
        "add_observer",
        "tangent_plane",
        "add_arrow",
        "add_tube",
    }

    assert advanced.isdisjoint(wenu3d.__all__)
