from pathlib import Path
from wenu3d import CelestialScene, SceneStyle


style = SceneStyle(
    sphere_back_opacity=0.14,
    sphere_front_opacity=0.035,
    sphere_specular=0.18,
    sphere_specular_power=55,
)

scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    earth_radius=0.25,
    style=style,
    initial_label_size=16,
)

# Every grid independently selects:
# 1. which curves are drawn
# 2. which of those curves receive labels
scene.add_horizontal_grid(
    meridians_deg=(0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330),
    parallels_deg=(-60, -30, 0, 30, 60),
    labeled_meridians_deg=(0, 90, 180, 270),
    labeled_parallels_deg=(-60, -30, 0, 30, 60),
)

scene.add_equatorial_grid(
    meridians_deg=(0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330),
    parallels_deg=(-60, -30, 0, 30, 60),
    labeled_meridians_deg=(0, 90, 180, 270),
    labeled_parallels_deg=(-60, -30, 0, 30, 60),
)

# Comment out scene.add_equatorial_grid(...) to omit it entirely.
scene.add_controls()

output = Path(__file__).resolve().parents[1] / "outputs" / "la_ligua_grids.png"
scene.show(screenshot=str(output))
