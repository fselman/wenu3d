# wenu3d

Standalone PyVista toolkit for geometrically correct 3D astronomical
illustrations.

Wenu3D is intended for teaching, publications, and outreach. It is not an
interactive planetarium.

## Install

```bash
python -m pip install -e .
```

## Run the canonical example

```bash
python examples/la_ligua_interactive_grids.py
```

The example constructs horizontal and equatorial grids for La Ligua, adds
interactive grid controls, and writes:

```text
outputs/la_ligua_interactive.png
```

## Basic use

```python
from wenu3d import CelestialScene


scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
)

horizontal = scene.make_horizontal_grid(
    meridians_deg=(0, 30, 60, 90, 120, 150),
    parallels_deg=(-60, -30, 0, 30, 60),
)
scene.add(horizontal)

scene.add_grid_controls(horizontal)
scene.add_global_controls()
scene.show()
scene.close()
```

## Adding both coordinate grids

Grid creation and scene insertion are separate operations. This keeps each
grid available as a named, individually controllable `GridLayer`.

```python
horizontal = scene.make_horizontal_grid()
scene.add(horizontal)

equatorial = scene.make_equatorial_grid()
scene.add(equatorial)
```

To omit a grid, do not create and add it.

Each grid accepts independent `meridians_deg` and `parallels_deg` sequences.
Major meridians and parallels receive the current major-grid style.

## Viewport controls

A grid control panel provides:

- complete-grid visibility;
- meridian-family visibility;
- parallel-family visibility;
- individual meridian visibility;
- individual parallel visibility.

Disabling a family preserves its individual selections, which are restored
when that family is enabled again.

Global controls provide:

- celestial-sphere visual presence;
- Earth/plane/observer scale.
- canonical camera reset.

`ControlManager` assigns panel positions, wraps panels into columns, avoids
overlaps, and synchronizes widget state with the scene model.

## Annotations

`Annotation`, `AnnotationObject`, and `AnnotationLayer` provide first-class
scientific callouts. Grids can create separately selectable annotation layers
with `make_label_layer()`. Annotation controls manage layer visibility and
text-size scaling.

The canonical example demonstrates horizontal-grid labels and a Spanish
callout for the south celestial pole.

## Reproducible image export

Use an off-screen scene when no interactive window is required:

```python
scene = CelestialScene(
    latitude_deg=-32.4524,
    longitude_deg=-71.2311,
    location_name="La Ligua",
    off_screen=True,
)

scene.add(scene.make_horizontal_grid())
scene.add(scene.make_equatorial_grid())

image = scene.save(
    "la_ligua.png",
    window_size=(1600, 1150),
    transparent_background=False,
)
scene.close()
```

`CameraState` captures and reapplies the complete camera configuration.
Repeated `render()` and `save()` calls reuse scene content without duplicating
the title, actors, or controls. `close()` releases graph and PyVista resources
and is safe to call more than once.

## Architecture and roadmap

Developer documentation is in `docs/developer/`:

- `current_architecture.md`;
- `target_architecture_horizonA.md`;
- `migration_path_horizonA.md`;
- `assistant_instructions.md`.
