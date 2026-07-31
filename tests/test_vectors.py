from unittest.mock import Mock, patch

import numpy as np
import pytest

from wenu3d import VectorArrow, VectorObject, VectorStyle


def test_vector_arrow_normalizes_direction_and_preserves_geometry() -> None:
    vector = VectorArrow(
        start=(1.0, 2.0, 3.0),
        direction=(0.0, 4.0, 0.0),
        scale=0.07,
    )

    assert vector.start == (1.0, 2.0, 3.0)
    assert vector.direction == (0.0, 1.0, 0.0)
    assert vector.scale == 0.07


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("start", (1.0, 2.0), "start"),
        ("start", (1.0, np.nan, 3.0), "start"),
        ("direction", (0.0, 0.0, 0.0), "zero vector"),
        ("direction", (0.0, np.inf, 0.0), "direction"),
        ("scale", 0.0, "scale"),
        ("scale", -1.0, "scale"),
        ("scale", np.nan, "scale"),
    ],
)
def test_vector_arrow_rejects_invalid_geometry(field, value, message) -> None:
    arguments = {
        "start": (0.0, 0.0, 0.0),
        "direction": (1.0, 0.0, 0.0),
        "scale": 1.0,
    }
    arguments[field] = value
    with pytest.raises(ValueError, match=message):
        VectorArrow(**arguments)


@pytest.mark.parametrize("opacity", [-0.1, 1.1, np.inf, np.nan])
def test_vector_style_rejects_invalid_opacity(opacity: float) -> None:
    with pytest.raises(ValueError, match="opacity"):
        VectorStyle(opacity=opacity)


def test_vector_object_build_uses_existing_solid_arrow_renderer() -> None:
    plotter = Mock()
    actor = Mock()
    vector = VectorArrow(
        start=(0.0, 0.0, 0.262),
        direction=(2.0, 0.0, 0.0),
        scale=0.07,
        style=VectorStyle(color="#59645d", opacity=0.8),
    )
    obj = VectorObject(name="east", vector=vector)

    with patch("wenu3d.vector_object.add_arrow", return_value=actor) as add_arrow:
        obj.build(plotter)

    add_arrow.assert_called_once()
    arguments = add_arrow.call_args
    assert arguments.args[0] is plotter
    np.testing.assert_allclose(arguments.args[1], vector.start)
    np.testing.assert_allclose(arguments.args[2], vector.direction)
    assert arguments.kwargs == {"scale": 0.07, "color": "#59645d"}
    assert obj.actors == [actor]
    actor.GetProperty.return_value.SetOpacity.assert_called_with(0.8)


def test_vector_object_rebuild_and_detach_do_not_accumulate_actors() -> None:
    plotter = Mock()
    first = Mock()
    second = Mock()
    obj = VectorObject(
        name="north",
        vector=VectorArrow(
            start=(0.0, 0.0, 0.262),
            direction=(0.0, 1.0, 0.0),
            scale=0.07,
        ),
    )

    with patch(
        "wenu3d.vector_object.add_arrow",
        side_effect=[first, second],
    ):
        obj.build(plotter)
        obj.build(plotter)

    plotter.remove_actor.assert_called_once_with(first, render=False)
    assert obj.actors == [second]

    obj.detach(render=False)
    assert plotter.remove_actor.call_count == 2
    assert obj.actors == []
    assert obj.attached_plotter is None


def test_vector_object_requires_vector_record() -> None:
    with pytest.raises(TypeError, match="VectorArrow"):
        VectorObject(name="invalid", vector=None)
