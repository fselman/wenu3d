"""Show one celestial direction from two finite observer positions.

The gold marker is a displayed position on the celestial shell.  The gray
line from the origin represents the abstract celestial direction.  The two
red lines are finite sight lines from observer eye anchors to that same
displayed marker; they are illustrative and do not assign a physical distance
to the star.
"""

from pathlib import Path

from wenu3d import (
    CelestialScene,
    CelestialTarget,
    MarkerStyle,
    Observer,
    ObserverComposition,
    SegmentStyle,
    StickFigureRepresentation,
    TargetLineIllustration,
)


LATITUDE_DEG = -32.4524
LONGITUDE_DEG = -71.2311
EARTH_RADIUS = 0.25


scene = CelestialScene(
    latitude_deg=LATITUDE_DEG,
    longitude_deg=LONGITUDE_DEG,
    location_name="La Ligua and Maunakea",
    title="Two observers and one star",
    earth_radius=EARTH_RADIUS,
    window_size=(1800, 1200),
)

# The scene already contains the canonical La Ligua observer.  Add a second
# observer at the Maunakea observatory site.  The large geographic separation
# makes the finite illustrative baseline conspicuous.
second_geographic_observer = Observer.at_geographic_site(
    "maunakea",
    latitude_deg=19.8236,
    longitude_deg=-155.4708,
    earth_radius=EARTH_RADIUS,
)
second_observer = scene.earth.display_observer(second_geographic_observer)
second_representation = StickFigureRepresentation(
    name="maunakea.stick_figure",
    observer=second_observer,
    height=0.92 * EARTH_RADIUS,
    body_color="#304f73",
    head_color="#d4af8a",
)
second_composition = ObserverComposition(
    name="maunakea.composition",
    observer=second_observer,
    representation=second_representation,
)
scene.local_cartoon.add_observer(second_composition)

# CelestialTarget keeps the scientific unit direction separate from the
# finite marker position derived at the shell radius.
star = CelestialTarget(
    name="illustrative_star",
    direction=(
        scene.observer.frame.pole
        + second_observer.frame.pole
    ),
    shell_radius=scene.sphere_radius,
    marker_style=MarkerStyle(
        shape="star",
        color="#f2c14e",
        radius=0.055,
    ),
)

lines = TargetLineIllustration(
    name="two_observers_one_star",
    target=star,
    local_cartoon=scene.local_cartoon,
    observer_anchors={
        scene.observer.name: "eye",
        second_observer.name: "eye",
    },
    include_centered_direction=True,
    direction_style=SegmentStyle(
        color="#4b4b4b",
        width=4.0,
        opacity=0.95,
    ),
    sight_line_style=SegmentStyle(
        color="#b5483a",
        width=3.0,
        opacity=0.90,
    ),
)
scene.add(lines)

# The standard local-scale control now refreshes transform-dependent finite
# sight lines while leaving the star and centered direction line fixed.
scene.add_global_controls()

output = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "two_observers_one_star.png"
)
output.parent.mkdir(parents=True, exist_ok=True)

scene.show(screenshot=str(output))
scene.close()
