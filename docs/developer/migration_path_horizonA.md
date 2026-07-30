# Wenu3D Migration Path — Horizon A

**Version:** 1.0  
**Date:** 2026-07-30  
**Status:** Fixed incremental migration path  
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
| M8 | Local illustration as a layer |
| M9 | Horizon A release candidate |

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

## 12. M8 — Local illustration layer

### Goal

Bring Earth, plane, observer, arrows, and axes into the scene graph.

### Work

1. Introduce the smallest useful explicit objects.
2. Group them into a local layer with visibility and scale.
3. Retire `ActorScaleGroup` once fully replaced.
4. define or reject geographic-pole behavior.
5. Preserve Earth axis, site, zenith, and texture relationships.
6. Move hard-coded style only as each object is formalized.

### Gate

- local geometry tests pass;
- group scale works through the layer;
- Earth orientation is verified for La Ligua and reference sites;
- all base elements appear in the graph;
- interactive and batch renders succeed.

### Working product

The full canonical illustration follows one object architecture.

## 13. M9 — Product hardening

### Goal

Produce a standalone Horizon A release candidate.

### Work

- classify stable, advanced, and internal APIs;
- organize styles where accumulated parameters justify it;
- document transparency, far-side visibility, ordering, and occlusion;
- complete quick-start, interactive, batch, annotation, control, coordinate,
  and extension documentation;
- verify packaging, supported Python, errors, and absence of stale modules;
- run the full gate in a clean environment.

### Gate

All completion criteria in `target_architecture_horizonA.md` pass.

### Working product

A coherent standalone scientific-illustration product ready for a separately
planned Wenu renderer adapter.

## 14. Deferred Horizon B

Defer:

- importing Wenu;
- consuming Wenu `Observer` and `CelestialSphere`;
- adapting Wenu layers and catalogs;
- apparent-coordinate transformations;
- renderer plugins inside Wenu;
- complete transparency semantics for every possible Wenu layer.

Record real adapter requirements during Horizon A, but do not redesign for
hypothetical needs.

## 15. Commit strategy

A milestone may contain several small commits:

1. tests describing current behavior;
2. smallest implementation change;
3. example migration;
4. documentation update;
5. milestone verification.

At each milestone record the commit SHA, checks executed, canonical output,
known limitations, and next milestone.

## 16. Change control

This path is authoritative for Horizon A. Departure requires repository
evidence of a contradiction, duplication, broken dependency, simpler safe
path, or scientific error.

Before departing:

1. state the evidence;
2. explain the alternative;
3. describe effects on later milestones;
4. update this document;
5. obtain agreement before substantial architectural change.
