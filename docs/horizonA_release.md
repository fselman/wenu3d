# Wenu3D Horizon A release candidate

Horizon A delivers Wenu3D 0.1.0 as a standalone scientific-illustration
toolkit. It does not include the separately planned Wenu renderer adapter.

## Completion evidence

The completion criteria in `developer/target_architecture_horizonA.md` map to
the following repository evidence.

| # | Criterion | Evidence |
|---|---|---|
| 1 | One coherent API | `api_stability.md`, `user_guide.md`, README, canonical example, `test_public_api.py` |
| 2 | Scientific and lifecycle tests | Complete pytest suite; geometry, frame, observer, rendering, and lifecycle test modules |
| 3 | Interactive and batch canonical scene | `examples/la_ligua_interactive_grids.py`, `test_scene_rendering.py`, `test_m9_batch_render.py` |
| 4 | Safe object lifecycle | `test_lifecycle.py` and primitive rendering tests |
| 5 | First-class annotations | Annotation record, object, layer, controls, rendering, and sizing tests |
| 6 | Reusable managed controls | `ControlManager`, grid/annotation/global panels, control tests |
| 7 | Shell and local graph participation | Shell, Earth, observer-composition, and local-cartoon tests |
| 8 | Deterministic publication export | Camera and scene rendering tests; scale-comparison export tests |
| 9 | Coordinate and transparency conventions | `user_guide.md`, `rendering_policy.md`, coordinate and transparency tests |
| 10 | Reusable illustration primitives | Marker, segment, curve, arc, surface, illustration-layer, coordinate, horizon, target-line, and parallax tests |
| 11 | Celestial/local scale separation | Transform and scale-comparison tests |
| 12 | Direction versus display position | `CelestialTarget`, target and target-line tests |
| 13 | Shared Earth and multiple observers | Geography, Earth-object, and multiple-observer tests, including poles and antipodes |
| 14 | Observer responsibility separation | Observer-model, representation, anchor, local-cartoon, and sight-line tests |
| 15 | Horizon/platform separation | Horizon, platform, and platform-decoration tests |
| 16 | Render/query transform alignment | Transform, local-cartoon, sight-line, and comparison tests |
| 17 | Wenu adapter boundary | `user_guide.md`, `api_stability.md`, target architecture, and renderer-neutral primitives |

## Final release gate

Run from a clean checkout of the release-candidate commit on Python 3.11.
Generated distributions are ignored by Git and must not be committed.

### 1. Repository gate

```bash
git status
git branch --show-current
git log -1 --oneline
python -m pytest -q
python examples/la_ligua_interactive_grids.py
```

Confirm the complete test suite passes, the canonical window behaves normally,
and the final visual result has no regression.

### 2. Distribution build

```bash
python -m pip install build
python -m build
ls -lh dist
```

Expected artifacts:

```text
wenu3d-0.1.0.tar.gz
wenu3d-0.1.0-py3-none-any.whl
```

### 3. Clean wheel environment

Create a disposable environment outside the repository and install the wheel,
its dependencies, and pytest:

```bash
WENU3D_RELEASE_ENV="$(mktemp -d /tmp/wenu3d-release-check.XXXXXX)"
python3.11 -m venv "$WENU3D_RELEASE_ENV"
source "$WENU3D_RELEASE_ENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install pytest dist/wenu3d-0.1.0-py3-none-any.whl
python -c "import pkgutil, wenu3d; [__import__(m.name) for m in pkgutil.iter_modules(wenu3d.__path__, 'wenu3d.')]"
python -m pytest -q
python examples/la_ligua_interactive_grids.py
deactivate
```

The tests are intentionally run from the repository, while imports resolve to
the installed wheel because Wenu3D uses the `src` layout and the clean
environment has no editable installation.

### 4. Final repository check

```bash
git status
```

Only the intended closeout-document changes should be present before commit.
`build/`, `dist/`, and `*.egg-info` are ignored release artifacts.

## Release-candidate interpretation

Passing this gate establishes a coherent Horizon A release candidate:

- the stable package-root API is documented;
- scientific geometry and renderer lifecycle are tested;
- interactive and off-screen output work;
- source and wheel distributions build and import cleanly;
- the canonical illustration passes visual review;
- Wenu integration remains explicitly deferred to Horizon B.

Platform-independent pixel identity is not claimed. VTK output can vary across
graphics environments, so deterministic tests compare repeated output within
one environment and retain scientific geometry assertions as the primary
cross-platform contract.
