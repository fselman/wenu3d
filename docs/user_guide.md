# Wenu3D user guide

Wenu3D creates reproducible 3D scientific illustrations of astronomical
geometry with PyVista. It is a composition toolkit, not an interactive
planetarium: callers supply the scientific geometry and Wenu3D displays it.

Public application code should import stable names from `wenu3d`. See
`api_stability.md` for the compatibility policy and `rendering_policy.md` for
transparency and occlusion semantics.

## 1. Quick start

Create a scene, add a grid, render it, and always release its resources:

```python
from wenu3d import CelestialScene


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
)
try:
    horizontal = scene.make_horizontal_grid()
    scene.add(horizontal)
    scene.show()
finally:
    scene.close()
```

`CelestialScene` already contains the celestial shell, one cartoon Earth, one
canonical observer and local platform, the celestial axis, a reproducible
camera, and a managed control layout. Grid creation and insertion are separate
so the caller retains the layer object for styling, controls, and lifecycle
operations.

## 2. Interactive workflow

Add both grid families and register controls before opening the window:

```python
from wenu3d import CelestialScene


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
)
try:
    horizontal = scene.add(scene.make_horizontal_grid())
    equatorial = scene.add(scene.make_equatorial_grid())

    scene.add_grid_controls(horizontal)
    scene.add_grid_controls(equatorial)
    scene.add_global_controls()
    scene.show()
finally:
    scene.close()
```

Grid panels control whole-grid, family, and individual-curve visibility.
Global controls adjust shell presence, local-cartoon scale, and camera reset.
`ControlManager` assigns panel positions; application code should not calculate
widget coordinates.

Calling `render()` refreshes controls and shell material and renders once.
`show()` renders before entering PyVista interaction and keeps the scene open.
`close()` is idempotent.

## 3. Batch rendering and export

Use `off_screen=True` when no interactive window is required:

```python
from wenu3d import CelestialScene


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    off_screen=True,
)
try:
    scene.add(scene.make_horizontal_grid())
    scene.add(scene.make_equatorial_grid())
    image = scene.save(
        "la_ligua.png",
        window_size=(1600, 1150),
        transparent_background=False,
    )
finally:
    scene.close()
```

`save()` returns the NumPy image and does not close the scene. Reusing the same
camera, window size, styles, scene state, and rendering environment produces
repeatable output. `transparent_background=True` requests RGBA canvas output;
it does not alter object opacity.

Capture `scene.camera_state` after interactively selecting a view, then apply
it with `scene.set_camera(state)` or pass it to `save(camera_state=state)`.

## 4. Annotations

Annotations are renderer-neutral text records with world-coordinate anchors
and offsets. Group them in an `AnnotationLayer`:

```python
from wenu3d import Annotation, AnnotationLayer, AnnotationStyle


labels = AnnotationLayer(name="explanation")
labels.add_annotation(
    "explanation.zenith",
    Annotation(
        text="Zenith",
        anchor=(0.0, 0.0, 1.0),
        offset=(0.03, 0.03, 0.03),
        style=AnnotationStyle(font_size=16, bold=True),
        associated_with="horizontal.zenith",
    ),
)
scene.add(labels)
scene.add_annotation_controls(labels)
```

Annotation text is an always-visible explanatory overlay. Its anchor remains
3D geometry, but opaque objects do not hide the label. Use visible markers or
curves when geometric near/far-side visibility is part of the explanation.

Grid layers can create their own selectable labels with
`grid.make_label_layer(...)`; the canonical example is the authoritative
working reference for its options.

## 5. Coordinate illustrations

A `CelestialTarget` stores a normalized direction. `display_position` is that
direction multiplied by an illustrative shell radius; it is not a physical
distance.

```python
from wenu3d import (
    CelestialTarget,
    HorizontalCoordinateIllustration,
)


target = CelestialTarget(
    name="example_star",
    direction=(0.55, 0.35, 0.76),
    shell_radius=scene.sphere_radius,
)
horizontal_coordinates = HorizontalCoordinateIllustration(
    name="coordinates.horizontal.example_star",
    target=target,
    frame=scene.horizontal,
)
scene.add(horizontal_coordinates)
```

Horizontal azimuth is measured from North through East in `[0, 360)` and
altitude is measured from the ideal horizon. Targets exactly at Zenith or
Nadir are rejected because azimuth is undefined.

Equatorial geometry uses an explicit frame:

```python
from wenu3d import EquatorialCoordinateIllustration


equatorial_coordinates = EquatorialCoordinateIllustration(
    name="coordinates.equatorial.example_star",
    target=target,
    frame=scene.equatorial,
    longitude_kind="diagrammatic",
)
scene.add(equatorial_coordinates)
```

The scene's equatorial frame illustrates declination and equatorial longitude,
but Wenu3D has no observation time, sidereal time, or epoch. Do not call its
longitude absolute right ascension unless the supplied frame and
`right_ascension_origin` have a scientifically defined origin.

## 6. Observers and local composition

`Observer` is renderer-neutral identity, position, and local ENU frame.
Representations are replaceable graphics; context contains finite platforms,
decorations, or other scene objects. The canonical observer is available as
`scene.observer`, inside `scene.observer_composition` and
`scene.local_cartoon`.

Create a geographic observer and a point representation as follows:

```python
from wenu3d import Observer, ObserverComposition, PointObserverRepresentation


second_observer = Observer.at_geographic_site(
    "second_site",
    latitude_deg=20.0,
    longitude_deg=45.0,
    earth_radius=scene.earth_radius,
)
second_representation = PointObserverRepresentation(
    name="second_site.point",
    observer=second_observer,
    radius=0.018,
)
second_composition = ObserverComposition(
    name="second_site.composition",
    observer=second_observer,
    representation=second_representation,
)
scene.local_cartoon.add_observer(second_composition)
```

The local cartoon owns exactly one shared Earth. Do not create an Earth per
observer. Use `set_observer_representation()` to replace an attached
representation while preserving the semantic observer, context, transform,
and graph lifecycle.

Named representation anchors support model-aware queries and finite sight
lines. Stick figures provide anchors including `feet`, `head`, and `eye`;
point representations provide `position`.

## 7. Ideal horizons and local platforms

Every `ObserverComposition` has an `IdealHorizon`: an infinite mathematical
plane through the celestial origin, normal to the observer's Zenith. It is not
the observer's finite local platform.

```python
from wenu3d import IllustrationLayer, SurfaceStyle


horizon_surface = scene.observer_composition.ideal_horizon.as_surface(
    width=1.5,
    style=SurfaceStyle(color="#8ba6bf", opacity=0.18),
    visible=True,
)
horizon_display = IllustrationLayer(name="canonical_ideal_horizon")
horizon_display.add_surface("canonical_ideal_horizon.surface", horizon_surface)
scene.add(horizon_display)
```

The finite surface is an optional display of the mathematical plane. A local
platform instead belongs to one observer composition, is normally tangent to
the cartoon Earth at that observer, and may carry replaceable decoration.

## 8. Target lines and parallax

Use `TargetLineIllustration` to distinguish a centered celestial direction
from finite sight lines beginning at transformed observer anchors:

```python
from wenu3d import TargetLineIllustration


target_lines = TargetLineIllustration(
    name="target_lines.example_star",
    target=target,
    local_cartoon=scene.local_cartoon,
    observer_anchors={scene.observer.name: "eye"},
)
scene.add(target_lines)
```

Parallax illustration requires at least two registered observers:

```python
from wenu3d import ParallaxIllustration


parallax = ParallaxIllustration(
    name="parallax.example_star",
    target=target,
    local_cartoon=scene.local_cartoon,
    observer_anchors={
        scene.observer.name: "eye",
        second_observer.name: "position",
    },
)
scene.add(parallax)

baseline = parallax.baseline_length(
    scene.observer.name,
    second_observer.name,
)
angle = parallax.convergence_angle_deg(
    scene.observer.name,
    second_observer.name,
)
```

These lines converge on the displayed shell marker. `display_distance` is the
illustrative shell radius, never a recovered physical target distance. The
default annotation states this limitation.

## 9. Scale comparison

`LocalScaleComparison` applies named, explicit transforms while leaving target,
coordinate, and horizon geometry fixed:

```python
from wenu3d import LocalScaleComparison


comparison = LocalScaleComparison(
    local_cartoon=scene.local_cartoon,
    observer=scene.observer.name,
    anchor="eye",
)
comparison.apply("small_cartoon")
comparison.export(
    "comparison_output",
    modes=("surface", "small_cartoon", "observer_at_origin"),
    window_size=(1200, 900),
)
```

Export restores the original local transform. The three states illustrate the
directional limit; they do not change celestial geometry.

## 10. Extending Wenu3D

Prefer composition from stable renderer-neutral primitives. A custom
scientific explanation can be an `IllustrationLayer` containing markers,
segments, curves, surfaces, and annotations:

```python
from wenu3d import (
    Annotation,
    IllustrationLayer,
    LineSegment,
    Marker,
)


illustration = IllustrationLayer(name="custom_explanation")
illustration.add_marker(
    "custom_explanation.origin",
    Marker(position=(0.0, 0.0, 0.0)),
)
illustration.add_segment(
    "custom_explanation.axis",
    LineSegment(start=(0.0, 0.0, 0.0), end=(0.0, 0.0, 0.8)),
)
illustration.add_annotation(
    "custom_explanation.label",
    Annotation(text="Reference axis", anchor=(0.0, 0.0, 0.8)),
)
scene.add(illustration)
```

Keep scientific geometry in renderer-neutral records and prefer composition
through the stable primitive objects. Direct `SceneObject` subclassing still
depends on advanced lifecycle hooks in Horizon A; isolate and test such an
extension rather than treating those hooks as stable application API.

A future Wenu adapter should translate Wenu directions and layers at the
integration boundary. It should not be implemented by coupling application
code to PyVista actors or Wenu3D private state.

## 11. Lifecycle checklist

For every scene:

1. construct the scene and layers;
2. add layers through `scene.add()`;
3. register controls only for attached layers;
4. use `render()`, `show()`, or `save()` for the intended workflow;
5. call `close()` in `finally`;
6. keep output files outside source and test directories;
7. fix camera and export parameters for publication output.
