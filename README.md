# wenu3d

Standalone PyVista toolkit for geometrically correct 3D astronomy diagrams.

## Install

```bash
python -m pip install -e .
```

## Run

```bash
python examples/la_ligua_grids.py
```

## Selecting grid curves and labels

Each grid distinguishes between curves that are drawn and curves that are
labeled:

```python
scene.add_horizontal_grid(
    meridians_deg=(0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330),
    parallels_deg=(-60, -30, 0, 30, 60),
    labeled_meridians_deg=(0, 90, 180, 270),
    labeled_parallels_deg=(-60, -30, 0, 30, 60),
)
```

The same arguments are accepted by `add_equatorial_grid()`.

To omit the equatorial grid, do not call `scene.add_equatorial_grid()`.

## Viewport controls

- celestial sphere presence
- Earth/plane/observer scale
- label font size
- equatorial-grid checkbox
