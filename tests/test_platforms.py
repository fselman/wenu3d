from unittest.mock import Mock

import pytest

from wenu3d.platforms import (
    CardinalDirectionsDecoration,
    LocalPlatform,
    PlatformDecoration,
)
from wenu3d.surface_object import SurfaceObject
from wenu3d.surfaces import PlaneSurface
from wenu3d.vector_object import VectorObject
from wenu3d.vectors import VectorArrow


def make_surface() -> SurfaceObject:
    return SurfaceObject(
        name="platform.surface",
        surface=PlaneSurface(
            center=(0.0, 0.0, 0.25),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=0.4,
            height=0.3,
        ),
    )


def make_vectors() -> dict[str, VectorObject]:
    directions = {
        "east": (1.0, 0.0, 0.0),
        "west": (-1.0, 0.0, 0.0),
        "north": (0.0, 1.0, 0.0),
        "south": (0.0, -1.0, 0.0),
    }
    return {
        name: VectorObject(
            name=f"cardinal.{name}",
            vector=VectorArrow(
                start=(0.0, 0.0, 0.25),
                direction=direction,
                scale=0.1,
            ),
        )
        for name, direction in directions.items()
    }


def make_decoration(name: str = "cardinals") -> CardinalDirectionsDecoration:
    return CardinalDirectionsDecoration(name=name, vectors=make_vectors())


def test_cardinal_decoration_preserves_semantic_order_and_lookup() -> None:
    vectors = make_vectors()
    decoration = CardinalDirectionsDecoration(
        name="cardinals",
        vectors=vectors,
    )

    assert decoration.vectors == tuple(vectors.values())
    assert decoration.objects == list(vectors.values())
    assert decoration.get_direction(" NORTH ") is vectors["north"]


def test_cardinal_decoration_validates_directions_and_objects() -> None:
    vectors = make_vectors()
    reordered = {name: vectors[name] for name in ("north", "east", "south", "west")}
    with pytest.raises(ValueError, match="East, West, North, South"):
        CardinalDirectionsDecoration(name="cardinals", vectors=reordered)

    invalid = dict(vectors)
    invalid["south"] = object()
    with pytest.raises(TypeError, match="VectorObjects"):
        CardinalDirectionsDecoration(name="cardinals", vectors=invalid)


def test_local_platform_owns_surface_and_decoration() -> None:
    surface = make_surface()
    decoration = make_decoration()
    platform = LocalPlatform(
        name="platform",
        surface=surface,
        decoration=decoration,
    )

    assert platform.surface is surface
    assert platform.decoration is decoration
    assert platform.objects == [surface, decoration]


def test_local_platform_validates_components() -> None:
    with pytest.raises(TypeError, match="SurfaceObject"):
        LocalPlatform(name="platform", surface=object())
    with pytest.raises(TypeError, match="PlatformDecoration"):
        LocalPlatform(
            name="platform",
            surface=make_surface(),
            decoration=object(),
        )


def test_attached_platform_replaces_and_removes_decoration() -> None:
    surface = make_surface()
    first = make_decoration("first")
    first_vector = first.vectors[0]
    first_actor = Mock()
    first_vector.actors.append(first_actor)
    second = PlatformDecoration(name="second")
    platform = LocalPlatform(
        name="platform",
        surface=surface,
        decoration=first,
    )
    plotter = Mock()
    platform._plotter = plotter
    first._plotter = plotter
    first_vector._plotter = plotter

    platform.set_decoration(second)

    assert platform.decoration is second
    assert platform.objects == [surface, second]
    plotter.remove_actor.assert_called_once_with(first_actor, render=False)
    plotter.render.assert_called_once_with()

    platform.set_decoration(None)
    assert platform.decoration is None
    assert platform.objects == [surface]
