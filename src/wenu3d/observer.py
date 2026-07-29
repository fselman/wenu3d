from __future__ import annotations
import numpy as np
import pyvista as pv

from .geometry import unit
from .rendering import add_tube


def tangent_plane(center, east, north, *, width, depth) -> pv.PolyData:
    e = unit(east)
    n = unit(north)
    hw = width / 2
    hd = depth / 2

    points = np.array([
        center - hw * e - hd * n,
        center + hw * e - hd * n,
        center + hw * e + hd * n,
        center - hw * e + hd * n,
    ])
    return pv.PolyData(points, np.array([4, 0, 1, 2, 3]))


def add_observer(plotter, *, base, zenith, east, height) -> list[pv.Actor]:
    z = unit(zenith)
    e = unit(east)

    feet = base
    hips = feet + 0.38 * height * z
    shoulders = feet + 0.68 * height * z
    neck = feet + 0.78 * height * z
    head = feet + 0.90 * height * z

    left_foot = feet - 0.10 * height * e
    right_foot = feet + 0.10 * height * e
    left_hand = shoulders - 0.20 * height * e
    right_hand = shoulders + 0.20 * height * e

    r = 0.018 * height
    actors = []

    for p0, p1 in (
        (hips, shoulders),
        (hips, left_foot),
        (hips, right_foot),
        (shoulders, left_hand),
        (shoulders, right_hand),
        (shoulders, neck),
    ):
        actors.append(
            add_tube(
                plotter,
                np.vstack([p0, p1]),
                color="#474747",
                radius=r,
            )
        )

    actors.append(
        plotter.add_mesh(
            pv.Sphere(radius=0.09 * height, center=head),
            color="#d4af8a",
            smooth_shading=True,
        )
    )
    return actors
