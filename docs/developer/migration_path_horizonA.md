# Wenu3D Migration Path — Horizon A

**Version:** 1.5
**Date:** 2026-07-31
**Status:** M10 completed; M11 product hardening in progress through M11.1
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

M0 through M10 are completed history at the start of version 1.4. The remaining
path distinguishes centered celestial geometry from the finite local cartoon.
The celestial sphere, target directions, coordinate curves, observer-specific
ideal horizons, and centered direction lines remain angular constructions.
One cartoon Earth, observer representations, local platforms or vehicles,
decorations, and finite observer sight lines form transformable local
composition. A displayed celestial marker may participate in both domains
without conflating their scientific meanings.

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

Bring the finite Earth-and-observer cartoon into the scene graph without
conflating it with centered celestial geometry. Establish one Earth-fixed
world frame, semantic observers, replaceable representations, coherent
model-aware transforms, and multiple observers while preserving the canonical
visual output incrementally.

### Work

M9 is implemented through small checkpoints. Each checkpoint leaves Wenu3D
working and preserves appearance unless an explicitly requested new mode is
enabled.

#### M9.1 — Characterize the current single-observer composition

Add tests and documentation only. Characterize:

- Earth orientation and texture-correction conventions;
- the current fixed observer at local `+z` and the East-North-Zenith frame;
- equatorial-pole orientation;
- the `cos(latitude)` geographic-pole singularity as a known limitation, not
  desired behavior;
- membership of Earth, stick figure, displaced tangent platform, cardinal
  arrows, axis, and `ActorScaleGroup`;
- centered grids as independent from local actor scale;
- absence of first-class Earth, observer composition, transform, and ideal
  horizon objects.

Do not change visual output or runtime implementation.

#### M9.2 — Earth-fixed observer geometry

1. Define one world Cartesian frame and one Earth orientation per scene.
2. Add renderer-neutral conversion from geographic longitude and latitude to
   a finite position on that Earth and a validated East-North-Zenith frame.
3. Support geographic poles through a documented longitude-based
   local-meridian convention without division by `cos(latitude)`.
4. Verify La Ligua, equatorial, polar, and antipodal reference sites.
5. Adding an observer must never reorient or duplicate Earth.

#### M9.3 — Semantic observer and replaceable representation

1. Add a renderer-neutral `Observer` containing identity, location or finite
   position, and local frame.
2. Define an `ObserverRepresentation` interface for optional drawable
   geometry and named semantic anchors.
3. Wrap the existing stick figure as the first representation without changing
   its appearance.
4. Add an `ObserverComposition` associating the model, representation,
   platform or vehicle context, decorations, and annotations.
5. Keep mesh-specific offsets below this API. Representation anchors such as
   feet and eye remain distinct from intrinsic observer geometry.

#### M9.4 — Earth and local-cartoon scene graph

1. Make Earth an explicit scene object with preserved texture and orientation.
2. Introduce one `LocalCartoonLayer` owning the shared Earth and one or more
   observer compositions.
3. Bring the current local actors into the graph while preserving rendering.
4. Move hard-coded style only as each owning object is formalized.
5. Keep `ActorScaleGroup` until the replacement transform is complete.

#### M9.5 — Ideal horizons and local platforms

1. Associate with each observer an ideal horizon through the celestial origin,
   perpendicular to that observer's zenith.
2. Preserve the finite local platform as a separate object in its observer
   composition, tangent to the cartoon Earth when surface-anchored.
3. Keep each platform parallel to its observer's ideal horizon while allowing
   different centers.
4. Add North, East, South, and West lines and inscriptions as platform
   decoration.
5. Add interchangeable compass-rose and Nainoa Thompson navigation
   decorations from validated vectors or an explicit texture.
6. Do not show a new ideal-horizon surface by default if it changes canonical
   output.

#### M9.6 — Model-aware transforms and placement modes

1. Add the minimum renderer-neutral translation and uniform-scale transform
   required by the local cartoon.
2. Make that transform authoritative for both rendered actors and queries of
   positions and semantic anchors; do not transform actors alone.
3. Support coherent transformation of the shared Earth and all observer
   compositions for scale comparisons.
4. Support surface placement and aligning a selected observer anchor with the
   celestial origin.
5. Transform only the finite local cartoon. Leave the shell, target directions,
   displayed markers, centered curves, and ideal horizons fixed.
6. Retire `ActorScaleGroup` only after this path fully replaces it.

#### M9.7 — Multiple observers and representation replacement

1. Support multiple observers on the shared Earth without special-case scene
   code.
2. Demonstrate observers at antipodal sites with distinct local frames and
   ideal horizons.
3. Replace the stick figure with a minimal alternative representation without
   changing observer geometry or higher-level composition APIs.
4. Verify that named-anchor sight-line origins follow model-aware transforms.

#### M9.8 — Gate hardening and closeout

1. Replace the legacy rendered-Earth orientation with a stable orthonormal
   basis mapping that remains defined at both geographic poles.
2. Convert geographic Earth-fixed observers explicitly into the rendered
   Earth's display frame and verify antipodal platforms and ideal horizons.
3. Exercise the completed two-observer composition through an off-screen
   PyVista render and record the M9 gate as completed.

### Gate

Completed by M9.8.3. The following criteria remain the regression contract:

- M9.1 characterization passes without source changes;
- one fixed Earth orientation supports La Ligua, equatorial, polar, and
  antipodal observers;
- observer positions and East-North-Zenith frames are geometrically verified;
- semantic observers and replaceable representations remain separate;
- named anchors remain correct after representation replacement and local
  transforms;
- two observers coexist without duplicating or reorienting Earth;
- their ideal horizons pass through the celestial origin and their local
  platforms are independently positioned;
- cardinal, compass-rose, and navigation decorations are interchangeable on
  local platforms;
- local visibility, translation, and scale work through the graph;
- `ActorScaleGroup` is retired without changing canonical appearance;
- interactive and batch renders succeed.

### Working product

One Earth, semantic observers, replaceable representations, decorated local
platforms, and observer-specific ideal horizons follow the common object
architecture without mixing cartoon scale with celestial geometry.

## 14. M10 — Coordinate and parallax illustrations

### Goal

Assemble the reusable objects into complete scientifically meaningful
illustrations that combine abstract celestial geometry and finite local-cartoon
geometry without confusing their meanings.

### Work

1. Add a celestial target that retains a unit direction and derives one
   configurable displayed marker position on the shell.
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
5. Ensure coordinate arcs and ideal horizons use the celestial origin and
   target direction, not displaced cartoon-observer positions.
6. Add an optional centered direction line from the celestial origin to the
   displayed marker.
7. Add finite sight lines from named observer anchors to that same marker.
8. Add explicit scale-comparison scenes. Hold the shell, target direction,
   displayed marker, coordinate curves, and ideal horizons fixed while
   transforming only the local cartoon.
9. Demonstrate conspicuous and negligible finite baselines and an explicit
   observer-anchor-at-origin presentation.
10. Treat parallax or convergence as an explicitly requested composition, not
    an implicit consequence of ordinary coordinate helpers.
11. Preserve direct access to every primitive, observer, representation,
    composition, transform, annotation, and style used by convenience helpers.

#### M10.1–M10.9 — Completed checkpoints

1. Separate celestial target direction from its derived shell marker.
2. Add centered horizontal-coordinate geometry and its renderable composition.
3. Add centered equatorial geometry with explicit longitude convention and its
   renderable composition.
4. Add explicit centered direction and finite observer sight-line composition.
5. Add reproducible surface, small-cartoon, and observer-at-origin states.
6. Export those states deterministically while restoring prior local state.
7. Add explicit parallax/convergence composition with transformed baselines,
   convergence angles, and a nonphysical-distance interpretation note.

### Gate

Completed by M10.9. The following criteria remain the regression contract:

- altitude, azimuth, declination, and right-ascension arc endpoints are
  geometrically verified;
- coordinate labels state the convention actually used;
- coordinate curves and ideal horizons remain centered under every local
  transform;
- target direction and displayed position are explicitly linked but not
  conflated;
- both sight lines share the same finite star endpoint;
- centered direction lines originate at the celestial origin;
- observer sight lines resolve named transformed anchors;
- local-to-sphere scale and placement are explicit and reproducible;
- surface, small-cartoon, and observer-at-origin illustrations export
  deterministically;
- their comparison communicates the directional limit without changing
  celestial geometry;
- interactive and batch renders succeed.

### Working product

A scientific-illustration toolkit that produces reusable coordinate, horizon,
navigation, directional-limit, and explicitly requested finite-distance
parallax diagrams.

## 15. M11 — Product hardening

### Goal

Produce a standalone Horizon A release candidate.

### Work

- classify stable, advanced, and internal APIs (completed by M11.1);
- organize styles where accumulated parameters justify it;
- document transparency, far-side visibility, ordering, and occlusion;
- complete quick-start, interactive, batch, annotation, control, coordinate,
  observer, horizon, parallax, and extension documentation;
- verify packaging, supported Python, errors, and absence of stale modules;
- run the full gate in a clean environment.

### Completed checkpoints

- **M11.1 — API classification:** package-root `__all__` is the stable API;
  documented module-only interfaces are advanced; private and undocumented
  renderer details are internal; tests guard the export boundary.

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

Horizon B may supply celestial objects as directions. The adapter maps those
directions into the abstract celestial domain and derives shell positions for
display. It must not silently assign a physical finite distance to a
directional target merely because local-cartoon sight lines can terminate at
the displayed marker.

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
