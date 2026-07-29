# wenu3d interactive-layer update

This update stops at the requested architectural milestone:

- `SceneObject`: uniform actor ownership, visibility, and opacity
- `Layer`: collection of scene objects
- `GridLayer`: collection of individually addressable grid curves
- `GridCurveObject`: one meridian or parallel
- `SceneGraph`: named layer registry
- `GridControlPanel`: one checkbox per meridian and parallel

No renderer abstraction and no Wenu integration are included.

## Apply

Copy the files under `src/wenu3d/` into the corresponding package directory,
then run:

```bash
python examples/la_ligua_interactive_grids.py
```

Individual programmatic controls:

```python
horizontal.meridians[90].set_visible(False)
horizontal.parallels[-30].set_visible(False)
```
