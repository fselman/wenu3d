# Wenu3D Current Architecture

**Version:** 0.13
**Date:** 2026-07-31
**Status:** Description through M9.4.2 on `feature/interactive-grid-controls`

## 1. Purpose

This document describes Wenu3D as it exists in the repository. It is
descriptive rather than aspirational; the repository remains the source of
truth.

Wenu3D is a standalone PyVista package for geometrically correct 3D astronomy
illustrations for teaching, publications, and outreach. It is not an
interactive planetarium. A later horizon may make it a renderer for Wenu, but
that integration does not yet exist.

## 2. Package responsibilities

| Module | Current responsibility |
|---|---|
| `geometry.py` | Vector normalization |
| `frames.py` | Orthonormal spherical frames |
| `geography.py` | Spherical Earth-fixed positions and local ENU frames |
| `curves.py` | Sampled Cartesian curves, styles, meridians, and parallels |
| `arcs.py` | Renderer-neutral partial great-circle and small-circle geometry |
| `camera.py` | Validated, renderer-neutral camera state |
| `rendering.py` | Low-level PyVista tubes and arrows |
| `scene_object.py` | Base drawable object and actor state |
| `layer.py` | Composite collection of scene objects |
| `markers.py` | Finite marker records and styles |
| `marker_object.py` | Lifecycle-managed marker rendering |
| `segments.py` | Finite segment and sight-line records and styles |
| `segment_object.py` | Lifecycle-managed segment rendering |
| `vectors.py` | Finite solid-vector records and styles |
| `vector_object.py` | Lifecycle-managed solid-vector rendering |
| `curve_object.py` | Lifecycle-managed sampled-curve rendering |
| `surfaces.py` | Finite plane records, frames, and styles |
| `surface_object.py` | Lifecycle-managed finite-surface rendering |
| `illustration.py` | Mixed scientific-illustration layer |
| `grid.py` | Grid styles, curves, and layers |
| `annotations.py` | Annotation records, objects, styles, and layers |
| `controls.py` | Managed grid, annotation, and global controls |
| `shell.py` | Celestial-shell mesh, material, presence, and callback lifecycle |
| `earth.py` | Earth orientation and lifecycle-managed Earth rendering |
| `observer_model.py` | Renderer-neutral semantic observer record |
| `observer.py` | Observer representations, composition, and legacy helpers |
| `local_group.py` | Scaling a raw group of actors |
| `style.py` | Flat scene styling |
| `scene.py` | Scene composition, camera, rendering, grids, and controls |

`examples/la_ligua_interactive_grids.py` is the canonical example and uses the
current API.

## 3. Scientific geometry

`SphericalFrame` stores an orthonormal basis:

- `pole`: positive-latitude axis;
- `zero`: zero-longitude direction;
- `east`: increasing-longitude direction.

Construction normalizes the vectors and removes non-orthogonal components.
When `east` is omitted, it is inferred to complete a right-handed basis. An
explicitly supplied increasing-longitude direction is preserved, allowing the
horizontal convention in which azimuth increases from North toward East.

`point()` converts longitude and latitude to Cartesian coordinates. The local
convention is +x East, +y North, and +z Zenith.

`horizontal_frame()` supplies the local horizontal basis.
`equatorial_frame(latitude_deg)` correctly inclines the celestial pole, but
chooses zero longitude on the upper local meridian. It therefore illustrates
equatorial geometry but does not define absolute right ascension: observation
time, sidereal time, and epoch are absent.

`earth_fixed_frame()` defines one renderer-neutral spherical world frame:
longitude zero on +x, longitude 90 degrees East on +y, and the geographic
north pole on +z. `geographic_position()` maps a spherical latitude,
east-positive longitude, and radius into that frame. This is deliberately a
spherical cartoon-Earth model, not an ellipsoidal geodetic conversion.

`local_enu_frame()` derives East, North, and Zenith at any geographic site in
the same Earth-fixed frame. At either geographic pole, longitude selects the
limiting local meridian and therefore fixes otherwise non-unique East and
North directions without division by `cos(latitude)`. These functions are
public renderer-neutral geometry; the current `CelestialScene` does not yet
consume them, so its accepted single-observer appearance is unchanged.

`Meridian` and `Parallel` are immutable, renderer-neutral sampled geometry
objects. `SampledCurve` generalizes ordered finite Cartesian samples with
renderer-neutral color, width, opacity, visibility, and arrowhead style.

`SphericalArc` samples a validated partial great circle or constant-latitude
small circle in an explicit `SphericalFrame`. It preserves increasing or
decreasing parameter direction and converts directly to `SampledCurve`, so
partial coordinate arcs use the general curve renderer rather than a
coordinate-specific rendering path.

Finite marker, segment, sight-line, and rectangular-plane records validate
their Cartesian geometry independently of PyVista. A `PlaneSurface` stores an
explicit center, normal, orthogonal in-plane axes, dimensions, style, and
counterclockwise corners.

## 4. Object model

The intended structure is:

```text
CelestialScene
    SceneGraph
        Layer
            SceneObject
                PyVista Actor
```

`SceneObject` owns a name, independent and effective visibility, opacity,
actors, and its current plotter attachment. Subclasses implement
`build(plotter)`. Rebuilding detaches previously owned actors first, and
`detach()` removes those actors from the plotter.

`Layer` is a composite `SceneObject`. It owns children and delegates building
and lifecycle, while also duplicating child actor references in its own actor
list. Layer visibility is inherited: hiding a layer does not overwrite a
child's own visibility selection, and a child cannot expose itself while an
ancestor layer remains hidden.

`SceneGraph` is a name-indexed dictionary of layers with duplicate-name
protection and lookup. It preserves insertion order, supports ordered
iteration and length, and provides actor-safe `remove()` and `clear()`.

The grid, celestial shell, Earth, finite platform, cardinal vectors,
annotations, and M8 illustration primitives follow this object model. The
canonical observer and celestial axis are still created directly by
`CelestialScene`. `ActorScaleGroup` is consequently a second actor-management
mechanism outside the graph.

M9.3 adds an `ObserverComposition` layer outside the canonical scene path. It
associates one semantic `Observer` with one replaceable
`ObserverRepresentation` and may contain ordinary context children through the
existing layer API. Replacing an attached representation detaches its actors,
retains the other children, rebuilds safely, and preserves inherited layer
visibility.

## 5. Grid system

Each meridian or parallel is a `GridCurveObject`. It stores a frame, angle,
sphere radius, tube radius, color, opacity, and a string selecting meridian or
parallel geometry.

`GridLayer` contains individually addressable meridians and parallels. It
supports:

- individual curve visibility;
- whole-family visibility;
- major and minor curves;
- independent style and radius.

`CelestialScene.make_horizontal_grid()` and `make_equatorial_grid()` are
factories. The resulting layer must be added explicitly with `scene.add()`.

Grid label layers are created with `GridLayer.make_label_layer()`. Their
anchors are specified independently for meridians and parallels, and each
label retains the name of its associated grid curve.

## 6. Controls

`ControlManager` owns panel registration, widget lifetime, collision-aware
pixel layout, state synchronization, and nested render batching. Callers add
supported panels without calculating coordinates; the manager stacks panels
and wraps them into additional columns within the configured window.

`GridControlPanel` provides three visibility levels:

1. complete grid;
2. meridian or parallel family;
3. individual curve.

Family hiding preserves individual selections. Whole-grid hiding uses inherited
layer visibility and therefore also preserves curve selections. Grid and
individual-curve widgets initialize from the model and can be synchronized
after programmatic model changes.

`AnnotationControlPanel` controls visibility and text-size scale for one or
more annotation layers. `GlobalControlPanel` controls shell presence and
local-object scale and provides a momentary camera-reset action. These panels
also synchronize their widget representations from current model state.

The canonical example registers two grid panels, one shared annotation panel,
and one global panel without specifying panel coordinates.

Current limitations are that panel dimensions remain fixed in pixels, grid
hierarchy is still implemented by a grid-specific panel, and there is no
general capability-driven control factory. Restore-defaults is deferred
because scene objects do not yet retain a universal creation-time state.

## 7. Celestial shell and local illustration

The shell is a `CelestialShellObject` inside the named `celestial_shell`
layer. It owns a high-resolution sphere with camera-dependent per-vertex RGBA
values, limb emphasis, two specular sources, presence, its PyVista actor, and
its camera interaction callback. Rebuild and detach replace or remove both the
actor and callback through the standard scene-object lifecycle.

`CelestialScene` creates and retains the shell object for camera refresh and
global presence controls, but it no longer implements shell mesh, material, or
callback behavior. The shell layer is cleared with the rest of the
`SceneGraph` during scene cleanup.

`EarthObject` owns the current oriented Earth mesh, globe texture, material
parameters, PyVista actor, and standard rebuild/detach lifecycle. It is the
first child of the named `local_cartoon` graph layer.

The finite platform is a general `PlaneSurface` rendered by `SurfaceObject`.
Its established center, East/North axes, dimensions, opacity, color, and edge
treatment are preserved. Four `VectorObject` children render the cardinal
directions through the existing solid PyVista-arrow path. `VectorArrow` and
`VectorStyle` are renderer-neutral general records rather than local-specific
types.

Earth, platform, and cardinal-vector actors are temporarily registered with
`ActorScaleGroup` so the existing local-scale control remains unchanged until
M9.6 replaces that parallel mechanism.

The observer and celestial axis are still constructed directly by
`CelestialScene`. Some local styling remains hard-coded. The legacy
rendered-Earth orientation divides by
`cos(latitude)` and remains singular at the geographic poles; the stable M9.2
Earth-fixed geometry is not yet connected to Earth rendering.

The current composition is a single-observer display convention rather than
an Earth-fixed multi-observer model. Its horizontal frame is always local
`+x` East, `+y` North, and `+z` Zenith. Earth is rotated so that the selected
site, including the texture's 180-degree longitude correction, lies beneath
that fixed zenith; adding a second geographic observer is not yet modeled.

The finite platform is centered at
`(earth_radius + 0.012) * zenith`, parallel to the centered mathematical
horizon but displaced from the celestial origin. Earth, the platform, four
cardinal arrows, and the seven stick-figure actors belong to the raw
`ActorScaleGroup`. The celestial axis is also a direct actor but is not a
member of that scale group. Centered grid geometry remains at its configured
sphere radius when the raw local actors are scaled.

The canonical scene now has first-class Earth, finite-platform, and cardinal-
vector objects in `local_cartoon`. It does not yet use the semantic observer
composition, and it has no model-aware local transform or ideal-horizon
object. The remaining raw local actors migrate in later M9.4 checkpoints.

`Observer` is renderer-neutral and owns a stable identity, an immutable finite
position, a validated local `SphericalFrame`, and optional geographic metadata.
`Observer.at_geographic_site()` constructs consistent position and ENU frame
state from M9.2 geometry. Explicit observers may instead occupy any finite
cartoon position, including the celestial origin.

`ObserverRepresentation` is the drawable interface for representation-owned
semantic anchors. `StickFigureRepresentation` preserves the existing six tube
actors and one head actor and exposes feet, left foot, right foot, hips,
shoulders, neck, head, and eye anchors. For the current featureless spherical
head, eye and head use the same center. `add_observer()` remains as a backward-
compatible wrapper and now builds through this representation without changing
the canonical appearance.

## 8. Styling

`SceneStyle` is a flat dataclass containing shell, grid, plane, and text
properties. `GridStyle` separately holds major/minor curve widths and
opacities. Other rendering and widget constants remain hard-coded.

## 9. Rendering and output

`CelestialScene` owns a PyVista `Plotter`, camera, lighting, and window size.
`show(screenshot=...)` opens the window, optionally writes a screenshot, and
uses `auto_close=False`.

The public rendering lifecycle is:

- `render()` refreshes derived scene state and renders once;
- `show()` uses that render path before interaction;
- `save()` renders and writes an image without closing the scene;
- `close()` releases scene-graph and PyVista resources exactly once.

`CameraState` is an immutable, validated, renderer-neutral record containing
position, focal point, view-up vector, view angle, parallel-projection state,
and parallel scale. `camera_state`, `set_camera()`, and `reset_camera()` make
views explicit and reproducible.

The plotter supports interactive and off-screen construction. `save()` accepts
an optional camera state, export-specific dimensions, and opaque RGB or
transparent RGBA output. Repeated render and save calls reuse the existing
scene content: the title is added once, graph layers are not rebuilt, and
controls are synchronized without requesting an extra render.

`close()` clears attached graph layers without rendering and closes the
plotter. Clearing the shell layer unregisters its camera observer and removes
its actor. Repeated cleanup is harmless, and a detached shell callback ignores
late interaction events.

Visibility, opacity, detach, remove, and clear operations honor their `render`
argument. The current grid and shell object paths support safe detach and
rebuild without actor or callback accumulation.

## 10. Annotation state

`Annotation` is a renderer-neutral record containing text, a 3D anchor,
offset, style, visibility, and an optional association name.

`AnnotationObject` is a `SceneObject` that renders one record as a
camera-facing point label. `AnnotationLayer` owns named annotation objects,
supports layer visibility and text-size scaling, and rebuilds its children
safely when text properties change.

Grid labels and manual scientific callouts use the same annotation object
path. The canonical example includes selected horizontal-grid labels and a
Spanish callout for the south celestial pole. Annotation selection remains
independent from associated curve visibility.

## 11. General scientific illustration primitives

M8 adds a coordinate-independent vocabulary for finite scientific diagrams:

- `Marker` and `MarkerStyle` describe a finite sphere or eight-point star;
- `LineSegment` and `SightLine` describe finite Cartesian endpoints using one
  segment style and renderer;
- `SampledCurve` and `CurveStyle` describe connected polylines with optional
  start or end arrowheads;
- `SphericalArc` supplies partial great-circle and small-circle samples to the
  general curve path;
- `PlaneSurface` and `SurfaceStyle` describe a finite rectangular plane with
  explicit orientation and edge treatment.

`MarkerObject`, `SegmentObject`, `CurveObject`, and `SurfaceObject` translate
those records into PyVista meshes and actors. Each derives its initial
visibility and opacity from its record and uses the established
`SceneObject` lifecycle. Rebuilding on the same or another plotter first
removes owned actors, and detaching clears both actors and retained meshes.

The star marker is finite, camera-independent stellated geometry. Its color
and radius are ordinary `MarkerStyle` values, so a large golden star does not
require a special renderer. Thick partial arcs similarly result from
`SphericalArc.to_curve()` plus `CurveStyle`, and are rendered by
`CurveObject`.

`IllustrationLayer` is a semantic `Layer` specialization with typed helpers
for markers, segments and sight lines, curves, surfaces, and annotations. It
retains insertion order and the ordinary layer lifecycle. A complete
scientific explanation can therefore be hidden, rebuilt, detached, or removed
as a unit without overwriting each child's own visibility selection.

These primitives are public package-root exports. They are not yet used by
the canonical local Earth/observer composition; that migration begins in M9.

## 12. Verification state

The M2 scientific test suite verifies:

- vector normalization and invalid vector components;
- frame orthogonality and orientation;
- coordinate conversion and broadcasting;
- coordinate, radius, and observer-latitude validation;
- meridian and parallel sampling;
- invalid curve definitions.

An off-screen rendering smoke test also verifies that a small `GridLayer`
builds three PyVista actors and produces a nonempty PNG with the requested
dimensions.

M3 lifecycle tests verify safe detach, rebuild on the same or another plotter,
stable actor counts, graph ordering/removal/clearing, inherited visibility,
retained child selections, and render requests.

M4 tests verify annotation records, validation, object rendering, layer
lifecycle, grid-label anchors and associations, visibility, and text-size
scaling.

M5 tests verify:

- panel registration, placement, wrapping, and overlap detection;
- nested render batching;
- annotation, global, grid, family, and individual state synchronization;
- preservation of curve selections while grids or families are hidden;
- compact slider placement within declared panel footprints;
- the canonical camera-reset action.

The M5 roadmap gate is satisfied:

- the canonical example calculates no panel coordinates;
- managed panels fit its supported `1800 × 1200` window;
- widgets reflect initial and subsequently synchronized model state;
- the object and rendering paths remain usable without registering controls.

M6 tests verify:

- complete camera-state validation, capture, application, and reset;
- idempotent render and title behavior;
- reuse of scene content across repeated saves;
- off-screen plotter configuration;
- explicit output dimensions and opaque or transparent output;
- observer removal, graph detachment, plotter closure, and repeated cleanup.

The M6 roadmap gate is satisfied:

- an off-screen scene exports without opening an interactive window;
- repeated saves do not rebuild layers or duplicate the title;
- explicit camera state reproduces a configured view;
- configurable RGB and RGBA export is available;
- the canonical interactive example and controls remain operational.

M7 tests verify:

- shell mesh resolution, normals, RGBA storage, and actor configuration;
- camera-dependent material refresh and fully transparent zero presence;
- callback installation, optional interactor behavior, and safe late events;
- actor and callback replacement during rebuild;
- complete actor and callback release during detach;
- integration as the named `celestial_shell` scene layer;
- camera, rendering, presence-control, and scene-cleanup integration.

The M7 roadmap gate is satisfied:

- the characterized shell appearance and material behavior are preserved;
- rebuild and detach do not duplicate actors or camera callbacks;
- global shell-presence controls use the shell object state;
- the canonical interactive example and full test suite remain operational;
- the legacy duplicate implementation has been removed from
  `CelestialScene`.

M8 tests verify:

- finite marker positions, shapes, style, validation, and rendering;
- finite line-segment and sight-line endpoints, length, direction, style, and
  shared rendering;
- sampled-curve validation, style, connected rendering, and optional
  arrowhead placement;
- partial great-circle and small-circle endpoints, direction, radius,
  latitude, span, sampling, and conversion to a styled `SampledCurve`;
- plane center, right-handed frame, orthogonalization, dimensions, corners,
  winding, area, surface style, and quadrilateral rendering;
- primitive visibility, opacity, hide/show, detach, and rebuild without actor
  accumulation;
- mixed marker, segment, curve, surface, and annotation grouping through
  `IllustrationLayer`;
- inherited layer visibility while retaining child selections;
- off-screen output for every renderer and the mixed illustration layer.

The M8 roadmap gate is satisfied:

- marker, segment, curve, arc, and plane geometry tests pass;
- all renderer objects safely build, hide, show, detach, and rebuild;
- the golden star uses `MarkerStyle` and the general `MarkerObject`;
- thick partial arcs use `CurveStyle` and the general `CurveObject`;
- the mixed illustration layer has stable ordered lifecycle behavior;
- the canonical interactive example and full 317-test suite remain
  operational.

M9.1 characterization tests verify the existing Earth texture-orientation
convention, fixed local frame, geographic-pole singularity, displaced tangent
platform, raw local actor membership, ungrouped celestial axis, and
independence of centered grid geometry from raw local-actor scaling. M9.1 adds
no runtime implementation.

M9.2 tests verify the Earth-fixed world axes, known equatorial and polar
positions, La Ligua's finite position and tangent frame, stable polar frames,
antipodal positions and zeniths, frame orthonormality and handedness, radius
handling, and invalid coordinates. M9.2 is additive geometry and does not
integrate the new frame with rendering or scene composition.

M9.3 tests verify explicit and geographic observers, immutable positions,
geographic position/frame consistency, representation anchors, preserved
seven-actor stick-figure geometry, representation lifecycle, legacy-wrapper
compatibility, composition association, retained context, and safe attached
representation replacement. The canonical scene continues to use the legacy
wrapper, so M9.3 changes architecture without migrating scene ownership.

M9.4.1 tests verify Earth validation, preserved mesh and texture construction,
material parameters, actor ownership, safe rebuild and detach, graph placement
in `local_cartoon`, and temporary participation in legacy local scaling. The
platform, cardinal arrows, observer, and axis remain on their previous paths.

M9.4.2 tests verify renderer-neutral vector validation and normalization,
solid-arrow rendering, visibility and opacity state, safe rebuild and detach,
platform geometry and material preservation, graph ownership of the platform
and four cardinal vectors, and temporary participation in legacy local
scaling. The semantic observer and celestial axis remain unmigrated.

The repository does not yet automatically execute the canonical interactive
example. M9.1 verifies Earth orientation analytically but does not introduce a
pixel-based texture-orientation regression test.

## 13. Strengths

1. Compact, understandable spherical geometry.
2. Reusable `SphericalFrame`.
3. Working `Scene → Layer → SceneObject` lifecycle for grids and the shell.
4. Individually addressable grid curves.
5. First-class annotations through the object model.
6. Managed controls with layout, synchronization, and render batching.
7. Explicit reproducible camera and rendering lifecycle.
8. Configurable off-screen RGB and transparent RGBA export.
9. Small codebase suitable for incremental improvement.
10. Renderer-neutral finite markers, segments, curves, arcs, and planes.
11. Reusable primitive renderers with uniform lifecycle behavior.
12. Mixed scientific explanations grouped by `IllustrationLayer`.
13. Renderer-neutral spherical Earth-fixed positions and local ENU frames.
14. Semantic observers with replaceable lifecycle-managed representations.

## 14. Liabilities

1. The observer and celestial axis still bypass the graph.
2. `CelestialScene` has too many responsibilities.
3. Rendering lifecycle responsibilities have not yet moved into a separate
   render context.
4. Controls use fixed pixel footprints and object-specific panel classes.
5. Restore-default behavior has no model-level definition.
6. Pixel output is not regression-tested across platforms.
7. Equatorial coordinates are diagrammatic, not time-aware.

## 15. Current boundary

Wenu3D currently owns diagrammatic geometry, PyVista rendering, fixed scene
composition, first-class annotations, managed interactive controls, a
reproducible camera, deterministic interactive/off-screen rendering,
configurable image export, explicit cleanup, and a lifecycle-managed celestial
shell. It also owns renderer-neutral finite marker, segment, sight-line,
sampled-curve, spherical-arc, and rectangular-plane records; their PyVista
scene objects; mixed illustration layers; and spherical Earth-fixed geographic
positions and local ENU frames. It also owns a renderer-neutral observer model,
semantic representation anchors, the preserved stick-figure representation,
and an observer composition layer that is not yet integrated into the
canonical scene.

It does not own or consume a Wenu `Observer`, `CelestialSphere`, Wenu layers,
catalogs, apparent positions, or renderer-neutral Wenu primitives. Horizon A
must first make the standalone product coherent, tested, reproducible, and
extensible.
