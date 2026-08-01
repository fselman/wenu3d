# Wenu3D packaging and release verification

Wenu3D uses the `src` layout, setuptools, and `pyproject.toml`. The Horizon A
release candidate requires Python 3.11 or newer. Python 3.11 is the explicitly
classified and release-gate environment; newer Python versions remain subject
to dependency availability and should be added to the classifier list only
after verification.

## Development installation

From the repository root in the intended environment:

```bash
python -m pip install -e ".[test]"
python -c "import wenu3d; print(len(wenu3d.__all__))"
python -m pytest -q
```

The editable installation must resolve `wenu3d` from `src/wenu3d` and install
NumPy, PyVista, VTK, and the test extra.

## Build distributions

Install the standard build frontend in the release environment, then build
both source and wheel distributions:

```bash
python -m pip install build
python -m build
```

The command creates `dist/wenu3d-0.1.0.tar.gz` and a platform-independent
`wenu3d-0.1.0-py3-none-any.whl`. Generated `build/`, `dist/`, and metadata
directories are release artifacts and must not be committed.

## Clean-environment gate

Use a disposable environment outside the repository. On macOS or Linux:

```bash
python3.11 -m venv /tmp/wenu3d-release-check
source /tmp/wenu3d-release-check/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[test]"
python -m pytest -q
python examples/la_ligua_interactive_grids.py
```

For a wheel-specific check, build first and install the generated wheel plus
pytest in the disposable environment:

```bash
python -m pip install pytest dist/wenu3d-0.1.0-py3-none-any.whl
python -c "import pkgutil, wenu3d; [__import__(m.name) for m in pkgutil.iter_modules(wenu3d.__path__, 'wenu3d.')]"
```

The canonical example is not installed as a console command; run it from the
repository checkout during the release gate.

## Supported metadata

The project metadata declares:

- distribution name and version: `wenu3d` 0.1.0;
- Python requirement: 3.11 or newer;
- runtime dependencies: NumPy, PyVista, and VTK;
- optional test dependency: pytest;
- project README as the long description;
- repository and documentation URLs.

The package has no command-line entry point and no bundled data files. Runtime
Earth texture data is obtained through PyVista's example-data facility by the
current advanced Earth renderer.

## Module inventory

Every Python file directly under `src/wenu3d` is a shipped importable module.
The release tests enumerate and import that inventory. Historical modules
`wenu3d.labels` and `wenu3d.local_group` are intentionally absent; the obsolete
`examples/la_ligua_grids.py` is also absent. Their historical mention in the
migration record does not make them supported interfaces.

## Failure interpretation

- A build failure is a packaging blocker, not a rendering issue.
- A module-import failure identifies a missing dependency, circular import, or
  stale module reference and blocks release.
- A PyVista window or off-screen rendering failure may depend on the platform's
  graphics configuration; record the environment before changing geometry.
- Do not force-install around an incompatible Python or dependency version.
