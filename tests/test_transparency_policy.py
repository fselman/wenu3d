from unittest.mock import Mock

from wenu3d import (
    Annotation,
    AnnotationObject,
    CelestialShellObject,
    SceneObject,
)


def test_scene_object_applies_visibility_and_opacity_to_new_actor() -> None:
    actor = Mock()
    prop = actor.GetProperty.return_value
    obj = SceneObject(name="policy", visible=False, opacity=0.35)

    obj.add_actor(actor)

    actor.SetVisibility.assert_called_once_with(False)
    prop.SetOpacity.assert_called_once_with(0.35)


def test_scene_object_opacity_updates_existing_actor() -> None:
    actor = Mock()
    prop = actor.GetProperty.return_value
    obj = SceneObject(name="policy")
    obj.add_actor(actor)
    prop.reset_mock()

    obj.set_opacity(0.2, render=False)

    assert obj.opacity == 0.2
    prop.SetOpacity.assert_called_once_with(0.2)


def test_shell_uses_rgba_material_and_back_face_culling() -> None:
    plotter = Mock()
    plotter.camera.position = (2.35, -2.70, 1.55)
    plotter.iren.add_observer.return_value = 17
    shell = CelestialShellObject(name="shell", radius=1.4)

    shell.build(plotter)

    options = plotter.add_mesh.call_args.kwargs
    assert options["scalars"] == "celestial_sphere_rgba"
    assert options["rgba"] is True
    assert options["lighting"] is False
    assert options["culling"] == "back"


def test_annotations_are_explanatory_always_visible_overlays() -> None:
    plotter = Mock()
    obj = AnnotationObject(
        name="zenith.label",
        annotation=Annotation(text="Zenith", anchor=(0.0, 0.0, 1.0)),
    )

    obj.build(plotter)

    options = plotter.add_point_labels.call_args.kwargs
    assert options["always_visible"] is True
    assert options["show_points"] is False
    assert options["shape"] is None
