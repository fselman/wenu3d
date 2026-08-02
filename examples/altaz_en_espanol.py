"""Vista con coordenadas horizontales o ecuatoriales en español."""

from pathlib import Path

from wenu3d import (
    AnnotationStyle,
    CelestialScene,
    CelestialTarget,
    CurveStyle,
    EquatorialCoordinateIllustration,
    EquatorialCoordinateGeometry,
    EquatorialLabels,
    EquatorialReferenceIllustration,
    GridStyle,
    HorizontalCoordinateIllustration,
    HorizontalCoordinateGeometry,
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
    title="Coordenadas celestes: horizontal y ecuatorial",
    axis_visible=False,
    window_size=(1600, 1150),
)

# Horizontal-coordinate geometry is clearest in the limiting view from an
# infinitely distant diagram camera. This changes only the projection used to
# view the illustration; the astronomical observer remains at the center of
# the celestial sphere.
scene.set_parallel_projection(
    True,
    parallel_scale=1.12 * scene.sphere_radius,
    make_default=True,
    render=False,
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

equatorial_labels = EquatorialLabels(
    right_ascension="RA",
    declination="Dec",
    north_celestial_pole="PNC",
    south_celestial_pole="PSC",
    equator="Ecuador celeste",
)

# The scene's base equatorial frame fixes the celestial poles from latitude.
# Its longitude zero lies initially on the upper local meridian. The RA-origin
# slider rotates this explicit illustration frame around the fixed polar axis.
ra_origin = {"offset_hours": 0.0}
equatorial_frame = scene.equatorial.with_longitude_origin(
    15.0 * ra_origin["offset_hours"],
    name="equatorial_ajustable",
)
equatorial_references = EquatorialReferenceIllustration(
    name="referencias_ecuatoriales",
    frame=equatorial_frame,
    radius=0.982 * scene.sphere_radius,
    labels=equatorial_labels,
    equator_style=CurveStyle(
        color="#665b78",
        width=2.2,
        opacity=0.68,
    ),
    zero_tick_style=CurveStyle(
        color="#463953",
        width=5.0,
        opacity=0.92,
    ),
    annotation_style=AnnotationStyle(
        color="#302943",
        font_size=17,
        bold=True,
    ),
)
scene.add(equatorial_references)

# A reusable equatorial grid follows the selected RA frame. Meridians are
# separated by 2 h (30 degrees) and parallels by 20 degrees. The equator is
# drawn separately by the reference illustration, so every grid curve remains
# deliberately faint and the RA zero is marked only by its heavy tick.
equatorial_grid = scene.make_equatorial_grid(
    name="reticula_ecuatorial",
    frame=equatorial_frame,
    meridians_deg=tuple(range(0, 360, 30)),
    parallels_deg=tuple(range(-80, 81, 20)),
    major_meridians_deg=(),
    major_parallels_deg=(),
    style=GridStyle(
        color="#776f82",
        major_radius=0.0012,
        minor_radius=0.0012,
        major_opacity=0.25,
        minor_opacity=0.25,
    ),
)
scene.add(equatorial_grid)

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

equatorial_coordinates = EquatorialCoordinateIllustration(
    name="coordenadas_ecuatoriales_estrella",
    target=star,
    frame=equatorial_frame,
    longitude_kind="right_ascension",
    right_ascension_origin="origen ajustable de esta ilustración",
    labels=equatorial_labels,
    angle_decimals=1,
    show_hour_circle=True,
    show_declination_circle=True,
    hour_circle_style=CurveStyle(
        color="#776c86",
        width=1.0,
        opacity=0.24,
    ),
    declination_circle_style=CurveStyle(
        color="#776c86",
        width=1.0,
        opacity=0.18,
    ),
    declination_style=CurveStyle(
        color="#8b5fbf",
        width=4.5,
        opacity=0.95,
        arrowheads="end",
    ),
    longitude_style=CurveStyle(
        color="#bd6f3f",
        width=4.5,
        opacity=0.95,
        arrowheads="end",
    ),
    annotation_style=AnnotationStyle(
        color="#2d203b",
        font_size=16,
        bold=True,
    ),
)
scene.add(equatorial_coordinates)

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

# Restore the standard celestial-shell, local-scale, and camera controls.
scene.add_global_controls()

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

target_state = {"target": star}
star_angles = {"azimuth": 45.0, "altitude": 30.0}
initial_equatorial = EquatorialCoordinateGeometry(
    target=star,
    frame=equatorial_frame,
    longitude_kind="right_ascension",
    right_ascension_origin="origen ajustable de esta ilustración",
)
equatorial_angles = {
    "right_ascension_hours": initial_equatorial.right_ascension_hours,
    "declination_deg": initial_equatorial.declination_deg,
}
coordinate_mode = {"value": "equatorial"}


def replace_target(
    updated_target: CelestialTarget,
    *,
    equatorial_frame_override=None,
) -> None:
    """Synchronize every illustration derived from the selected direction."""
    target_state["target"] = updated_target
    coordinates.set_target(updated_target, render=False)
    equatorial_coordinates.set_target_and_frame(
        target=updated_target,
        frame=equatorial_frame_override,
        render=False,
    )
    ideal_sight_line.set_target(updated_target, render=False)


def update_horizontal_values_from_target() -> None:
    geometry = HorizontalCoordinateGeometry(
        target=target_state["target"],
        frame=scene.horizontal,
    )
    star_angles["azimuth"] = geometry.azimuth_deg
    star_angles["altitude"] = geometry.altitude_deg


def update_equatorial_values_from_target() -> None:
    geometry = EquatorialCoordinateGeometry(
        target=target_state["target"],
        frame=equatorial_references.frame,
        longitude_kind="right_ascension",
        right_ascension_origin="origen ajustable de esta ilustración",
    )
    equatorial_angles["right_ascension_hours"] = (
        geometry.right_ascension_hours
    )
    equatorial_angles["declination_deg"] = geometry.declination_deg


def set_coordinate_mode(mode: str) -> None:
    """Show one coordinate composition while retaining common context."""
    if mode not in ("horizontal", "equatorial"):
        raise ValueError(f"Modo de coordenadas desconocido: {mode}")
    coordinate_mode["value"] = mode
    if mode == "horizontal":
        update_horizontal_values_from_target()
    else:
        update_equatorial_values_from_target()
    coordinates.set_visible(mode == "horizontal", render=False)
    equatorial_grid.set_visible(mode == "equatorial", render=False)
    equatorial_references.set_visible(mode == "equatorial", render=False)
    equatorial_coordinates.set_visible(mode == "equatorial", render=False)
    if mode == "horizontal":
        primary_coordinate_panel.set_capability(
            set_value=lambda value: set_star_direction(azimuth=value),
            get_value=lambda: star_angles["azimuth"],
            title="Acimut de la estrella",
            value_range=(0.0, 359.0),
            value_format="%.0f°",
        )
        secondary_coordinate_panel.set_capability(
            set_value=lambda value: set_star_direction(altitude=value),
            get_value=lambda: star_angles["altitude"],
            title="Altura de la estrella",
            value_range=(1.0, 89.0),
            value_format="%.0f°",
        )
    else:
        primary_coordinate_panel.set_capability(
            set_value=lambda value: set_equatorial_direction(
                right_ascension_hours=value
            ),
            get_value=lambda: equatorial_angles["right_ascension_hours"],
            title="RA de la estrella",
            value_range=(0.0, 24.0),
            value_format="%.1f h",
        )
        secondary_coordinate_panel.set_capability(
            set_value=lambda value: set_equatorial_direction(
                declination=value
            ),
            get_value=lambda: equatorial_angles["declination_deg"],
            title="Dec de la estrella",
            value_range=(-89.0, 89.0),
            value_format="%.0f°",
        )
    scene.controls.set_panel_visible(
        ra_origin_panel,
        mode == "equatorial",
        render=False,
    )
    scene.controls.sync(render=False)
    scene.plotter.render()


def set_star_direction(*, azimuth=None, altitude=None):
    """Set the target from horizontal coordinates."""
    if azimuth is not None:
        star_angles["azimuth"] = float(azimuth)
    if altitude is not None:
        star_angles["altitude"] = float(altitude)
    updated_target = target_state["target"].with_direction(
        scene.horizontal.point(
            star_angles["azimuth"],
            star_angles["altitude"],
        )
    )
    replace_target(updated_target)
    scene.plotter.render()


def set_equatorial_direction(*, right_ascension_hours=None, declination=None):
    """Set the target from RA and Dec in the current equatorial frame."""
    if right_ascension_hours is not None:
        equatorial_angles["right_ascension_hours"] = float(
            right_ascension_hours
        ) % 24.0
    if declination is not None:
        equatorial_angles["declination_deg"] = float(declination)
    updated_target = target_state["target"].with_direction(
        equatorial_references.frame.point(
            15.0 * equatorial_angles["right_ascension_hours"],
            equatorial_angles["declination_deg"],
        )
    )
    replace_target(updated_target)
    scene.plotter.render()


def set_ra_origin(offset_hours: float) -> None:
    """Rotate the RA frame while retaining the selected RA and Dec values."""
    ra_origin["offset_hours"] = float(offset_hours) % 24.0
    updated_frame = scene.equatorial.with_longitude_origin(
        15.0 * ra_origin["offset_hours"],
        name="equatorial_ajustable",
    )
    equatorial_references.set_frame(updated_frame, render=False)
    equatorial_grid.set_frame(updated_frame, render=False)
    updated_target = target_state["target"].with_direction(
        updated_frame.point(
            15.0 * equatorial_angles["right_ascension_hours"],
            equatorial_angles["declination_deg"],
        )
    )
    replace_target(
        updated_target,
        equatorial_frame_override=updated_frame,
    )
    scene.plotter.render()


scene.add_choice_control(
    set_choice=set_coordinate_mode,
    get_choice=lambda: coordinate_mode["value"],
    choices=(
        ("horizontal", "Horizontal: acimut y altura"),
        ("equatorial", "Ecuatorial: RA y Dec"),
    ),
    title="Sistema de coordenadas",
    group="sistema_de_coordenadas",
)
primary_coordinate_panel = scene.add_scalar_control(
    set_value=lambda value: set_star_direction(azimuth=value),
    get_value=lambda: star_angles["azimuth"],
    title="Acimut de la estrella",
    value_range=(0.0, 359.0),
    value_format="%.0f°",
)
secondary_coordinate_panel = scene.add_scalar_control(
    set_value=lambda value: set_star_direction(altitude=value),
    get_value=lambda: star_angles["altitude"],
    title="Altura de la estrella",
    value_range=(1.0, 89.0),
    value_format="%.0f°",
)
ra_origin_panel = scene.add_scalar_control(
    set_value=set_ra_origin,
    get_value=lambda: ra_origin["offset_hours"],
    title="Origen de RA",
    value_range=(0.0, 24.0),
    value_format="%.1f h",
)
local_height_panel = scene.add_scalar_control(
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
scene.add_annotation_controls(
    references,
    coordinates,
    equatorial_references,
    equatorial_coordinates,
)
set_coordinate_mode("equatorial")

scene.show()

output_directory = Path(__file__).resolve().parents[1] / "outputs"
output_directory.mkdir(parents=True, exist_ok=True)
output_coordinate_name = {
    "horizontal": "altaz",
    "equatorial": "radec",
}[coordinate_mode["value"]]
output_path = output_directory / (
    f"coordenadas_{output_coordinate_name}_en_espanol.png"
)
scene.save_sphere_frame(output_path)
print(f"Imagen guardada en: {output_path}")
scene.close()
