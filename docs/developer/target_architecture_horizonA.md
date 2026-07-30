# Wenu3D Target Architecture — Horizon A

**Version:** 1.0  
**Date:** 2026-07-30  
**Status:** Target for the standalone scientific-illustration product

## 1. Purpose

Horizon A produces a dependable standalone Wenu3D product with:

- correct astronomical geometry;
- interactive inspection;
- publication-quality deterministic output;
- reusable controls;
- first-class annotations;
- incremental scientific-object extension;
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

## 4. Target components

```text
CelestialScene
├── SceneGraph
│   ├── CelestialShellLayer
│   ├── ReferenceGridLayer
│   ├── LocalSceneLayer
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

## 8. Renderable objects and layers

A general curve object renders supplied geometry with color, opacity, and
width. `GridCurveObject` may remain a semantic specialization and should reuse
general curve behavior when a second concrete curve family justifies it.

First-class point, vector, and surface objects support poles, directions,
axes, markers, planes, Earth, and the shell.

The celestial shell owns its mesh, material refresh, style, and camera
callback lifecycle.

Earth, plane, observer, and direction arrows form a composite local layer with
visibility and group scale. `ActorScaleGroup` is retired once that layer fully
replaces it.

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

## 15. Verification

Unit tests cover vector and frame mathematics, curve geometry, edge cases,
validation, lifecycle, and state propagation.

Off-screen smoke tests verify scene construction, image output, and absence of
actor accumulation. Pixel-perfect comparisons are used sparingly because VTK
varies by platform.

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
10. a Wenu adapter can begin without restructuring the renderer.
