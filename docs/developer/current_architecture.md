# Wenu3D Current Architecture

**Version:** 0.7
**Date:** 2026-07-31
**Status:** Description of `feature/interactive-grid-controls` through M7

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
| `curves.py` | Sampled meridians and parallels |
| `camera.py` | Validated, renderer-neutral camera state |
| `rendering.py` | Low-level PyVista tubes and arrows |
| `scene_object.py` | Base drawable object and actor state |
| `layer.py` | Composite collection of scene objects |
| `grid.py` | Grid styles, curves, and layers |
| `annotations.py` | Annotation records, objects, styles, and layers |
| `controls.py` | Managed grid, annotation, and global controls |
| `shell.py` | Celestial-shell mesh, material, presence, and callback lifecycle |
| `earth.py` | Earth mesh loading and orientation |
| `observer.py` | Tangent plane and observer figure |
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

`Meridian` and `Parallel` are immutable, renderer-neutral sampled geometry
objects. This is the cleanest existing separation between scientific geometry
and PyVista.

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

The grid and celestial shell follow this object model. Earth, plane, observer,
arrows, and axis are still created directly by `CelestialScene`.
`ActorScaleGroup` is consequently a second actor-management mechanism outside
the graph.

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

Earth orientation, tangent plane, observer, arrows, and celestial axis are
also constructed directly by `CelestialScene`. Their styling contains several
hard-coded values. Earth orientation divides by `cos(latitude)` and is
singular at the geographic poles.

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

## 11. Verification state

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

The repository does not yet automatically execute the canonical interactive
example or verify Earth orientation.

## 12. Strengths

1. Compact, understandable spherical geometry.
2. Reusable `SphericalFrame`.
3. Working `Scene → Layer → SceneObject` lifecycle for grids and the shell.
4. Individually addressable grid curves.
5. First-class annotations through the object model.
6. Managed controls with layout, synchronization, and render batching.
7. Explicit reproducible camera and rendering lifecycle.
8. Configurable off-screen RGB and transparent RGBA export.
9. Small codebase suitable for incremental improvement.

## 13. Liabilities

1. Earth and most local scene elements still bypass the graph.
2. `CelestialScene` has too many responsibilities.
3. Rendering lifecycle responsibilities have not yet moved into a separate
   render context.
4. Controls use fixed pixel footprints and object-specific panel classes.
5. Restore-default behavior has no model-level definition.
6. Pixel output is not regression-tested across platforms.
7. Equatorial coordinates are diagrammatic, not time-aware.

## 14. Current boundary

Wenu3D currently owns diagrammatic geometry, PyVista rendering, fixed scene
composition, first-class annotations, managed interactive controls, a
reproducible camera, deterministic interactive/off-screen rendering,
configurable image export, explicit cleanup, and a lifecycle-managed celestial
shell.

It does not own or consume a Wenu `Observer`, `CelestialSphere`, Wenu layers,
catalogs, apparent positions, or renderer-neutral Wenu primitives. Horizon A
must first make the standalone product coherent, tested, reproducible, and
extensible.
