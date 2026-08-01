from unittest.mock import Mock, patch

import numpy as np
import pytest

from wenu3d.axis import CelestialAxisObject


def test_axis_normalizes_direction_and_exposes_symmetric_points() -> None:
    axis = CelestialAxisObject(
        name="axis",
        direction=(0.0, 0.0, 2.0),
        half_length=1.25,
    )

    np.testing.assert_allclose(axis.direction, [0.0, 0.0, 1.0])
    np.testing.assert_allclose(axis.points[0], [0.0, 0.0, -1.25])
    np.testing.assert_allclose(axis.points[1], [0.0, 0.0, 1.25])


def test_axis_builds_owned_tube_with_explicit_style() -> None:
    plotter = Mock()
    actor = Mock()
    actor.GetProperty.return_value = Mock()
    axis = CelestialAxisObject(
        name="axis",
        direction=(1.0, 0.0, 0.0),
        half_length=1.1,
        tube_radius=0.004,
        color="#123456",
        opacity=0.4,
        visible=False,
    )

    with patch("wenu3d.axis.add_tube", return_value=actor) as add_tube:
        axis.build(plotter)

    add_tube.assert_called_once()
    call = add_tube.call_args
    assert call.args[0] is plotter
    np.testing.assert_allclose(call.args[1], [[-1.1, 0.0, 0.0], [1.1, 0.0, 0.0]])
    assert call.kwargs == {
        "color": "#123456",
        "radius": 0.004,
        "opacity": 0.4,
        "name": "axis",
    }
    assert axis.actors == [actor]
    actor.SetVisibility.assert_called_with(False)
    actor.GetProperty.return_value.SetOpacity.assert_called_with(0.4)


@pytest.mark.parametrize(
    "arguments",
    [
        {"direction": (0.0, 0.0, 0.0)},
        {"direction": (1.0, 2.0)},
        {"half_length": 0.0},
        {"tube_radius": 0.0},
        {"color": ""},
        {"opacity": -0.1},
        {"opacity": 1.1},
    ],
)
def test_axis_rejects_invalid_geometry_and_style(arguments) -> None:
    with pytest.raises(ValueError):
        CelestialAxisObject(name="axis", **arguments)
