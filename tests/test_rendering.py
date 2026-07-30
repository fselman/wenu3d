import numpy as np
import pyvista as pv

from wenu3d.frames import horizontal_frame
from wenu3d.grid import GridLayer


def test_grid_layer_renders_png_off_screen(tmp_path) -> None:
    output = tmp_path / "grid_smoke.png"
    plotter = pv.Plotter(
        off_screen=True,
        window_size=(320, 240),
    )

    try:
        grid = GridLayer(
            name="smoke",
            frame=horizontal_frame(),
            meridians_deg=(0.0, 90.0),
            parallels_deg=(0.0,),
            major_meridians_deg=(0.0,),
            major_parallels_deg=(0.0,),
        )
        grid.build(plotter)

        image = plotter.screenshot(
            filename=str(output),
            return_img=True,
        )
    finally:
        plotter.close()

    assert len(grid.objects) == 3
    assert len(grid.actors) == 3
    assert output.is_file()
    assert output.stat().st_size > 0
    assert isinstance(image, np.ndarray)
    assert image.shape[:2] == (240, 320)
    assert image.shape[2] in (3, 4)
