from pathlib import Path

from wenu3d import CelestialScene, SceneStyle


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    earth_radius=0.25,
    style=SceneStyle(),
    window_size=(1800, 1200),
)

meridians = (
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
)

parallels = (-60, -30, 0, 30, 60)

horizontal = scene.make_horizontal_grid(
    meridians_deg=meridians,
    parallels_deg=parallels,
)
scene.add(horizontal)

equatorial = scene.make_equatorial_grid(
    meridians_deg=meridians,
    parallels_deg=parallels,
)
scene.add(equatorial)

# Both panels remain on the left. Each panel is vertical internally.
scene.add_grid_controls(
    horizontal,
    origin_x=20,
    origin_y=960,
)

scene.add_grid_controls(
    equatorial,
    origin_x=175,
    origin_y=960,
)

scene.add_global_controls()

output = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "la_ligua_interactive.png"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

scene.show(
    screenshot=str(output),
)
