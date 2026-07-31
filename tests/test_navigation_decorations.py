import numpy as np
import pytest

from wenu3d.platforms import (
    CompassRoseDecoration,
    NainoaThompsonStarCompassDecoration,
    PlatformDecoration,
)


def make_decoration(cls, *, radius=0.2):
    return cls(
        name="navigation",
        center=(0.0, 0.0, 0.25),
        east=(2.0, 0.0, 0.0),
        north=(0.2, 3.0, 0.0),
        radius=radius,
    )


def test_compass_rose_has_sixteen_validated_directions() -> None:
    decoration = make_decoration(CompassRoseDecoration)

    assert isinstance(decoration, PlatformDecoration)
    assert tuple(decoration.lines) == CompassRoseDecoration.direction_labels
    assert len(decoration.objects) == 32
    assert decoration.bearings_deg["N"] == 0.0
    assert decoration.bearings_deg["E"] == 90.0
    assert decoration.bearings_deg["S"] == 180.0
    assert decoration.bearings_deg["W"] == 270.0
    np.testing.assert_allclose(
        decoration.lines["E"].segment.end,
        [0.2, 0.0, 0.25],
        atol=1e-12,
    )


def test_hawaiian_star_compass_has_32_equidistant_houses() -> None:
    decoration = make_decoration(NainoaThompsonStarCompassDecoration)

    assert isinstance(decoration, PlatformDecoration)
    assert len(decoration.lines) == 32
    assert len(decoration.inscriptions) == 32
    assert len(decoration.objects) == 64
    bearings = np.asarray(tuple(decoration.bearings_deg.values()))
    np.testing.assert_allclose(np.diff(bearings), 11.25)
    assert decoration.bearings_deg["ʻĀkau"] == 0.0
    assert decoration.bearings_deg["Hikina"] == 90.0
    assert decoration.bearings_deg["Hema"] == 180.0
    assert decoration.bearings_deg["Komohana"] == 270.0


def test_hawaiian_house_names_follow_quadrant_sequence() -> None:
    labels = NainoaThompsonStarCompassDecoration.direction_labels

    assert labels[1:8] == (
        "Haka Koʻolau", "Nā Leo Koʻolau", "Nālani Koʻolau",
        "Manu Koʻolau", "Noio Koʻolau", "ʻĀina Koʻolau", "Lā Koʻolau",
    )
    assert labels[25:32] == (
        "Lā Hoʻolua", "ʻĀina Hoʻolua", "Noio Hoʻolua", "Manu Hoʻolua",
        "Nālani Hoʻolua", "Nā Leo Hoʻolua", "Haka Hoʻolua",
    )


@pytest.mark.parametrize("radius", [0.0, -1.0, np.nan, np.inf])
def test_radial_decorations_reject_invalid_radius(radius) -> None:
    with pytest.raises(ValueError, match="radius"):
        make_decoration(CompassRoseDecoration, radius=radius)


@pytest.mark.parametrize(
    ("east", "north", "message"),
    [
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), "east"),
        ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0), "north"),
    ],
)
def test_radial_decorations_reject_invalid_platform_frame(
    east,
    north,
    message,
) -> None:
    with pytest.raises(ValueError, match=message):
        CompassRoseDecoration(
            name="navigation",
            center=(0.0, 0.0, 0.0),
            east=east,
            north=north,
            radius=0.2,
        )
