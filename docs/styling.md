# Wenu3D styling guide

Wenu3D separates scientific geometry from rendering style. Horizon A uses
small renderer-neutral style records at primitive boundaries and one scene
theme for the canonical composition.

## Style layers

### Scene theme

`SceneStyle` defines defaults owned by `CelestialScene`:

- background and text colors;
- horizontal and equatorial grid colors;
- local-platform color;
- the camera-dependent celestial-shell palette, opacity profile, limb shape,
  and highlight parameters.

Pass one at scene construction:

```python
from wenu3d import CelestialScene, SceneStyle


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    style=SceneStyle(
        background="#ffffff",
        horizontal_grid_color="#477bb8",
        equatorial_grid_color="#755792",
    ),
)
```

`SceneStyle` is a construction-time theme, not a live stylesheet. Changing its
fields after actors are built does not promise to restyle existing actors. For
reproducible output, construct the scene with the final theme.

### Primitive styles

Renderer-neutral primitives own styles matching their visual semantics:

| Primitive | Style | Main properties |
|---|---|---|
| annotation | `AnnotationStyle` | color, font size, bold |
| marker | `MarkerStyle` | shape, color, radius, opacity |
| segment or sight line | `SegmentStyle` | color, width, opacity |
| sampled curve or arc | `CurveStyle` | color, width, opacity, arrowheads |
| finite plane | `SurfaceStyle` | face, opacity, edges |
| vector arrow | `VectorStyle` | color, opacity |
| coordinate grid | `GridStyle` | major/minor radii and opacities, labels |

These types remain distinct even when properties overlap. A segment width is a
screen-space line width, a curve may own arrowheads, a surface has edge
treatment, and a marker radius is world-space geometry. Combining them into a
generic color-width-opacity record would erase useful constraints.

Most primitive style records are immutable and validate their inputs. Reuse is
safe:

```python
from wenu3d import IllustrationLayer, LineSegment, SegmentStyle


construction = SegmentStyle(color="#496b83", width=3.0, opacity=0.8)
layer = IllustrationLayer(name="construction")
layer.add_segment(
    "construction.first",
    LineSegment(start=(0, 0, 0), end=(0, 0, 1), style=construction),
)
layer.add_segment(
    "construction.second",
    LineSegment(start=(0, 0, 0), end=(1, 0, 0), style=construction),
)
```

## Composite illustrations

Composite illustrations accept one style per scientific role instead of a
large illustration-specific style bundle:

- horizontal coordinates: altitude curve, azimuth curve, annotations;
- equatorial coordinates: declination curve, longitude curve, annotations;
- target lines: centered direction and observer sight lines;
- parallax: centered direction, sight lines, and interpretation note;
- decorated platforms: surface, line or vector, and inscription styles.

This keeps each role explicit and allows the same primitive style to be reused
across different illustrations.

```python
from wenu3d import CurveStyle, HorizontalCoordinateIllustration


coordinates = HorizontalCoordinateIllustration(
    name="coordinates.target",
    target=target,
    frame=scene.horizontal,
    altitude_style=CurveStyle(
        color="#315f9b",
        width=4.0,
        arrowheads="end",
    ),
    azimuth_style=CurveStyle(
        color="#477b50",
        width=4.0,
        arrowheads="end",
    ),
)
```

Defaults are created by the owning illustration. Supplying one role style does
not silently modify another role.

## Opacity and visibility

Style opacity initializes the lifecycle-managed object's actor opacity.
`SceneObject.set_opacity()` can update the attached actor later. Visibility is
separate from opacity: hidden objects do not participate visually, while
zero-opacity objects remain renderer actors.

Layer visibility is inherited without overwriting child selections. Layer
opacity is not recursively multiplied into child style opacity. See
`rendering_policy.md` for depth, shell alpha, labels, and transparent export.

## Horizon A organization decision

The M11 review retains the existing style boundaries:

- primitive style records already replace repeated scalar parameters where
  semantics justify grouping;
- composite constructors expose a short, role-specific list of those records;
- `SceneStyle` remains one flat canonical-scene theme because its parameters
  have one consumer and are normally configured together;
- no generic master style, nested shell theme, or coordinate/parallax bundle is
  introduced for the release candidate.

A future split is justified only when a style group has multiple independent
consumers or callers repeatedly pass the same group as a unit. Such a change
must preserve existing constructor behavior where practical.

## Publication practice

- Define styles near the scientific object that owns their meaning.
- Reuse immutable primitive styles for related geometry.
- Keep color contrast legible on the selected background.
- Distinguish coordinate roles by more than small color differences when
  possible, using width, arrowheads, or labels.
- Fix all style values before deterministic export.
- Visually inspect transparency and annotation placement at the final camera
  and output size.
