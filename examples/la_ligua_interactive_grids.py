from pathlib import Path

from wenu3d import CelestialScene, SceneStyle


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    earth_radius=0.25,
    style=SceneStyle(),
)

horizontal = scene.make_horizontal_grid(
    meridians_deg=(
        0,
        30,
        60,
        90,
        120,
        150,
        180,
        210,
        240,
        270,
        300,
        330,
    ),
    parallels_deg=(-60, -30, 0, 30, 60),
)
scene.add(horizontal)

equatorial = scene.make_equatorial_grid(
    meridians_deg=(
        0,
        30,
        60,
        90,
        120,
        150,
        180,
        210,
        240,
        270,
        300,
        330,
    ),
    parallels_deg=(-60, -30, 0, 30, 60),
)
scene.add(equatorial)

# The panel controls one chosen grid.
# Replace horizontal with equatorial to control the other grid.
scene.add_grid_controls(
    horizontal,
    origin_x=20,
    origin_y=930,
)

scene.add_global_controls()

output = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "la_ligua_interactive.png"
)

output.parent.mkdir(parents=True, exist_ok=True)
scene.show(screenshot=str(output))
