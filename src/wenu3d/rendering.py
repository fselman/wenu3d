from __future__ import annotations
import numpy as np
import pyvista as pv
from .geometry import unit


def add_tube(plotter, points, *, color, radius, opacity=1.0, name=None):
    line = pv.lines_from_points(np.asarray(points), close=False)
    tube = line.tube(radius=radius)
    return plotter.add_mesh(
        tube,
        color=color,
        opacity=opacity,
        smooth_shading=True,
        name=name,
    )


def add_arrow(plotter, start, direction, *, scale, color):
    arrow = pv.Arrow(
        start=np.asarray(start, dtype=float),
        direction=unit(direction),
        scale=scale,
        tip_length=0.28,
        tip_radius=0.10,
        shaft_radius=0.025,
    )
    return plotter.add_mesh(arrow, color=color, smooth_shading=True)
