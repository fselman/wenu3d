# Wenu3D Current Architecture

**Version:** 0.35
**Date:** 2026-07-31
**Status:** Description through M10.5 on `feature/interactive-grid-controls`

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
| `coordinates.py` | Centered coordinate-illustration geometry |
| `camera.py` | Validated, renderer-neutral camera state |
| `rendering.py` | Low-level PyVista tubes and arrows |
| `scene_object.py` | Base drawable object and actor state |
| `layer.py` | Composite collection of scene objects |
| `markers.py` | Finite marker records and styles |
| `marker_object.py` | Lifecycle-managed marker rendering |
| `targets.py` | Celestial directions and derived shell markers |
| `segments.py` | Finite segment and sight-line records and styles |
| `segment_object.py` | Lifecycle-managed segment rendering |
| `vectors.py` | Finite solid-vector records and styles |
| `vector_object.py` | Lifecycle-managed solid-vector rendering |
| `curve_object.py` | Lifecycle-managed sampled-curve rendering |
| `surfaces.py` | Finite plane records, frames, and styles |
| `surface_object.py` | Lifecycle-managed finite-surface rendering |
| `horizons.py` | Observer-specific ideal-horizon geometry |
| `platforms.py` | Finite local platforms and replaceable decorations |
| `transforms.py` | Renderer-neutral local-cartoon affine transform |
| `illustration.py` | Mixed scientific-illustration layer |
| `grid.py` | Grid styles, curves, and layers |
| `annotations.py` | Annotation records, objects, styles, and layers |
| `controls.py` | Managed grid, annotation, and global controls |
| `shell.py` | Celestial-shell mesh, material, presence, and callback lifecycle |
| `earth.py` | Stable Earth-fixed display orientation and Earth rendering |
| `observer_model.py` | Renderer-neutral semantic observer record |
| `observer.py` | Observer representations, composition, and legacy helpers |
| `local_cartoon.py` | Shared Earth and finite observer-composition layer |
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

The grid, celestial shell, Earth, finite platform, cardinal vectors, observer
composition, annotations, and M8 illustration primitives follow this object
model. The celestial axis is still created directly by `CelestialScene`.

`ObserverComposition` associates one semantic `Observer` with one replaceable
`ObserverRepresentation` and an ordered collection of validated context
objects. Context is built before the representation, can be added to an
attached composition through safe rebuild, and remains intact when the
representation is replaced. M9.4.3 connects the canonical composition to the
graph through `LocalCartoonLayer`; M9.5.2 moves its finite platform and
cardinal vectors into composition context.

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
first child of the named `LocalCartoonLayer`.

`LocalCartoonLayer` owns that one shared Earth and registers observer
compositions by semantic observer name. Duplicate observer identities are
rejected, and compositions are available through ordered iteration and named
lookup. The canonical layer currently contains one observer composition.

The finite platform is a `LocalPlatform` composition containing a general
`PlaneSurface` rendered by `SurfaceObject` and one interchangeable
`PlatformDecoration`. It is the first context object of the canonical
`ObserverComposition`. Its established center, East/North axes, dimensions,
opacity, color, and edge treatment are preserved. The current
`CardinalDirectionsDecoration` maps four `VectorObject` children to East,
West, North, and South through the existing solid PyVista-arrow path.
`VectorArrow` and `VectorStyle` are renderer-neutral general records rather
than local-specific types. Replacing or removing a decoration preserves the
platform surface and uses the standard attached-layer lifecycle.

`CardinalLinesDecoration` is an optional alternative containing validated
East, West, North, and South line segments and associated inscriptions. It
reuses `SegmentObject` and `AnnotationObject` and is not selected by the
canonical scene, so accepted output remains unchanged.

`CompassRoseDecoration` adds a conventional 16-point radial compass.
`NainoaThompsonStarCompassDecoration` represents the documented 32
equidistant houses of the Hawaiian star-compass directional system, starting
at North and proceeding clockwise in 11.25-degree steps. Both use the same
validated platform frame, line-segment, and annotation paths. The Hawaiian
class represents directional geometry and house metadata; it is not a
reproduction of the Polynesian Voyaging Society's protected artwork. The
directional convention follows the Society's educational description at
`https://worldwidevoyage.hokulea.com/education-at-sea/polynesian-navigation/the-star-compass/`.

Earth, platform, cardinal-vector, and observer actors share the transform owned
by `LocalCartoonLayer`. The existing local-scale control now updates that
model-aware transform rather than a separate raw-actor collection.

The celestial axis is still constructed directly by `CelestialScene`. Some
local styling remains hard-coded.

`earth_orientation_matrix()` maps the Earth-fixed source ENU basis at the
texture-corrected geographic site into one explicit display ENU basis. This
stable orthonormal rotation replaces the former division by `cos(latitude)`.
For nonpolar sites it is algebraically identical to the accepted orientation;
at a geographic pole, explicit display North fixes the otherwise undetermined
rotation about Zenith. `EarthObject` owns and exposes this matrix, validates
the relation between geographic latitude, display Zenith, North, and the
rotation axis, and supports both poles. The canonical scene supplies its
existing horizontal North, preserving texture placement and appearance.

M9.8.2 adds `EarthObject.display_observer()` as the explicit bridge from a
geographic observer's Earth-fixed semantic coordinates to the rendered
Earth's display coordinates. It applies the same texture-corrected orientation
used by the globe to the observer position and complete ENU frame, returns an
explicit display observer, and requires the semantic observer radius to match
the rendered Earth. A geographic observer and its antipode can therefore own
independently positioned local platforms and oppositely oriented ideal
horizons while sharing one rendered Earth and one local transform. Geographic
metadata remains on the Earth-fixed observers rather than being incorrectly
attached to their rotated display-coordinate counterparts. The canonical
scene still creates only its accepted explicit observer composition.

The finite platform is centered at
`(earth_radius + 0.012) * zenith`, parallel to the centered mathematical
horizon but displaced from the celestial origin. Earth, the platform, four
cardinal arrows, and the seven stick-figure actors belong to the local-cartoon
layer. The celestial axis remains a separate direct actor. Centered grid
geometry remains at its configured sphere radius when the local cartoon is
scaled.

The canonical `LocalCartoonLayer` now contains the shared Earth followed by one
semantic observer composition. That composition contains the finite platform,
four cardinal vectors, and replaceable `StickFigureRepresentation` in the
established actor order. The celestial axis remains the only direct actor
created by the scene.

`LocalCartoonTransform` is the renderer-neutral mathematical contract for
M9.6. It contains a finite translation and positive uniform scale and applies
the correct affine semantics to points, free vectors, directions, and lengths.
It also provides inverse, ordered composition, and a homogeneous 4-by-4
matrix. `LocalCartoonLayer` owns one such transform and uses it for transformed
point, observer-position, and named semantic-anchor queries. One transform is
shared by Earth and every observer composition.

M9.6.3 applies the transform's homogeneous matrix to every actor owned by the
layer after a build and after each attached transform update. Rendered Earth
and observer composition geometry therefore remains aligned with transformed
position and anchor queries. Updates may defer rendering for batching. The
local-scale control preserves the transform's translation while replacing its
uniform scale. This model-aware path fully replaces and retires
`ActorScaleGroup`; the canonical identity transform leaves accepted output
unchanged.

M9.6.4 adds explicit model-aware placement operations to
`LocalCartoonLayer`. `set_scale()` changes uniform scale without discarding the
current translation. `place_on_surface(observer=...)` validates the selected
observer and restores the nominal Earth-relative placement by setting layer
translation to zero while retaining scale. `place_observer_anchor_at_origin()`
preserves scale and computes the translation that maps a named representation
anchor exactly to the celestial origin. Each operation delegates to
`set_transform()`, so attached actors and renderer-neutral queries change
together. No placement mode moves centered celestial geometry or the ideal
horizons.

M9.7.1 makes observer registration lifecycle-safe after
`LocalCartoonLayer` is attached. A newly registered composition alone is
built on the existing plotter, inherits effective layer visibility, receives
the layer's current transform, and contributes its actors to the layer-owned
collection. The shared Earth and earlier observer compositions are not
rebuilt. Registration may defer rendering for batch composition. The
canonical scene still registers only its established observer, so its actor
order and appearance remain unchanged.

M9.7.2 promotes antipodal-site construction to the semantic observer model.
A geographic `Observer` can create a named antipode at the opposite latitude
and longitude while preserving Earth radius. Their positions and zeniths are
opposite, East directions are opposite, and North directions coincide; both
frames retain right-handed East-North-Zenith orientation. Their distinct
`ObserverComposition` instances own distinct, oppositely oriented ideal
horizons and coexist under one shared Earth and local transform. The
canonical scene does not add the demonstration pair, so accepted output is
unchanged.

M9.7.3 adds `PointObserverRepresentation`, a minimal one-actor spherical
marker with a semantic `position` anchor. It provides a concrete replacement
for the stick figure without changing the associated `Observer`, ideal
horizon, or composition context. `LocalCartoonLayer` owns the safe attached
replacement operation: it delegates model replacement to the composition,
refreshes its flattened actor ownership, removes stale actor references,
applies the current shared transform to the new representation, preserves
inherited visibility, and renders once unless deferred. The canonical scene
continues to select `StickFigureRepresentation`, so its appearance is
unchanged.

M9.7.4 adds `LocalCartoonLayer.make_observer_sight_line()`. The factory
resolves a named anchor through the current representation and authoritative
local transform, then creates an immutable `SightLine` whose target remains
the caller-supplied fixed display position. This makes the local-versus-
celestial boundary explicit: only the origin is derived from transformed
finite cartoon geometry. Calling the factory again after a transform or
representation change produces a reproducible updated snapshot rather than
introducing hidden live dependencies. This completes the four planned M9.7
checkpoints without adding sight lines to the canonical scene.

Each `ObserverComposition` owns an `IdealHorizon`. This renderer-neutral plane
passes through the celestial origin and is perpendicular to the observer's
zenith, independent of the observer's finite cartoon position. It exposes its
East/North basis, signed-distance and orthogonal-projection queries, and may
produce a finite `PlaneSurface` for display. Such a display surface is hidden
by default and is not added to the canonical graph, so ideal-horizon geometry
does not enter the finite local-cartoon transform or alter the accepted
illustration.

The ideal horizon and local platform are intentionally distinct: the horizon
is centered celestial geometry, while the current platform remains displaced
to `(earth_radius + 0.012) * zenith` in the finite local cartoon. They are
parallel in the canonical composition but have different centers.

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

These primitives are public package-root exports. The finite plane and vector
primitives are used by the canonical local composition; other illustration
primitives remain available for later M9 and M10 assemblies.

M10.1 adds the renderer-neutral `CelestialTarget`. It owns a nonempty name,
normalized unit direction, positive illustrative shell radius, marker style,
and visibility. `display_position` is derived as shell radius times direction,
and `as_marker()` produces the corresponding finite `Marker` without adding a
direction to that finite record. `at_shell_radius()` returns a new immutable
target with the same scientific direction at a different display radius.
Coordinate constructions will therefore consume `direction`, while explicit
sight-line or marker rendering may consume `display_position` or the derived
marker. No target is added to the canonical scene in this checkpoint.

M10.2 adds `HorizontalCoordinateGeometry`. It consumes a `CelestialTarget`'s
unit direction and an explicit `SphericalFrame`, then derives altitude,
North-through-East azimuth, and the vertical-circle foot on the ideal horizon.
Its altitude arc runs from that foot to the target along a centered vertical
great circle; its azimuth arc runs on the centered ideal horizon from North to
the foot. Both use the target's shell radius and configurable sampling.
Zero-length altitude or azimuth arcs are represented by `None` instead of an
invalid curve, and Zenith/Nadir targets are rejected because their azimuth and
vertical circle are undefined. No finite observer position participates in
these calculations, and no geometry is added to the canonical scene.

M10.3 adds `HorizontalCoordinateIllustration`, an `IllustrationLayer` that
assembles the target marker, optional altitude and azimuth curve objects, and
optional associated annotations while retaining direct access to every model,
object, and style. Default curve styles distinguish altitude and azimuth and
place an arrowhead at each arc end; callers may replace either complete
`CurveStyle`, the common `AnnotationStyle`, label precision, or label
visibility. Labels state `Altitude` and `Azimuth (North through East)` so the
diagram does not conceal its convention. Zero-span geometry omits only the
corresponding curve and label. The canonical scene remains unchanged.

M10.4 adds `EquatorialCoordinateGeometry`. It derives declination,
equatorial longitude, the hour-circle foot on the centered equator, a
declination arc from the equator to the target, and a longitude arc from the
frame's explicit zero direction to the hour circle. The caller must select
either `diagrammatic` longitude or `right_ascension`. Right ascension requires
a nonempty description of its scientifically defined origin and exposes hours;
diagrammatic longitude explicitly reports no right-ascension value. Polar
targets are rejected because their longitude and hour circle are undefined,
and zero-span arcs are omitted independently. No geometry is added to the
canonical scene.

M10.5 adds `EquatorialCoordinateIllustration`, an `IllustrationLayer` that
assembles the target marker, optional declination and longitude curve objects,
and optional associated annotations while exposing all geometry, objects, and
styles. Diagrammatic longitude labels use degrees and name the quantity
explicitly. Right-ascension labels use hours and include the required origin
description. Default curve styles place end arrowheads, while callers retain
control of both `CurveStyle` records, the common `AnnotationStyle`, precision,
and label visibility. Zero-span components are omitted independently, and the
canonical scene remains unchanged.

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

M9.4.3 tests verify one shared Earth per `LocalCartoonLayer`, ordered and named
observer-composition registration, duplicate observer rejection, canonical
semantic-observer geometry, graph ownership of the stick-figure
representation, preserved actor order, and one complete registration with the
temporary local scale group. The legacy `add_observer()` wrapper remains for
backward compatibility, but the canonical scene no longer uses it.

M9.5.1 tests verify ideal-horizon origin and observer-frame orientation,
arbitrary tilted ENU frames, handedness validation, signed distance,
orthogonal projection, invalid query geometry, hidden-by-default finite display
surfaces, explicit surface style and visibility, composition association, and
canonical separation from the displaced local platform. No ideal-horizon
actor is added by default.

M9.5.2 tests verify validated ordered observer context, context insertion and
safe attached rebuild, retention across representation replacement, canonical
ownership of the platform and cardinal vectors by the observer composition,
unchanged flattened actor order, and one temporary scale-group registration.

M9.5.3 tests verify the finite platform/decorations ownership boundary,
semantic cardinal-direction ordering and lookup, component validation,
attached decoration replacement and removal, canonical nesting, unchanged
flattened actor order, and preserved platform/vector objects.

M9.5.4 tests verify optional East, West, North, and South segment endpoints,
inscription associations, orthogonalized platform axes, and invalid extent
handling through the common decoration interface.

M9.5.5 tests verify 16-point compass bearings, 32 equidistant Hawaiian star-
compass houses, cardinal Hawaiian bearings, quadrant house ordering, platform-
frame validation, radius validation, and compatibility with the common
decoration interface. Neither optional decoration is selected by the canonical
scene.

M9.6.1 tests verify identity, point translation and scale, vector and direction
semantics, transformed lengths, batched geometry, inverse round trips, ordered
composition, homogeneous matrices, and invalid transform or query values. It
does not alter actors or canonical scene composition.

M9.6.2 tests verify identity transform ownership, transformed points, observer
positions and representation anchors, one shared transform across multiple
observers, transform validation, and canonical identity queries.

M9.6.3 tests verify actor matrices after non-identity builds, synchronized
model-and-actor updates on attached layers, deferred rendering, preservation
of translation through the global scale control, exclusion of centered
celestial geometry, and removal of the parallel raw-actor scale group.

M9.6.4 tests verify scale changes with retained translation, restoration of
nominal surface placement, exact semantic-anchor alignment at the origin,
synchronized actor matrices, and validation before placement state changes.

M9.7.1 tests verify attached addition of a second observer without rebuilding
Earth, ordered observer and actor ownership, shared transform application,
inherited hidden-layer state, and deferred rendering.

M9.7.2 tests verify semantic antipode construction, rejection for observers
without geographic metadata, opposite positions and ENU axes, distinct
oriented ideal horizons, and two complete compositions sharing one Earth and
one transformed local-cartoon layer.

M9.7.3 tests verify point-representation anchors, one-actor rendering and
radius validation, attached replacement with retained observer and horizon,
stale-actor removal, shared-transform application, transformed anchor queries,
and deferred rendering.

M9.7.4 tests verify transformed named-anchor origins, fixed target positions,
anchor resolution after representation replacement, multiple observers
sharing one target, style and visibility preservation, and invalid observer or
anchor handling.

M9.8.1 tests verify the stable orientation against the accepted nonpolar
matrix, corrected-site and north-pole placement, orthonormal right-handed
polar matrices, inclusive geographic-pole support, inconsistent-frame
rejection, scene propagation of display North, and unchanged Earth actor
lifecycle.

M9.8.2 tests verify Earth-fixed-to-display observer conversion, alignment of
the selected site with display Zenith and North, geographic and radius
validation, antipodal display positions, independent finite platforms,
centered oppositely oriented ideal horizons, one shared Earth and transform,
and lifecycle construction of both platform and point-representation actors.

M9.8.3 closes the M9 gate with a real off-screen PyVista render of one shared
Earth, two antipodal point representations, two independently positioned
finite platforms, and both centered ideal-horizon display surfaces. The test
uses a local untextured sphere so it exercises meshes, actors, transforms,
screenshot export, and cleanup without network or texture-cache dependence.
It verifies that the exported image is nonempty, the observers remain
antipodal, and the ideal-horizon surfaces remain outside the transformed local
cartoon. Together with the canonical interactive run, this satisfies the M9
interactive-and-batch-render gate.

All M9 gate criteria are now covered: the characterized canonical composition
is preserved; Earth orientation supports ordinary, polar, and antipodal
sites; geographic ENU frames convert explicitly to display space; semantic
observers, representations, anchors, platforms, and horizons remain distinct;
multiple observers share one Earth and transform; decorations are
interchangeable; local visibility and placement are graph-managed;
`ActorScaleGroup` is retired; and interactive and batch rendering succeed.

The repository does not automatically execute the canonical interactive
example, and texture pixels are not regression-tested across platforms. The
canonical visual run therefore remains the manual textured-Earth acceptance
check, while the automated M9 batch test is deliberately texture-independent.

M10.1 tests verify direction normalization, derived shell position, immutable
radius replacement, marker derivation with shared style and visibility, and
validation of target identity, direction, radius, style, and visibility.

M10.2 tests verify the North-through-East convention, vertical-circle foot,
positive and negative altitude-arc direction, altitude and azimuth endpoints,
target-direction dependence, centered shell radius, degenerate zero spans,
undefined polar azimuth, and target, frame, and sampling validation.

M10.3 tests verify ordered component ownership, target-marker linkage,
convention-correct label text and associations, caller-supplied styles and
arrowheads, optional labels, independent zero-span omission, actual off-screen
actor construction, validation, and finite radial annotation offsets.

M10.4 tests verify longitude and declination recovery, equatorial and target
endpoints, positive and negative declination direction, diagrammatic-longitude
naming, right-ascension hours and required origin description, independent
zero-span omission, polar rejection, and convention, target, frame, and
sampling validation.

M10.5 tests verify ordered ownership, target-marker linkage, diagrammatic and
right-ascension label units and conventions, associations, caller-supplied
styles and arrowheads, optional labels, independent zero-span omission,
off-screen actor construction, validation, and finite radial label offsets.

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

1. The celestial axis still bypasses the graph.
2. `CelestialScene` has too many responsibilities.
3. Rendering lifecycle responsibilities have not yet moved into a separate
   render context.
4. Controls use fixed pixel footprints and object-specific panel classes.
5. Restore-default behavior has no model-level definition.
6. Pixel output is not regression-tested across platforms.
7. Equatorial coordinates are diagrammatic, not time-aware.
8. Optional platform decorations are not yet selectable through canonical
   scene construction or interactive controls.
9. Directly rebuilding attached observer context below `LocalCartoonLayer`
   does not yet refresh the parent's flattened actor cache; attached
   representation replacement must use the layer-level operation.

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
and a local-cartoon layer integrating one shared Earth with named observer
compositions in the canonical scene. Each composition has renderer-neutral
ideal-horizon geometry independent of local-cartoon scale and placement.

It does not own or consume a Wenu `Observer`, `CelestialSphere`, Wenu layers,
catalogs, apparent positions, or renderer-neutral Wenu primitives. Horizon A
must first make the standalone product coherent, tested, reproducible, and
extensible.
