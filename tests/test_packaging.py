import importlib
import pkgutil
from pathlib import Path
import tomllib

import wenu3d


ROOT = Path(__file__).resolve().parents[1]


def project_metadata() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)["project"]


def test_project_metadata_declares_release_inputs() -> None:
    project = project_metadata()

    assert project["name"] == "wenu3d"
    assert project["version"] == "0.1.0"
    assert project["readme"] == "README.md"
    assert project["requires-python"] == ">=3.11"
    assert set(project["dependencies"]) == {
        "numpy>=1.26",
        "pyvista>=0.48",
        "vtk>=9.3",
    }
    assert project["optional-dependencies"]["test"] == ["pytest>=8"]
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]


def test_documentation_files_declared_by_readme_exist() -> None:
    for relative_path in (
        "README.md",
        "docs/api_stability.md",
        "docs/rendering_policy.md",
        "docs/user_guide.md",
        "docs/packaging.md",
    ):
        assert (ROOT / relative_path).is_file()


def test_every_shipped_package_module_imports() -> None:
    modules = tuple(
        module.name
        for module in pkgutil.iter_modules(wenu3d.__path__, "wenu3d.")
    )

    assert modules
    for module_name in modules:
        importlib.import_module(module_name)


def test_removed_modules_and_obsolete_example_remain_absent() -> None:
    shipped = {
        module.name
        for module in pkgutil.iter_modules(wenu3d.__path__, "wenu3d.")
    }

    assert "wenu3d.labels" not in shipped
    assert "wenu3d.local_group" not in shipped
    assert not (ROOT / "examples" / "la_ligua_grids.py").exists()
