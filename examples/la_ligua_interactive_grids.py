from pathlib import Path

from wenu3d import (
    Annotation,
    AnnotationLayer,
    AnnotationStyle,
    CelestialScene,
    SceneStyle,
)


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

parallels = (
    -60,
    -30,
    0,
    30,
    60,
)

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

horizontal_labels = horizontal.make_label_layer(
    meridian_anchors={
        0: 8,
        90: 8,
        180: 8,
        270: 8,
    },
    annotation_style=AnnotationStyle(
        color=scene.style.horizontal_grid_color,
        font_size=13,
        bold=True,
    ),
)
scene.add(horizontal_labels)

scientific_callouts = AnnotationLayer(name="scientific_callouts")
south_celestial_pole = -scene.equatorial.pole
scientific_callouts.add_annotation(
    "scientific_callouts.south_celestial_pole",
    Annotation(
        text="South celestial pole",
        anchor=scene.sphere_radius * south_celestial_pole,
        offset=0.055 * south_celestial_pole,
        style=AnnotationStyle(
            color=scene.style.text_color,
            font_size=16,
            bold=True,
        ),
    ),
)
scene.add(scientific_callouts)

# Both panels are on the left and remain visually separate.
scene.add_grid_controls(
    horizontal,
    origin_x=20,
    origin_y=990,
)

scene.add_grid_controls(
    equatorial,
    origin_x=180,
    origin_y=990,
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
