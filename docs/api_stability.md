# Wenu3D API stability

Wenu3D separates its interfaces into stable, advanced, and internal APIs. This
classification applies to the Horizon A release candidate and lets examples
and downstream code choose the appropriate compatibility level.

## Stable API

Names exported from the package root are the stable user-facing API:

```python
from wenu3d import CelestialScene, CelestialTarget, SphericalFrame
```

The complete stable set is declared by `wenu3d.__all__`. Stable names preserve
their documented meaning and import location across compatible releases.
Necessary changes will be documented and will preserve compatibility where
practical.

This category includes:

- scene, layer, and lifecycle types;
- renderer-neutral geometry and styles;
- annotations and managed controls;
- celestial-shell and local-cartoon objects;
- observer, platform, coordinate, target-line, comparison, and parallax
  illustration types;
- documented frame, geography, and Earth-orientation functions.

Application code and public examples should normally import only from
`wenu3d`.

## Advanced API

Publicly named objects that are available only from their defining modules are
advanced APIs. They support specialized construction, diagnostics, or
extension work, but may evolve between minor releases as renderer details are
hardened.

Examples include:

```python
from wenu3d.controls import ControlPanel, GridControlPanel
from wenu3d.earth import orient_earth_to_observer, realistic_earth
from wenu3d.observer import add_observer, tangent_plane
from wenu3d.rendering import add_arrow, add_tube
```

An advanced name is not promoted to the stable API merely because Python
allows importing it. Code that depends on one should isolate that dependency
and test it when updating Wenu3D.

## Internal API

Names beginning with an underscore and undocumented implementation details are
internal. Modules may also contain private validation and mesh-building
helpers. These interfaces have no compatibility guarantee and should not be
used by applications.

The following are also internal implementation details unless explicitly
documented otherwise:

- PyVista actors stored by scene objects;
- widget and callback bookkeeping;
- flattened actor caches;
- private validation helpers;
- mesh construction choices and renderer call order.

Use renderer-neutral records, scene objects, layers, and public lifecycle
operations instead of reaching into those details.

## Extension boundary

New scientific capabilities should be assembled from stable primitives and
added through `SceneObject`, `Layer`, or `IllustrationLayer`. Renderer-specific
work should remain behind lifecycle-managed scene objects. A future Wenu
adapter belongs outside the Horizon A standalone API and must not require
applications to depend on Wenu3D internals.
