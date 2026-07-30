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

horizontal.style.label_format = "{value:g}°"
horizontal_labels = horizontal.make_label_layer(
    meridian_anchors={
        0: 8,
        90: 8,
        180: 8,
        270: 8,
    },
    annotation_style=AnnotationStyle(
        color=scene.style.horizontal_grid_color,
        font_size=18,
        bold=True,
    ),
)
scene.add(horizontal_labels)

scientific_callouts = AnnotationLayer(name="scientific_callouts")
south_celestial_pole = -scene.equatorial.pole
scientific_callouts.add_annotation(
    "scientific_callouts.south_celestial_pole",
    Annotation(
        text="Polo sur celeste",
        anchor=scene.sphere_radius * south_celestial_pole,
        offset=0.055 * south_celestial_pole,
        style=AnnotationStyle(
            color=scene.style.text_color,
            font_size=22,
            bold=True,
        ),
    ),
)
scene.add(scientific_callouts)


def set_annotation_visibility(visible: bool) -> None:
    horizontal_labels.set_visible(visible, render=False)
    scientific_callouts.set_visible(visible, render=False)
    scene.plotter.render()


def set_annotation_size(scale: float) -> None:
    horizontal_labels.set_font_size_scale(scale, render=False)
    scientific_callouts.set_font_size_scale(scale, render=False)
    scene.plotter.render()


# M4 uses explicit widget positions. M5 will replace these with managed layout.
scene.plotter.add_checkbox_button_widget(
    callback=set_annotation_visibility,
    value=True,
    position=(360, 990),
    size=22,
    border_size=2,
    color_on=scene.style.horizontal_grid_color,
    color_off="#d4d4d4",
    background_color="#f7f6f2",
)
scene.plotter.add_text(
    "Mostrar anotaciones",
    position=(389, 990),
    font_size=11,
    color=scene.style.text_color,
)
scene.plotter.add_slider_widget(
    callback=set_annotation_size,
    rng=(0.75, 2.50),
    value=1.0,
    title="Tamaño de anotaciones",
    pointa=(0.62, 0.92),
    pointb=(0.92, 0.92),
    style="modern",
    fmt="%.2f x",
)

scene.add_grid_controls(horizontal)
scene.add_grid_controls(equatorial)

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
