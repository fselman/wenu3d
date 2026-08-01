"""Vista AltAz con acimut y altura rotulados en español."""

from pathlib import Path

from wenu3d import (
    AnnotationStyle,
    CelestialScene,
    CelestialTarget,
    CurveStyle,
    HorizontalCoordinateIllustration,
    HorizontalLabels,
    HorizontalReferenceIllustration,
    IllustrationLayer,
    LineSegment,
    MarkerStyle,
    SegmentStyle,
    TargetLineIllustration,
)


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    title="Coordenadas horizontales: acimut y altura",
    axis_visible=False,
    window_size=(1600, 1150),
)

# Put the observer's base and finite tangent platform in the centered ideal
# horizon plane. The local cartoon moves as a unit, so Earth is lowered while
# its observer, platform, and cardinal context remain mutually consistent.
scene.local_cartoon.set_observer_anchor_height(
    observer=scene.observer.name,
    anchor="feet",
    axis=scene.horizontal.pole,
    height=0.0,
    render=False,
)

labels = HorizontalLabels(
    north="N",
    east="E",
    south="S",
    west="O",
    zenith="Cenit",
    altitude="Altura",
    azimuth="Acimut",
)

# The geometric horizon and the local platform use the same horizontal frame.
# They therefore share Zenith as their normal even though the finite platform
# is displayed tangent to Earth and the geometric horizon is centered on the
# celestial sphere.
references = HorizontalReferenceIllustration(
    name="referencias_horizontales",
    frame=scene.horizontal,
    radius=0.986 * scene.sphere_radius,
    labels=labels,
    horizon_style=CurveStyle(
        color="#344f63",
        width=2.0,
        opacity=0.62,
    ),
    meridian_style=CurveStyle(
        color="#526878",
        width=1.5,
        opacity=0.42,
    ),
    annotation_style=AnnotationStyle(
        color="#203746",
        font_size=17,
        bold=True,
    ),
)
scene.add(references)

star = CelestialTarget(
    name="estrella_NE",
    direction=scene.horizontal.point(45.0, 30.0),
    shell_radius=0.982 * scene.sphere_radius,
    marker_style=MarkerStyle(
        shape="star",
        color="#e7b83d",
        radius=0.05,
    ),
)

coordinates = HorizontalCoordinateIllustration(
    name="coordenadas_estrella",
    target=star,
    frame=scene.horizontal,
    labels=labels,
    angle_decimals=0,
    show_vertical_circle=True,
    vertical_circle_style=CurveStyle(
        color="#697b88",
        width=1.0,
        opacity=0.22,
    ),
    altitude_style=CurveStyle(
        color="#2f70ad",
        width=4.5,
        opacity=0.95,
        arrowheads="end",
    ),
    azimuth_style=CurveStyle(
        color="#4d8558",
        width=4.5,
        opacity=0.95,
        arrowheads="end",
    ),
    annotation_style=AnnotationStyle(
        color="#172c3a",
        font_size=16,
        bold=True,
    ),
)
scene.add(coordinates)

# The ideal sight line is the renderer-neutral celestial direction from the
# center of the sphere. The target marker is already owned by the coordinate
# illustration, so this composition draws only the line.
ideal_sight_line = TargetLineIllustration(
    name="direccion_ideal",
    target=star,
    include_marker=False,
    include_centered_direction=True,
    direction_style=SegmentStyle(
        color="#3f474d",
        width=2.5,
        opacity=0.68,
        tube_radius=0.0035,
    ),
)
scene.add(ideal_sight_line)

# Renderer-neutral axes in the ideal horizon plane. Each segment has its own
# visibility control and can therefore be selected independently.
axis_radius = 0.93 * scene.sphere_radius
plane_axes = IllustrationLayer(name="ejes_del_horizonte_ideal")
north_south_axis = plane_axes.add_segment(
    "horizonte_ideal.norte_sur",
    LineSegment(
        start=-axis_radius * scene.horizontal.zero,
        end=axis_radius * scene.horizontal.zero,
        style=SegmentStyle(color="#805f45", width=2.0, opacity=0.72),
    ),
)
east_west_axis = plane_axes.add_segment(
    "horizonte_ideal.este_oeste",
    LineSegment(
        start=-axis_radius * scene.horizontal.east,
        end=axis_radius * scene.horizontal.east,
        style=SegmentStyle(color="#6f7650", width=2.0, opacity=0.72),
    ),
)
scene.add(plane_axes)

# Earth visibility is a reusable scene-object control, not example-specific
# widget code. The observer, tangent platform, and celestial references remain.
scene.add_visibility_control(
    scene.earth,
    title="Contexto local",
    label="Mostrar la Tierra",
)
scene.add_visibility_control(
    north_south_axis,
    title="Ejes del horizonte ideal",
    label="Línea N–S",
)
scene.add_visibility_control(
    east_west_axis,
    title="Ejes del horizonte ideal",
    label="Línea E–O",
)

star_angles = {"azimuth": 45.0, "altitude": 30.0}


def set_star_direction(*, azimuth=None, altitude=None):
    """Synchronize every illustration derived from the selected direction."""
    if azimuth is not None:
        star_angles["azimuth"] = float(azimuth)
    if altitude is not None:
        star_angles["altitude"] = float(altitude)
    updated_target = star.with_direction(
        scene.horizontal.point(
            star_angles["azimuth"],
            star_angles["altitude"],
        )
    )
    coordinates.set_target(updated_target, render=False)
    ideal_sight_line.set_target(updated_target, render=False)
    scene.plotter.render()


scene.add_scalar_control(
    set_value=lambda value: set_star_direction(azimuth=value),
    get_value=lambda: star_angles["azimuth"],
    title="Acimut de la estrella",
    value_range=(0.0, 359.0),
    value_format="%.0f°",
)
scene.add_scalar_control(
    set_value=lambda value: set_star_direction(altitude=value),
    get_value=lambda: star_angles["altitude"],
    title="Altura de la estrella",
    value_range=(1.0, 89.0),
    value_format="%.0f°",
)
scene.add_scalar_control(
    set_value=lambda value: scene.local_cartoon.set_observer_anchor_height(
        observer=scene.observer.name,
        anchor="feet",
        axis=scene.horizontal.pole,
        height=value,
    ),
    get_value=lambda: scene.local_cartoon.observer_anchor_height(
        observer=scene.observer.name,
        anchor="feet",
        axis=scene.horizontal.pole,
    ),
    title="Altura del horizonte local",
    value_range=(-0.15, 0.35),
    value_format="%.2f",
)
scene.add_annotation_controls(references, coordinates)

scene.show()

output_directory = Path(__file__).resolve().parents[1] / "outputs"
output_directory.mkdir(parents=True, exist_ok=True)
output_path = output_directory / "altaz_en_espanol.png"
scene.save_sphere_frame(output_path)
print(f"Imagen guardada en: {output_path}")
scene.close()
