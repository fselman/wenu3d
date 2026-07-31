import numpy as np
import pytest

from wenu3d import CurveStyle, SampledCurve


def test_sampled_curve_normalizes_renderer_neutral_values() -> None:
    source = np.array(
        [
            (1, 0, 0),
            (1, 1, 0),
            (0, 1, 0),
        ]
    )
    curve = SampledCurve(
        points=source,
        style=CurveStyle(
            color="  navy  ",
            width=6,
            opacity=0.7,
            arrowheads="end",
            arrow_size=0.08,
        ),
        visible=np.bool_(False),
    )
    source[:] = 0

    assert curve.points == (
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    )
    assert curve.style.color == "navy"
    assert curve.style.width == 6.0
    assert curve.style.opacity == 0.7
    assert curve.style.arrowheads == "end"
    assert curve.style.arrow_size == 0.08
    assert curve.visible is False


def test_sampled_curve_returns_independent_array() -> None:
    curve = SampledCurve(
        points=((0.0, 0.0, 0.0), (1.0, 2.0, 3.0)),
    )

    points = curve.as_array()
    points[:] = 0.0

    assert curve.points[1] == (1.0, 2.0, 3.0)


def test_sampled_curve_allows_repeated_endpoint_for_closed_curve() -> None:
    curve = SampledCurve(
        points=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (-1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
        )
    )

    assert curve.points[0] == curve.points[-1]


@pytest.mark.parametrize(
    ("points", "match"),
    [
        ((), "shape"),
        (((0.0, 0.0, 0.0),), "shape"),
        (((0.0, 0.0), (1.0, 0.0)), "shape"),
        (
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
            "rectangular",
        ),
        (((0.0, 0.0, 0.0), (np.nan, 1.0, 0.0)), "finite"),
        (((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), "non-zero"),
        (
            ((-1e308, 0.0, 0.0), (1e308, 0.0, 0.0)),
            "finite",
        ),
    ],
)
def test_sampled_curve_rejects_invalid_points(points, match) -> None:
    with pytest.raises(ValueError, match=match):
        SampledCurve(points=points)


@pytest.mark.parametrize("width", [0.0, -1.0, np.nan, np.inf])
def test_curve_style_rejects_invalid_width(width: float) -> None:
    with pytest.raises(ValueError, match="width"):
        CurveStyle(width=width)


@pytest.mark.parametrize("opacity", [-0.1, 1.1, np.nan, np.inf])
def test_curve_style_rejects_invalid_opacity(opacity: float) -> None:
    with pytest.raises(ValueError, match="opacity"):
        CurveStyle(opacity=opacity)


@pytest.mark.parametrize("arrow_size", [0.0, -1.0, np.nan, np.inf])
def test_curve_style_rejects_invalid_arrow_size(arrow_size: float) -> None:
    with pytest.raises(ValueError, match="arrow size"):
        CurveStyle(arrow_size=arrow_size)


@pytest.mark.parametrize("color", ["", "   ", None])
def test_curve_style_rejects_invalid_color(color) -> None:
    with pytest.raises(ValueError, match="color"):
        CurveStyle(color=color)


@pytest.mark.parametrize("arrowheads", ["head", "all", "", None])
def test_curve_style_rejects_invalid_arrowheads(arrowheads) -> None:
    with pytest.raises(ValueError, match="arrowheads"):
        CurveStyle(arrowheads=arrowheads)


def test_sampled_curve_rejects_invalid_style_and_visibility() -> None:
    points = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))

    with pytest.raises(TypeError, match="style"):
        SampledCurve(points=points, style={})

    with pytest.raises(TypeError, match="visible"):
        SampledCurve(points=points, visible=1)
