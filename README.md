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

scene.add_grid_controls(
    horizontal,
    origin_x=20,
    origin_y=650,
)
scene.add_global_controls()
scene.show()
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

Control positions are currently supplied explicitly in pixels. Automatic
control layout is planned for Horizon A.

## Current annotation status

Annotations and grid labels are not part of the current supported API. They
are planned as first-class scene objects in Horizon A milestone M4.

## Architecture and roadmap

Developer documentation is in `docs/developer/`:

- `current_architecture.md`;
- `target_architecture_horizonA.md`;
- `migration_path_horizonA.md`;
- `assistant_instructions.md`.
