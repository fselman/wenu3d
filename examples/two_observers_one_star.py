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
    GridLayer,
    GridStyle,
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
INITIAL_LOCAL_SCALE = 0.20
COMPARISON_LOCAL_SCALES = (0.20, 0.01)
WINDOW_SIZE = (1800, 1200)


scene = CelestialScene(
    latitude_deg=LATITUDE_DEG,
    longitude_deg=LONGITUDE_DEG,
    location_name="La Ligua and Maunakea",
    title="Two observers and one star",
    earth_radius=EARTH_RADIUS,
    axis_visible=False,
    window_size=WINDOW_SIZE,
)

# A restrained equatorial grid supplies surface-orientation cues without
# introducing a decorative texture or a second shell implementation.
equatorial_grid = GridLayer(
    name="equatorial_depth_cue",
    frame=scene.equatorial,
    meridians_deg=tuple(range(0, 360, 30)),
    parallels_deg=tuple(range(-80, 81, 20)),
    major_meridians_deg=(),
    major_parallels_deg=(),
    radius=0.988 * scene.sphere_radius,
    style=GridStyle(
        color="#71869a",
        major_radius=0.0016,
        minor_radius=0.0008,
        major_opacity=0.20,
        minor_opacity=0.10,
    ),
)
scene.add(equatorial_grid)

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
global_controls = scene.add_global_controls()

# Export-mode selection belongs to this example. PyVista radio buttons are
# grouped, so exactly one choice remains active. The default publication mode
# omits the interactive controls; select the other button to retain them.
export_options = {"include_controls": False}


def select_sphere_only() -> None:
    export_options["include_controls"] = False


def select_controls() -> None:
    export_options["include_controls"] = True


export_mode_widgets = (
    scene.plotter.add_radio_button_widget(
        callback=select_sphere_only,
        radio_button_group="png_export_mode",
        value=True,
        title="Sphere only",
        position=(20, 610),
        size=24,
        border_size=4,
        color_on="#506070",
        color_off="#d4d4d4",
        background_color="#f7f6f2",
    ),
    scene.plotter.add_radio_button_widget(
        callback=select_controls,
        radio_button_group="png_export_mode",
        value=False,
        title="Include controls",
        position=(20, 565),
        size=24,
        border_size=4,
        color_on="#506070",
        color_off="#d4d4d4",
        background_color="#f7f6f2",
    ),
)
scene.controls.register_radio_group("png_export_mode")

output_directory = (
    Path(__file__).resolve().parents[1]
    / "outputs"
)
output_directory.mkdir(parents=True, exist_ok=True)

# Choose the first scale and viewport interactively, then close the window.
# Saving without camera or window-size overrides captures the current live
# renderer exactly. Subsequent images change only the local-cartoon scale.
scene.set_local_scale(INITIAL_LOCAL_SCALE, render=False)
scene.show()

# Button widgets and control-panel items use different VTK visibility APIs.
# Hide both radio buttons as well as the managed scene controls when the
# publication-oriented "Sphere only" mode was selected.
controls_are_included = export_options["include_controls"]

def save_numbered(index: int) -> None:
    path = output_directory / f"two_observers_one_star_{index:03d}.png"
    if controls_are_included:
        scene.save(path)
    else:
        scene.save_sphere_frame(path, size=1200, padding=0.035)


save_numbered(1)
for index, scale in enumerate(COMPARISON_LOCAL_SCALES, start=2):
    scene.set_local_scale(scale, render=False)
    save_numbered(index)

scene.close()
