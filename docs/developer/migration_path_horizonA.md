# Wenu3D Migration Path — Horizon A

**Version:** 1.1
**Date:** 2026-07-30  
**Status:** Revised post-M6 incremental migration path
**From:** `current_architecture.md`  
**To:** `target_architecture_horizonA.md`

## 1. Central constraint

> Wenu3D must be working after every major milestone.

This is not a long architectural rewrite. Every milestone delivers a coherent
improvement that remains useful if later development pauses.

## 2. Global rules

Before each milestone, inspect the active branch, affected files, tests, and
examples. The repository overrides this document if they conflict.

Each commit should address one concern, preserve a usable package, avoid
unrelated cleanup, and include tests when behavior changes.

At every major milestone:

```text
[ ] clean installation succeeds
[ ] unit tests pass
[ ] rendering smoke test passes
[ ] canonical La Ligua example runs
[ ] interactive controls work
[ ] deterministic image export succeeds
[ ] public API, README, and examples agree
[ ] generated output is not committed accidentally
```

Before test and batch infrastructure exists, equivalent checks are manual.

Prefer compatible changes. When an API must change, explain the contradiction
and update all examples and documentation in the same milestone.

Do not introduce abstractions without a concrete illustration need. Horizon A
does not import Wenu.

## 3. Milestones

| Milestone | Outcome |
|---|---|
| M0 | Architecture documents |
| M1 | One coherent runnable baseline |
| M2 | Scientific and rendering verification |
| M3 | Reliable object lifecycle |
| M4 | First-class annotations |
| M5 | Reusable scalable controls |
| M6 | Reproducible rendering and export |
| M7 | Celestial shell as a scene object |
| M8 | General scientific illustration primitives |
| M9 | Observer, Earth, and horizon composition |
| M10 | Coordinate and parallax illustrations |
| M11 | Horizon A release candidate |

M0 through M6 are completed history and remain unchanged by version 1.1. The
post-M6 path is expanded because concrete illustration requirements now
justify reusable finite markers, sight lines, partial spherical arcs, multiple
observers, decorated horizon planes, and scale-comparison scenes.

## 4. M0 — Architectural baseline

Deliver:

- `current_architecture.md`;
- `target_architecture_horizonA.md`;
- `migration_path_horizonA.md`.

Do not change runtime behavior. Completion requires agreement with the active
branch and a clear separation between Horizon A and future Wenu integration.

## 5. M1 — Coherent runnable baseline

### Goal

Present exactly one supported current API.

### Work

1. Make `la_ligua_interactive_grids.py` the initial canonical example.
2. Reconcile README instructions with `make_*_grid()`, `scene.add()`,
   `add_grid_controls()`, and `add_global_controls()`.
3. Migrate or remove the obsolete `la_ligua_grids.py`.
4. Resolve the broken `labels.py` import minimally, without prematurely
   designing M4.
5. Verify package-root exports.

### Gate

- clean editable install;
- all supported examples run;
- README code runs;
- every packaged module imports;
- canonical scene renders and controls respond.

### Working product

A truthful, runnable prototype with one entry path.

## 6. M2 — Verification foundation

### Goal

Protect scientific geometry and rendering before further restructuring.

### Work

Add tests for:

- vector normalization and zero rejection;
- frame orthogonality and handedness;
- known spherical directions and broadcasting;
- meridian and parallel geometry;
- latitude, pole, radius, sampling, and duplicate-value edge cases;
- initial visibility and opacity;
- minimal off-screen image creation.

Validation should define behavior without speculative complexity.

### Gate

- unit suite passes;
- off-screen test produces a nonempty image;
- canonical interactive example still works;
- tested scientific conventions are documented.

### Working product

A runnable prototype with a protected mathematical foundation.

## 7. M3 — Reliable object lifecycle

### Goal

Make the existing object path safe before moving more objects into it.

### Work

1. Define attach/build, update, detach/remove, and safe rebuild.
2. Make render requests real and consistent; remove misleading unused
   `render` behavior.
3. Remove old actors and callbacks during rebuild.
4. Add only necessary graph operations: ordered iteration, remove, and clear.
5. Define layer hiding versus retained child selections.
6. Preserve current grid appearance and controls.

### Gate

- lifecycle tests pass;
- repeated build/remove/rebuild does not increase actor count;
- grid controls still work;
- interactive and off-screen scenes render.

### Working product

A trustworthy object foundation for new features.

## 8. M4 — First-class annotations

### Goal

Restore labels and add useful scientific callouts through the object model.

### Work

1. Add an annotation record with text, 3D anchor, offset, style, visibility,
   and optional association.
2. Add annotation objects and an annotation layer.
3. Restore separately selected grid labels and configurable anchors.
4. Add at least one manual scientific callout to the canonical example.
5. Add annotation visibility and size controls.

Do not implement global collision avoidance or a general layout engine.

### Gate

- annotation tests pass;
- grid labels and a manual callout render;
- labels hide and resize correctly;
- interactive and batch output succeed.

### Working product

A genuinely annotated scientific teaching illustration.

## 9. M5 — Reusable scalable controls

### Goal

Remove caller-managed widget coordinates and support additional layers.

### Work

1. Add a control manager for widget lifetime, layout, state synchronization,
   panel registration, and batched renders.
2. Reuse controls for visibility, opacity, scale, and annotations.
3. Preserve grid, family, and individual-curve hierarchy.
4. Base layout on verified PyVista capabilities.
5. Add reset-camera and restore-default actions if reliable.

### Gate

- canonical example calculates no panel coordinates;
- supported window sizes remain usable;
- widgets reflect initial and updated object state;
- batch rendering remains independent of controls.

### Working product

An interactive illustration whose controls can grow with the scene.

## 10. M6 — Reproducible rendering and export

### Goal

Separate interactive exploration from deterministic output.

### Work

Provide:

- `show()` for interaction;
- `render()` for build/update;
- `save()` for image output;
- `close()` for cleanup;
- explicit camera state;
- dimensions and background options;
- transparent background when reliable.

Repeated calls must not duplicate titles, actors, or widgets.

### Gate

- a documented script exports without opening a window;
- repeated saves do not accumulate actors;
- explicit camera state reproduces the view;
- interactive controls still work.

### Working product

A tool for both exploration and publication-oriented scripted output.

## 11. M7 — Celestial shell scene object

### Goal

Move the largest visual special case out of `CelestialScene`.

### Work

Move shell mesh, material refresh, style, and camera callback lifecycle into an
explicit shell object or layer. Preserve appearance before attempting visual
improvements. Expose stable visibility and presence controls.

### Gate

- appearance remains acceptable;
- callbacks do not duplicate after rebuild;
- sphere controls work;
- canonical interactive and batch renders succeed.

### Working product

A reusable shell governed by the same lifecycle as other objects.

## 12. M8 — General scientific illustration primitives

### Goal

Provide the smallest reusable object vocabulary required by concrete
astronomical illustrations.

### Work

1. Add a finite-position marker object suitable for stars, poles, and named
   points.
2. Add line-segment and sight-line objects with explicit Cartesian endpoints.
3. Add a general sampled-curve object with width, color, opacity, visibility,
   and optional arrowheads.
4. Add renderer-neutral partial great-circle and small-circle geometry,
   including validated endpoints and sampling.
5. Add a general plane or surface object needed by observer-relative horizon
   illustrations.
6. Add an illustration layer for grouping related primitives and annotations.
7. Reuse the established `SceneObject` lifecycle; do not introduce
   coordinate-specific renderers.

### Gate

- marker, segment, curve, arc, and plane geometry tests pass;
- all primitives build, hide, show, detach, and rebuild without actor
  accumulation;
- a large golden star is produced through marker style rather than a special
  renderer;
- thick partial arcs are produced through curve style;
- interactive and batch renders succeed.

### Working product

A reusable finite scientific-illustration vocabulary independent of any one
coordinate system.

## 13. M9 — Observer, Earth, and horizon composition

### Goal

Bring local astronomical geometry into the scene graph and support more than
one observer.

### Work

1. Make Earth an explicit scene object with preserved texture and axis
   orientation.
2. Make an observer an explicit object with a finite Cartesian position and
   validated observer-relative frame.
3. Support multiple observers, including observers on opposite sides of
   Earth.
4. Make the tangent horizon an observer-relative semi-opaque plane.
5. Separate horizon geometry from interchangeable decorations.
6. Provide North, East, South, and West lines and inscriptions.
7. Provide a compass-rose decoration.
8. Provide a Nainoa Thompson navigation decoration from validated vector
   geometry or an explicit texture.
9. Bring observer figures, direction arrows, planes, axes, and related
   annotations into a local scene layer.
10. Retire `ActorScaleGroup` once fully replaced.
11. Define or reject geographic-pole behavior.
12. Move hard-coded style only as each owning object is formalized.

### Gate

- observer position and local-frame tests pass;
- Earth orientation is verified for La Ligua and reference sites;
- two observers can coexist without special-case scene code;
- horizon geometry follows its observer;
- cardinal, compass-rose, and navigation decorations are interchangeable;
- local visibility and scale work through the layer;
- all local elements appear in the graph;
- interactive and batch renders succeed.

### Working product

Earth, observers, and decorated local horizons follow the common object
architecture.

## 14. M10 — Coordinate and parallax illustrations

### Goal

Assemble the reusable objects into complete scientifically meaningful
illustrations.

### Work

1. Add a finite star point on the celestial sphere with configurable marker
   style.
2. Add horizontal-coordinate composition helpers:
   - altitude arc along the star's vertical circle from horizon to star;
   - azimuth arc on the horizon from North to the vertical-circle foot;
   - associated labels and optional arrowheads.
3. Add equatorial-coordinate composition helpers:
   - declination arc from the equator to the star along its hour circle;
   - right-ascension arc along the equator from a scientifically defined
     origin to the hour circle;
   - associated labels and optional arrowheads.
4. Keep diagrammatic equatorial longitude distinct from absolute right
   ascension when time or sidereal orientation is absent.
5. Add two finite sight lines from two observer positions to one common star
   endpoint on the celestial sphere.
6. Add paired large-Earth and small-Earth configurations. Hold the celestial
   sphere and star fixed while scaling Earth, observer positions, horizon
   planes, and observer separation together.
7. Demonstrate how sight-line convergence becomes visually negligible when
   the observer baseline is small compared with star distance.
8. Preserve direct access to every marker, curve, line, plane, annotation, and
   style used by the convenience compositions.

### Gate

- altitude, azimuth, declination, and right-ascension arc endpoints are
  geometrically verified;
- coordinate labels state the convention actually used;
- both sight lines share the same finite star endpoint;
- the Earth-to-sphere scale ratio is explicit and reproducible;
- large-Earth and small-Earth illustrations export deterministically;
- their visual comparison communicates the intended convergence limit;
- interactive and batch renders succeed.

### Working product

A scientific-illustration toolkit that produces reusable coordinate, horizon,
navigation, and finite-distance parallax diagrams.

## 15. M11 — Product hardening

### Goal

Produce a standalone Horizon A release candidate.

### Work

- classify stable, advanced, and internal APIs;
- organize styles where accumulated parameters justify it;
- document transparency, far-side visibility, ordering, and occlusion;
- complete quick-start, interactive, batch, annotation, control, coordinate,
  observer, horizon, parallax, and extension documentation;
- verify packaging, supported Python, errors, and absence of stale modules;
- run the full gate in a clean environment.

### Gate

All completion criteria in `target_architecture_horizonA.md` pass.

### Working product

A coherent standalone scientific-illustration product ready for a separately
planned Wenu renderer adapter.

## 16. Deferred Horizon B

Defer:

- importing Wenu;
- consuming Wenu `Observer` and `CelestialSphere`;
- adapting Wenu layers and catalogs;
- apparent-coordinate transformations;
- renderer plugins inside Wenu;
- complete transparency semantics for every possible Wenu layer.

Horizon B may supply celestial objects as directions. It must preserve the
distinction between those directional inputs and Horizon A finite positioned
targets rather than silently reinterpreting finite illustrations.

Record real adapter requirements during Horizon A, but do not redesign for
hypothetical needs.

## 17. Commit strategy

A milestone may contain several small commits:

1. tests describing current behavior;
2. smallest implementation change;
3. example migration;
4. documentation update;
5. milestone verification.

At each milestone record the commit SHA, checks executed, canonical output,
known limitations, and next milestone.

## 18. Change control

This path is authoritative for Horizon A. Departure requires repository
evidence of a contradiction, duplication, broken dependency, simpler safe
path, or scientific error.

Before departing:

1. state the evidence;
2. explain the alternative;
3. describe effects on later milestones;
4. update this document;
5. obtain agreement before substantial architectural change.
