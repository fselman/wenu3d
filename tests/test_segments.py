import numpy as np
import pytest

from wenu3d import LineSegment, SegmentStyle, SightLine


def test_line_segment_normalizes_renderer_neutral_values() -> None:
    segment = LineSegment(
        start=np.array((1, 2, 3)),
        end=[4, 6, 3],
        style=SegmentStyle(
            color="  navy  ",
            width=4,
            opacity=0.6,
        ),
        visible=np.bool_(False),
    )

    assert segment.start == (1.0, 2.0, 3.0)
    assert segment.end == (4.0, 6.0, 3.0)
    assert segment.style.color == "navy"
    assert segment.style.width == 4.0
    assert segment.style.opacity == 0.6
    assert segment.visible is False
    assert segment.length == 5.0
    assert segment.direction == pytest.approx((0.6, 0.8, 0.0))


def test_sight_line_names_scientific_endpoint_roles() -> None:
    sight_line = SightLine(
        observer_position=(0.0, 1.0, 0.0),
        target_position=(0.0, 1.0, 3.0),
    )

    assert sight_line.start == sight_line.observer_position
    assert sight_line.end == sight_line.target_position
    assert sight_line.length == 3.0
    assert sight_line.direction == (0.0, 0.0, 1.0)


def test_two_sight_lines_can_share_one_finite_target() -> None:
    target = (0.5, -0.25, 10.0)
    first = SightLine(
        observer_position=(-1.0, 0.0, 0.0),
        target_position=target,
    )
    second = SightLine(
        observer_position=(1.0, 0.0, 0.0),
        target_position=target,
    )

    assert first.target_position == second.target_position == target
    assert first.observer_position != second.observer_position


@pytest.mark.parametrize(
    ("start", "end", "match"),
    [
        ((0.0, 1.0), (1.0, 0.0, 0.0), "start"),
        ((0.0, 0.0, 0.0), (1.0, 0.0), "end"),
        ((0.0, np.nan, 0.0), (1.0, 0.0, 0.0), "start"),
        ((0.0, 0.0, 0.0), (1.0, np.inf, 0.0), "end"),
        ((1.0, 2.0, 3.0), (1.0, 2.0, 3.0), "separation"),
        ((-1e308, 0.0, 0.0), (1e308, 0.0, 0.0), "separation"),
    ],
)
def test_line_segment_rejects_invalid_endpoints(start, end, match) -> None:
    with pytest.raises(ValueError, match=match):
        LineSegment(start=start, end=end)


def test_sight_line_rejects_coincident_observer_and_target() -> None:
    with pytest.raises(ValueError, match="separation"):
        SightLine(
            observer_position=(1.0, 2.0, 3.0),
            target_position=(1.0, 2.0, 3.0),
        )


@pytest.mark.parametrize("width", [0.0, -1.0, np.nan, np.inf])
def test_segment_style_rejects_invalid_width(width: float) -> None:
    with pytest.raises(ValueError, match="width"):
        SegmentStyle(width=width)


@pytest.mark.parametrize("opacity", [-0.1, 1.1, np.nan, np.inf])
def test_segment_style_rejects_invalid_opacity(opacity: float) -> None:
    with pytest.raises(ValueError, match="opacity"):
        SegmentStyle(opacity=opacity)


@pytest.mark.parametrize("color", ["", "   ", None])
def test_segment_style_rejects_invalid_color(color) -> None:
    with pytest.raises(ValueError, match="color"):
        SegmentStyle(color=color)


@pytest.mark.parametrize("record_type", [LineSegment, SightLine])
def test_segment_records_reject_invalid_style_and_visibility(record_type) -> None:
    endpoint_names = (
        {"start": (0.0, 0.0, 0.0), "end": (1.0, 0.0, 0.0)}
        if record_type is LineSegment
        else {
            "observer_position": (0.0, 0.0, 0.0),
            "target_position": (1.0, 0.0, 0.0),
        }
    )

    with pytest.raises(TypeError, match="style"):
        record_type(**endpoint_names, style={})

    with pytest.raises(TypeError, match="visible"):
        record_type(**endpoint_names, visible=1)
