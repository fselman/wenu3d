# Wenu3D Target Architecture — Horizon A

**Version:** 1.2
**Date:** 2026-07-31
**Status:** Revised post-M8 target with distinct celestial and local-cartoon
geometry domains

## 1. Purpose

Horizon A produces a dependable standalone Wenu3D product with:

- correct astronomical geometry;
- interactive inspection;
- publication-quality deterministic output;
- reusable controls;
- first-class annotations;
- incremental scientific-object extension;
- finite-scale astronomical geometry illustrations;
- a clean future boundary for a Wenu renderer.

It does not implement the Wenu adapter.

## 2. Product priorities

Wenu3D is a renderer and composition toolkit, not a planetarium, catalog
manager, or ephemeris engine. Priorities are:

1. scientific correctness;
2. reproducibility;
3. visual clarity;
4. maintainability;
5. ease of use;
6. extensibility;
7. interactive performance.

## 3. Architectural principles

### Repository authority

The repository is the source of truth. Work follows the migration path in
small, reviewable changes.

### Working milestone boundaries

After every major milestone:

- installation succeeds;
- tests pass;
- the canonical La Ligua example runs;
- interactive controls work;
- deterministic image export succeeds;
- documentation and public behavior agree.

### Scientific model before rendering

Geometry produces renderer-neutral arrays or records. PyVista-specific work is
performed by renderable scene objects.

### Composition

```text
CelestialScene
    SceneGraph
        Layer
            SceneObject
                geometry
                style
                renderer handles
```

The graph is the scene model; parallel raw-actor registries are avoided.

### UI observes objects

Controls manipulate public object capabilities. Scientific objects do not
construct widgets.

### No premature Wenu dependency

Horizon A does not import Wenu. Simple arrays and data records form the future
adapter boundary.

### Complementary geometric domains

Horizon A composes two distinct but compatible geometric domains.

The **abstract celestial domain** represents directions and angular geometry.
The celestial sphere is a spherical display surface with arbitrary rendered
radius. Stars are scientifically directions; coordinate grids, great and
small circles, coordinate arcs, observer-specific ideal horizons, and optional
center-to-target direction lines are centered on the celestial origin. Their
geometry does not depend on the scale or placement of the cartoon Earth.

The **finite local-cartoon domain** contains explanatory objects such as Earth,
observer representations, platforms or vehicles, decorations, and finite
observer-to-target sight lines. They have explicit displayed positions and
deliberately exaggerated relative scales. They explain observer location and
orientation without redefining celestial coordinates.

A celestial target retains a unit direction and derives a finite displayed
position on the shell. Spherical constructions consume the direction. An
explicit convergence or parallax illustration may use the displayed position
as the common endpoint of finite cartoon sight lines.

Changing local-cartoon scale or placement must not alter the shell, target
direction, displayed marker, coordinate curves, or centered ideal planes. The
future Wenu adapter may supply directions directly and must not silently treat
a displayed shell position as a physical finite distance.

## 4. Target components

```text
CelestialScene
├── SceneGraph
│   ├── CelestialShellLayer
│   ├── ReferenceGridLayer
│   ├── ScientificIllustrationLayer
│   ├── LocalCartoonLayer
│   │   ├── EarthObject
│   │   └── ObserverComposition(s)
│   └── AnnotationLayer
├── RenderContext
│   ├── PyVista Plotter
│   ├── Camera
│   └── lifecycle and export
├── ControlManager
│   ├── common controls
│   ├── grid controls
│   └── layout
└── SceneStyle
```

Names may evolve incrementally; responsibilities and dependency direction are
authoritative.

## 5. Scene and render context

`CelestialScene` is the user-facing composition root. It owns metadata,
diagrammatic frames, graph, render context, style, optional controls, and
convenience methods. It coordinates components but does not implement
object-specific meshes or materials.

A small `RenderContext` owns:

- plotter creation;
- actor addition and removal;
- render requests;
- camera configuration;
- interactive/off-screen mode;
- screenshots and export;
- resource cleanup.

The public lifecycle distinguishes:

- `show()` for interaction;
- `render()` for build/update;
- `save(path, ...)` for deterministic output;
- `close()` for cleanup.

## 6. Scene graph and lifecycle

The graph provides ordered named layers, add/get/remove/iteration, predictable
render order, and safe teardown.

Every `SceneObject` has:

- stable name;
- visibility and opacity;
- style;
- attachment/build;
- supported updates;
- removal;
- owned renderer handles.

Lifecycle is:

```text
created → attached → updated → detached
```

Rebuilding never leaves duplicate actors or callbacks.

A layer owns ordered children, group state, optional transforms, and
capabilities for controls. Temporarily hiding a layer does not destroy the
individual visibility choices of its children.

## 7. Scientific geometry

Renderer-neutral primitives produce NumPy data and may include, as concrete
illustrations require:

- points;
- finite-position markers;
- line segments and sight lines;
- polylines;
- meridians and parallels;
- great and small circles;
- partial spherical arcs;
- vectors;
- planes;
- spheres.

`SphericalFrame` remains a validated orthonormal basis. Documentation clearly
distinguishes diagrammatic frames from time-aware astronomical coordinates.

Objects should accept sampled Cartesian vectors or equivalent simple geometry
so a future Wenu adapter can translate Wenu layers without changing PyVista
rendering internals.

Scientific records distinguish a target direction from its derived displayed
shell position. Centered celestial planes and curves use the celestial origin.
Local-cartoon objects use an explicit composition transform. Parallel
orientation does not imply common position or common scientific meaning.

## 8. Renderable objects and layers

A general curve object renders supplied sampled geometry with color, opacity,
width, and optional arrowheads. Complete grid curves and partial coordinate
arcs use the same rendering path. `GridCurveObject` may remain a semantic
specialization and should reuse general curve behavior when the general object
exists.

First-class marker, segment, vector, curve, and surface objects support stars,
poles, finite sight lines, directions, coordinate arcs, axes, planes, Earth,
and the shell. Styling such as a large golden star or a thicker coordinate arc
is object state, not a separate object type.

A renderer-neutral `SphericalArc` represents a sampled portion of a great or
small circle. It has an explicit frame, radius, start and end parameters, and
sampling. Coordinate-specific helpers construct these arcs without
implementing separate renderers.

An illustration layer groups related markers, curves, rays, surfaces, and
annotations. Grouping makes a complete scientific explanation independently
visible and removable while retaining the lifecycle of each child.

The celestial shell owns its mesh, material refresh, style, and camera
callback lifecycle.

Earth and observer compositions form a `LocalCartoonLayer` with coherent
visibility and transform state. One Earth may contain multiple geographically
placed observers; an observer composition does not own or duplicate Earth.
`ActorScaleGroup` is retired once the model-aware transform path replaces it.

### Earth-fixed geometry

One world Cartesian frame and one Earth orientation apply to the complete
scene. Geographic longitude and latitude map each observer to a position on
that Earth and to a validated local East-North-Zenith frame. Adding another
observer never reorients or duplicates Earth.

Polar sites are supported with a documented longitude-based local-meridian
convention. Construction must not divide by `cos(latitude)` at the geographic
poles.

### Semantic observers and replaceable representations

An `Observer` is renderer-neutral scientific geometry: identity, geographic
location or explicit finite position, and a validated local frame. An
`ObserverRepresentation` is optional drawable geometry such as the existing
stick figure, a navigator, an instrument, an observatory, or no visible person.

An `ObserverComposition` associates one observer with one representation,
optional platform or vehicle context, decorations, annotations, and named
anchors. Representation-specific anchors such as feet or eye are supplied by
the representation through stable semantic names; they are not silently
treated as intrinsic properties of the abstract observer.

Higher-level operations request an anchor by name and do not calculate
mesh-specific offsets or manipulate individual actors.

### Local-cartoon transforms

A local-cartoon transform contains translation and uniform scale. It is
renderer-neutral and is the single source of truth for both rendered actors
and queries of transformed positions or semantic anchors. Actor-only
transformations that leave scientific geometry unchanged are not valid.

The containing `LocalCartoonLayer` may transform Earth and all observer
compositions coherently for scale-comparison scenes. Individual observer
compositions may manage their own representation and decoration state without
moving the shared Earth independently.

Supported presentation modes may include surface placement and aligning a
selected observer anchor with the celestial origin. These modes transform only
the finite local cartoon; celestial geometry remains fixed.

### Multiple observers and finite sight lines

Each observer has a finite displayed position and a local frame derived from
its position and orientation on the single shared Earth. A scene may contain
more than one observer, including observers at antipodal sites.

A finite cartoon sight line connects a named observer anchor to a target's
displayed shell position. Two observers viewing one displayed star therefore
create two segments sharing one finite marker endpoint. This is an explicitly
requested cartoon construction, not the default meaning of the celestial
sphere.

An optional centered direction line joins the celestial origin to the same
marker and represents the abstract direction. Scale comparisons may transform
Earth and its observers together while leaving all celestial geometry fixed.

### Horizon planes and decorations

Each observer may define an **ideal horizon** through the celestial origin,
perpendicular to that observer's zenith. Multiple observers may therefore have
distinct ideal horizons and horizontal frames.

A **local platform** belongs to an observer composition. At a surface site it
may be tangent to the cartoon Earth. It is parallel to its observer's ideal
horizon but normally has a different center; it may coincide with the ideal
horizon only in an explicit observer-anchor-at-origin presentation.

The platform has configurable extent, opacity, color, edge treatment, and
visibility. Its geometry is independent from optional decoration.

Supported concrete decorations include:

- North, East, South, and West direction lines and inscriptions;
- a compass rose;
- a Nainoa Thompson navigation plot supplied as validated vector geometry or
  an explicit image/texture when appropriate.

These are interchangeable decorations of one local-platform object, not three
independent platform implementations. Decorations do not define the ideal
horizon.

## 9. Grid architecture

A grid remains a layer of individually addressable curves with:

- meridian and parallel families;
- major/minor classification;
- family and curve visibility;
- associated annotations;
- grid style;
- renderer-neutral frame geometry.

Both APIs are supported:

```python
horizontal = scene.add_horizontal_grid(...)
```

```python
horizontal = GridLayer(...)
scene.add(horizontal)
```

The convenience method constructs, adds, and returns the same `GridLayer`.

## 10. Annotations

Annotations are scene objects containing:

- text;
- 3D anchor;
- optional offset;
- optional leader or arrow;
- style and visibility;
- optional association with another object.

An `AnnotationLayer` supports add/remove/update, group visibility, defaults,
and safe rebuilding when VTK text properties are immutable.

Horizon A supports grid labels, named points, titles, direction labels, and
manual callouts. Curve visibility and annotation visibility remain distinct,
with an explicit association policy.

Automatic global collision avoidance is not required initially.

### Coordinate illustrations

Horizontal-coordinate illustrations may combine:

- a star marker;
- an altitude arc along the star's vertical circle from the horizon to the
  star;
- an azimuth arc on the horizon from North to the foot of that vertical
  circle;
- labels and optional arrowheads.

Equatorial-coordinate illustrations may combine:

- a star marker;
- a declination arc along the star's hour circle from the celestial equator to
  the star;
- a right-ascension arc along the celestial equator from a defined origin to
  the hour circle;
- labels and optional arrowheads.

Absolute right ascension is shown only when the equatorial zero direction is
scientifically defined. A diagrammatic equatorial longitude must be described
as such when time, sidereal orientation, or epoch is absent.

Coordinate curves always use centered spherical geometry and target
directions, never displaced cartoon-observer positions. Parallax and
convergence scenes explicitly combine the two domains; exaggerated finite
sight lines do not arise implicitly from ordinary coordinate helpers.

## 11. Controls

A `ControlManager` owns widget lifetime, layout, state synchronization, panel
registration, and batched renders.

Reusable controls operate on capabilities:

- visibility;
- opacity;
- scale;
- color where reliable;
- annotation visibility and size;
- camera reset.

Grid panels retain whole-grid, family, and individual-curve controls.
High-level callers do not calculate raw pixel positions. Layout choices must
be based on verified PyVista capabilities and real scene sizes.

## 12. Styles

Styles are composed by responsibility as parameters accumulate:

```text
SceneStyle
├── shell
├── grids
├── local scene
├── annotations
├── controls
└── camera/output
```

Defaults are publication-oriented and scientifically meaningful. User
overrides are explicit and reproducible. Hard-coded constants move into style
objects only as their owning object is formalized.

## 13. Transparency policy

Objects or layers declare or inherit:

- nominal surface placement;
- inside/on/outside-shell relationship;
- front/far-side visibility intent;
- label occlusion behavior;
- translucent render order.

The policy is established through canonical scientific illustrations rather
than a speculative general rendering engine.

## 14. Ease-of-use target

Common use:

```python
scene = CelestialScene.for_observer_diagram(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
)
scene.add_horizontal_grid()
scene.add_equatorial_grid()
scene.add_default_controls()
scene.save("la_ligua.png")
```

Advanced users retain explicit layer and control composition. Convenience
does not conceal coordinate conventions.

Concrete illustration constructors may provide explicit local placement and
scale comparisons without hiding their geometry:

```python
local = scene.local_cartoon
local.place_on_surface(observer="navigator")
local.set_scale(0.05)

local.place_observer_anchor_at_origin(
    observer="navigator",
    anchor="feet",
)
```

Representation replacement remains independent:

```python
navigator.set_representation(BoatNavigator(...))
```

Specialized convergence or parallax constructors may combine multiple
observers, one celestial target, finite sight lines, and an optional centered
direction line while exposing every component and convention.

## 15. Verification

Unit tests cover vector and frame mathematics, curve geometry, edge cases,
validation, lifecycle, and state propagation.

Off-screen smoke tests verify scene construction, image output, and absence of
actor accumulation. Pixel-perfect comparisons are used sparingly because VTK
varies by platform.

Scientific illustration tests verify endpoint relationships, scale ratios,
observer frames, spherical-arc endpoints, and coordinate conventions without
depending on pixel comparisons.

One La Ligua example is the canonical integration example and remains runnable
at every milestone. Additional examples demonstrate genuinely distinct
scientific capabilities.

## 16. Public API

The package root exports stable user-facing types. Internal helpers remain
available from their modules but are not automatically promoted.

When an API change is necessary, documentation and examples change in the
same milestone, with compatibility preserved where practical.

## 17. Horizon B compatibility

Horizon A prepares this future boundary:

```text
Wenu Observer + CelestialSphere + Layers
                    ↓
             Wenu3D adapter
                    ↓
      renderer-neutral Wenu3D objects
                    ↓
          PyVista RenderContext
```

Wenu supplies astronomical transformations and apparent coordinates. The
adapter preserves names, visibility, style intent, and annotations, and
reports unsupported layers explicitly.

Wenu celestial inputs may be directional. The adapter maps them into the
abstract celestial domain and derives displayed shell positions only for
rendering. It must not silently assign physical finite distance to a target
because cartoon sight lines can terminate at its displayed marker.

The adapter should live in Wenu or an optional integration module so standalone
Wenu3D remains lightweight.

## 18. Completion criteria

Horizon A is complete when:

1. documentation and examples use one coherent API;
2. scientific and lifecycle tests pass;
3. the canonical scene works interactively and in batch mode;
4. objects build, update, hide, show, remove, and rebuild safely;
5. annotations are first-class;
6. controls are reusable and layout-managed;
7. shell and local objects participate in the scene model;
8. deterministic publication-quality export works;
9. coordinate and transparency conventions are documented;
10. reusable markers, segments, partial curves, and planes support the
    documented coordinate, horizon, convergence, and parallax illustrations;
11. celestial geometry remains independent of local-cartoon scale and
    placement;
12. targets distinguish direction from displayed shell position;
13. one shared Earth supports multiple geographic observers and valid local
    frames, including polar and antipodal sites;
14. semantic observers, replaceable representations, and named anchors remain
    separate responsibilities;
15. ideal horizons and decorated local platforms remain separate concepts;
16. model-aware local transforms keep rendered and queried geometry aligned;
17. a Wenu adapter can begin without restructuring the renderer.
