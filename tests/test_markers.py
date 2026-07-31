import numpy as np
import pytest

from wenu3d import Marker, MarkerStyle


def test_marker_normalizes_renderer_neutral_values() -> None:
    marker = Marker(
        position=np.array([1, 2, 3]),
        style=MarkerStyle(
            shape="star",
            color="  gold  ",
            radius=0.08,
            opacity=0.75,
        ),
        visible=np.bool_(False),
    )

    assert marker.position == (1.0, 2.0, 3.0)
    assert marker.style.shape == "star"
    assert marker.style.color == "gold"
    assert marker.style.radius == 0.08
    assert marker.style.opacity == 0.75
    assert marker.visible is False


def test_marker_defaults_describe_visible_finite_sphere() -> None:
    marker = Marker(position=(0.0, 0.0, 1.0))

    assert marker.style == MarkerStyle()
    assert marker.style.shape == "sphere"
    assert marker.style.radius > 0.0
    assert marker.visible is True


@pytest.mark.parametrize(
    "position",
    [
        (0.0, 1.0),
        (0.0, 1.0, 2.0, 3.0),
        (0.0, np.nan, 1.0),
        (0.0, 1.0, np.inf),
    ],
)
def test_marker_rejects_invalid_position(position) -> None:
    with pytest.raises(ValueError, match="position"):
        Marker(position=position)


@pytest.mark.parametrize("radius", [0.0, -0.1, np.nan, np.inf])
def test_marker_style_rejects_invalid_radius(radius: float) -> None:
    with pytest.raises(ValueError, match="radius"):
        MarkerStyle(radius=radius)


@pytest.mark.parametrize("opacity", [-0.1, 1.1, np.nan, np.inf])
def test_marker_style_rejects_invalid_opacity(opacity: float) -> None:
    with pytest.raises(ValueError, match="opacity"):
        MarkerStyle(opacity=opacity)


@pytest.mark.parametrize("shape", ["point", "", None])
def test_marker_style_rejects_unsupported_shape(shape) -> None:
    with pytest.raises(ValueError, match="shape"):
        MarkerStyle(shape=shape)


@pytest.mark.parametrize("color", ["", "   ", None])
def test_marker_style_rejects_invalid_color(color) -> None:
    with pytest.raises(ValueError, match="color"):
        MarkerStyle(color=color)


def test_marker_rejects_invalid_style_and_visibility() -> None:
    with pytest.raises(TypeError, match="style"):
        Marker(position=(0.0, 0.0, 1.0), style={})

    with pytest.raises(TypeError, match="visible"):
        Marker(position=(0.0, 0.0, 1.0), visible=1)
