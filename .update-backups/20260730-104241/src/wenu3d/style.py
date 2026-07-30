from dataclasses import dataclass


@dataclass
class SceneStyle:
    background: str = "#f7f6f2"

    # Pale blue, glass-like celestial sphere.
    sphere_back_color: str = "#bfd2e8"
    sphere_front_color: str = "#d9e6f4"
    sphere_outer_color: str = "#7fa3cf"

    sphere_back_opacity: float = 0.16
    sphere_front_opacity: float = 0.045
    sphere_outer_opacity: float = 0.065

    sphere_specular: float = 0.38
    sphere_specular_power: float = 80.0

    # Thin grid curves drawn just inside the shell.
    horizontal_grid_color: str = "#527bb3"
    equatorial_grid_color: str = "#7a6599"

    plane_color: str = "#c8c9c8"
    text_color: str = "#222222"
