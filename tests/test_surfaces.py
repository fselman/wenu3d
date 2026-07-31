import numpy as np
import pytest

from wenu3d import PlaneSurface, SurfaceStyle


def test_plane_surface_normalizes_renderer_neutral_values() -> None:
    center = np.array((1, 2, 3))
    plane = PlaneSurface(
        center=center,
        normal=(0.0, 0.0, 2.0),
        axis_u=(3.0, 0.0, 1.0),
        width=4,
        height=2,
        style=SurfaceStyle(
            color="  silver  ",
            opacity=0.35,
            show_edges=np.bool_(False),
            edge_color="  charcoal  ",
            edge_width=3,
        ),
        visible=np.bool_(False),
    )
    center[:] = 0

    assert plane.center == (1.0, 2.0, 3.0)
    assert plane.normal == (0.0, 0.0, 1.0)
    assert plane.axis_u == (1.0, 0.0, 0.0)
    assert plane.axis_v == (0.0, 1.0, 0.0)
    assert plane.width == 4.0
    assert plane.height == 2.0
    assert plane.area == 8.0
    assert plane.style.color == "silver"
    assert plane.style.opacity == 0.35
    assert plane.style.show_edges is False
    assert plane.style.edge_color == "charcoal"
    assert plane.style.edge_width == 3.0
    assert plane.visible is False


def test_plane_corners_follow_right_handed_local_frame() -> None:
    plane = PlaneSurface(
        center=(1.0, 2.0, 3.0),
        normal=(0.0, 0.0, 1.0),
        axis_u=(1.0, 0.0, 0.0),
        width=4.0,
        height=2.0,
    )

    corners = plane.corners()

    np.testing.assert_allclose(
        corners,
        (
            (-1.0, 1.0, 3.0),
            (3.0, 1.0, 3.0),
            (3.0, 3.0, 3.0),
            (-1.0, 3.0, 3.0),
        ),
        atol=1e-12,
    )
    np.testing.assert_allclose(corners.mean(axis=0), plane.center, atol=1e-12)
    np.testing.assert_allclose(
        np.cross(corners[1] - corners[0], corners[3] - corners[0]),
        plane.area * np.asarray(plane.normal),
        atol=1e-12,
    )
    assert plane.face == (0, 1, 2, 3)


def test_plane_orthogonalizes_in_plane_axis() -> None:
    plane = PlaneSurface(
        center=(0.0, 0.0, 0.0),
        normal=(1.0, 1.0, 1.0),
        axis_u=(1.0, -1.0, 0.5),
        width=3.0,
        height=2.0,
    )

    basis = np.asarray((plane.axis_u, plane.axis_v, plane.normal))

    np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(
        np.cross(plane.axis_u, plane.axis_v),
        plane.normal,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        (plane.corners() - plane.center) @ plane.normal,
        0.0,
        atol=1e-12,
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("center", (0.0, 1.0)),
        ("center", (0.0, np.nan, 1.0)),
        ("normal", (0.0, 0.0)),
        ("normal", (0.0, 0.0, 0.0)),
        ("normal", (0.0, np.inf, 1.0)),
        ("axis_u", (1.0, 0.0)),
        ("axis_u", (0.0, 0.0, 0.0)),
        ("axis_u", (0.0, np.nan, 1.0)),
        ("axis_u", (0.0, 0.0, 2.0)),
    ],
)
def test_plane_surface_rejects_invalid_vectors(field_name, value) -> None:
    arguments = {
        "center": (0.0, 0.0, 0.0),
        "normal": (0.0, 0.0, 1.0),
        "axis_u": (1.0, 0.0, 0.0),
        "width": 2.0,
        "height": 1.0,
    }
    arguments[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        PlaneSurface(**arguments)


@pytest.mark.parametrize("width", [0.0, -1.0, np.nan, np.inf])
def test_plane_surface_rejects_invalid_width(width: float) -> None:
    with pytest.raises(ValueError, match="width"):
        PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=width,
            height=1.0,
        )


@pytest.mark.parametrize("height", [0.0, -1.0, np.nan, np.inf])
def test_plane_surface_rejects_invalid_height(height: float) -> None:
    with pytest.raises(ValueError, match="height"):
        PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=1.0,
            height=height,
        )


def test_plane_surface_rejects_dimensions_with_overflowing_area() -> None:
    with pytest.raises(ValueError, match="finite area"):
        PlaneSurface(
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            axis_u=(1.0, 0.0, 0.0),
            width=1e308,
            height=1e308,
        )


@pytest.mark.parametrize("opacity", [-0.1, 1.1, np.nan, np.inf])
def test_surface_style_rejects_invalid_opacity(opacity: float) -> None:
    with pytest.raises(ValueError, match="opacity"):
        SurfaceStyle(opacity=opacity)


@pytest.mark.parametrize("edge_width", [0.0, -1.0, np.nan, np.inf])
def test_surface_style_rejects_invalid_edge_width(edge_width: float) -> None:
    with pytest.raises(ValueError, match="edge width"):
        SurfaceStyle(edge_width=edge_width)


@pytest.mark.parametrize("field_name", ["color", "edge_color"])
@pytest.mark.parametrize("value", ["", "   ", None])
def test_surface_style_rejects_invalid_colors(field_name, value) -> None:
    arguments = {field_name: value}
    with pytest.raises(ValueError, match="color"):
        SurfaceStyle(**arguments)


def test_surface_records_reject_invalid_style_and_visibility() -> None:
    arguments = {
        "center": (0.0, 0.0, 0.0),
        "normal": (0.0, 0.0, 1.0),
        "axis_u": (1.0, 0.0, 0.0),
        "width": 2.0,
        "height": 1.0,
    }

    with pytest.raises(TypeError, match="style"):
        PlaneSurface(**arguments, style={})

    with pytest.raises(TypeError, match="visible"):
        PlaneSurface(**arguments, visible=1)

    with pytest.raises(TypeError, match="show_edges"):
        SurfaceStyle(show_edges=1)
