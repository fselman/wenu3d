import pyvista as pv

from wenu3d.frames import horizontal_frame
from wenu3d.grid import GridLayer


def make_grid() -> GridLayer:
    return GridLayer(
        name="lifecycle",
        frame=horizontal_frame(),
        meridians_deg=(0.0, 90.0),
        parallels_deg=(0.0,),
    )


def test_rebuild_does_not_accumulate_actors() -> None:
    plotter = pv.Plotter(off_screen=True)
    grid = make_grid()

    try:
        grid.build(plotter)
        first_actors = tuple(grid.actors)

        grid.build(plotter)

        assert len(plotter.renderer.actors) == 3
        assert len(grid.actors) == 3
        assert all(len(obj.actors) == 1 for obj in grid.objects)
        assert {id(actor) for actor in first_actors}.isdisjoint(
            id(actor) for actor in grid.actors
        )
    finally:
        plotter.close()


def test_detach_removes_owned_actors() -> None:
    plotter = pv.Plotter(off_screen=True)
    grid = make_grid()

    try:
        grid.build(plotter)
        grid.detach(render=False)

        assert len(plotter.renderer.actors) == 0
        assert grid.actors == []
        assert all(obj.actors == [] for obj in grid.objects)
    finally:
        plotter.close()


def test_rebuild_on_another_plotter_detaches_from_first() -> None:
    first_plotter = pv.Plotter(off_screen=True)
    second_plotter = pv.Plotter(off_screen=True)
    grid = make_grid()

    try:
        grid.build(first_plotter)
        grid.build(second_plotter)

        assert len(first_plotter.renderer.actors) == 0
        assert len(second_plotter.renderer.actors) == 3
    finally:
        first_plotter.close()
        second_plotter.close()


def test_layer_visibility_preserves_child_selection() -> None:
    plotter = pv.Plotter(off_screen=True)
    grid = make_grid()
    hidden = grid.meridians[90.0]
    selected = grid.meridians[0.0]

    try:
        hidden.set_visible(False, render=False)
        grid.build(plotter)

        grid.set_visible(False, render=False)
        assert hidden.visible is False
        assert selected.visible is True
        assert all(not actor.GetVisibility() for actor in grid.actors)

        grid.set_visible(True, render=False)
        assert not hidden.actors[0].GetVisibility()
        assert selected.actors[0].GetVisibility()
    finally:
        plotter.close()
