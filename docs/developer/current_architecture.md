# Wenu3D Current Architecture

**Version:** 0.1  
**Date:** 2026-07-30  
**Status:** Description of `feature/interactive-grid-controls`

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
| `rendering.py` | Low-level PyVista tubes and arrows |
| `scene_object.py` | Base drawable object and actor state |
| `layer.py` | Composite collection of scene objects |
| `grid.py` | Grid styles, curves, and layers |
| `controls.py` | Interactive grid controls |
| `earth.py` | Earth mesh loading and orientation |
| `observer.py` | Tangent plane and observer figure |
| `local_group.py` | Scaling a raw group of actors |
| `labels.py` | Legacy labels; currently inconsistent with `grid.py` |
| `style.py` | Flat scene styling |
| `scene.py` | Composition, shell, camera, rendering, grids, and controls |

`examples/la_ligua_interactive_grids.py` uses the current API.
`examples/la_ligua_grids.py` and parts of the README use an earlier API.

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

`SceneObject` owns a name, visibility, opacity, and actors. Subclasses implement
`build(plotter)`.

`Layer` is a composite `SceneObject`. It owns children and delegates building
and visibility, while also duplicating child actor references in its own actor
list.

`SceneGraph` is a name-indexed dictionary of layers with duplicate-name
protection and lookup. It has no remove, ordering, iteration, or teardown API.

Only the grid system follows this object model. The shell, Earth, plane,
observer, arrows, and axis are created directly by `CelestialScene`.
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

## 6. Controls

`GridControlPanel` provides three visibility levels:

1. complete grid;
2. meridian or parallel family;
3. individual curve.

Family hiding preserves individual selections. Global sliders control shell
presence and local-object scale.

Current limitations are manual pixel positioning, fixed vertical layout,
grid-specific control logic, no annotation controls, and no automatic
synchronization when object state changes outside widgets.

## 7. Celestial shell and local illustration

The shell is a high-resolution sphere with camera-dependent per-vertex RGBA
values, limb emphasis, and two specular sources. A camera interaction callback
refreshes it. The implementation and callback lifecycle are embedded in
`CelestialScene`.

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

There is no separate API for deterministic batch rendering, headless export,
transparent backgrounds, camera presets, object removal, safe rebuilding, or
resource cleanup.

The `render` argument accepted by visibility methods does not itself trigger a
render. Rebuilding can accumulate actors because old actors are not removed
from the plotter.

## 10. Annotation state

`labels.py` imports `GridLabel`, but current `grid.py` no longer defines it.
Annotations are therefore stale, not part of the scene graph, and absent from
the active example.

## 11. Verification state

There is no committed automated test suite. The repository does not
automatically verify:

- frame geometry and handedness;
- coordinate conversion;
- curve sampling;
- Earth orientation;
- lifecycle and state propagation;
- repeated builds;
- off-screen rendering;
- canonical example execution.

## 12. Strengths

1. Compact, understandable spherical geometry.
2. Reusable `SphericalFrame`.
3. Appropriate `Scene → Layer → SceneObject` direction.
4. Individually addressable grid curves.
5. Separation of grid controls from the scene class.
6. Small codebase suitable for incremental improvement.

## 13. Liabilities

1. Documentation and examples describe conflicting APIs.
2. Annotation code is broken and disconnected.
3. Most scene elements bypass the graph.
4. `CelestialScene` has too many responsibilities.
5. Actor lifecycle is undefined.
6. Rendering semantics are inconsistent.
7. Controls do not scale automatically.
8. No scientific or rendering tests exist.
9. Equatorial coordinates are diagrammatic, not time-aware.

## 14. Current boundary

Wenu3D currently owns diagrammatic geometry, PyVista rendering, fixed scene
composition, grid controls, and screenshots.

It does not own or consume a Wenu `Observer`, `CelestialSphere`, Wenu layers,
catalogs, apparent positions, or renderer-neutral Wenu primitives. Horizon A
must first make the standalone product coherent, tested, reproducible, and
extensible.
