# Wenu3D transparency and occlusion policy

This document records the rendering semantics implemented by the Horizon A
release candidate. It describes the canonical scientific illustrations; it is
not a promise of a general-purpose transparency engine.

## Depth and occlusion

Ordinary 3D actors use PyVista and VTK depth testing. Opaque geometry therefore
occludes geometry behind it from the active camera. In particular, the cartoon
Earth can hide observer, platform, curve, marker, and sight-line geometry on
its far side.

Insertion order is stable in `SceneGraph`, `Layer`, and `IllustrationLayer` and
defines construction order. It does not override the depth buffer and is not a
guarantee that a later opaque object will appear in front of a nearer object.

Wenu3D does not currently install a custom translucent-depth-peeling or
per-object sorting policy. The appearance of several intersecting translucent
objects may therefore depend on VTK's renderer and camera. Canonical diagrams
avoid unnecessary coincident translucent surfaces and use explicit geometric
offsets where separation carries scientific meaning.

## Celestial shell

`CelestialShellObject` is a special translucent surface:

- its mesh lies at the configured celestial-shell radius;
- it uses camera-dependent per-vertex RGBA values;
- its center is nearly transparent and opacity increases toward the limb;
- only outward-facing geometry is drawn through back-face culling;
- lighting is disabled because color, limb emphasis, and highlights are
  computed by the shell material itself;
- camera changes refresh the material.

Far-side celestial geometry is not duplicated or projected onto the front of
the shell. It may be visible through the shell where alpha permits, subject to
ordinary occlusion by Earth and other geometry.

`presence` scales the shell mesh alpha. The inherited `SceneObject.opacity`
sets the actor-level opacity. Visibility, presence, and opacity are distinct:
visibility selects whether the actor participates, presence changes the shell
material, and opacity applies an actor-wide multiplier.

## Other translucent objects

Markers, segments, curves, vectors, finite surfaces, grids, layers, and local
composition use ordinary actor opacity. Renderer-neutral style opacity is
copied to the lifecycle-managed scene object, and `SceneObject` applies its
current opacity whenever an actor is attached or updated.

Layer opacity is not recursively multiplied into child styles. A layer owns
group visibility, while each child retains its own scientific style and actor
opacity. Callers that require a coordinated fade should set the participating
objects explicitly.

## Annotations

3D annotations use PyVista point labels with `always_visible=True`. They are
therefore explanatory overlays rather than depth-occluded physical objects.
Their anchor and offset remain world-coordinate geometry, but label text is
kept readable even when an opaque object lies between its position and the
camera.

Use annotations for explanation, not as evidence that an associated point is
on the visible side of a surface. When that distinction matters, pair the text
with visible marker or line geometry.

## Transparent image export

`CelestialScene.save(..., transparent_background=True)` requests an RGBA image
with a transparent canvas. This option does not change shell presence, actor
opacity, depth testing, or label behavior. With the default `False`, export is
an opaque RGB image using the scene background.

Transparent export is intended for composition in documents. Object alpha and
background alpha remain separate, explicit choices.

## Practical guidance

- Use opaque Earth geometry when physical near/far-side occlusion matters.
- Use shell transparency to reveal directional geometry, not to imply finite
  distance.
- Avoid coincident translucent planes; offset or omit one when possible.
- Treat label visibility separately from geometric visibility.
- Fix the camera and export settings for reproducible publication output.
- Visually inspect any new illustration with several overlapping translucent
  objects on every supported rendering environment.
