import numpy as np
import pytest

from wenu3d.markers import MarkerStyle
from wenu3d.targets import CelestialTarget


def test_target_retains_unit_direction_and_derives_display_position() -> None:
    target = CelestialTarget(
        name="Sirius",
        direction=(0.0, 3.0, 4.0),
        shell_radius=2.5,
    )

    assert target.name == "Sirius"
    assert target.direction == pytest.approx((0.0, 0.6, 0.8))
    assert target.display_position == pytest.approx((0.0, 1.5, 2.0))
    assert np.linalg.norm(target.direction) == pytest.approx(1.0)


def test_shell_radius_changes_display_position_not_direction() -> None:
    target = CelestialTarget(
        name="target",
        direction=(1.0, -2.0, 2.0),
        shell_radius=1.0,
    )

    enlarged = target.at_shell_radius(4.0)

    assert enlarged is not target
    assert enlarged.direction == target.direction
    assert enlarged.shell_radius == 4.0
    assert enlarged.display_position == pytest.approx(
        4.0 * np.asarray(target.direction)
    )
    assert target.shell_radius == 1.0


def test_target_derives_finite_marker_without_conflating_records() -> None:
    style = MarkerStyle(
        shape="star",
        color="gold",
        radius=0.08,
        opacity=0.7,
    )
    target = CelestialTarget(
        name="star",
        direction=(1.0, 0.0, 0.0),
        shell_radius=3.0,
        marker_style=style,
        visible=False,
    )

    marker = target.as_marker()

    assert marker.position == target.display_position
    assert marker.style is style
    assert marker.visible is False
    assert not hasattr(marker, "direction")


@pytest.mark.parametrize(
    "direction",
    [
        (0.0, 0.0, 0.0),
        (1.0, 2.0),
        (1.0, 2.0, 3.0, 4.0),
        (1.0, np.inf, 0.0),
        (1.0, np.nan, 0.0),
    ],
)
def test_target_rejects_invalid_direction(direction) -> None:
    with pytest.raises(ValueError, match="direction"):
        CelestialTarget(name="target", direction=direction)


@pytest.mark.parametrize("shell_radius", [0.0, -1.0, np.inf, np.nan])
def test_target_rejects_invalid_shell_radius(shell_radius: float) -> None:
    with pytest.raises(ValueError, match="shell radius"):
        CelestialTarget(
            name="target",
            direction=(1.0, 0.0, 0.0),
            shell_radius=shell_radius,
        )


@pytest.mark.parametrize("name", ["", "   "])
def test_target_rejects_empty_name(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        CelestialTarget(name=name, direction=(1.0, 0.0, 0.0))


def test_target_validates_marker_style_and_visibility() -> None:
    with pytest.raises(TypeError, match="MarkerStyle"):
        CelestialTarget(
            name="target",
            direction=(1.0, 0.0, 0.0),
            marker_style=object(),
        )
    with pytest.raises(TypeError, match="boolean"):
        CelestialTarget(
            name="target",
            direction=(1.0, 0.0, 0.0),
            visible=1,
        )
