from dataclasses import dataclass


@dataclass
class SceneStyle:
    background: str = "#f7f6f2"

    sphere_back_color: str = "#a7b2bb"
    sphere_front_color: str = "#7f919f"
    sphere_back_opacity: float = 0.14
    sphere_front_opacity: float = 0.035
    sphere_specular: float = 0.18
    sphere_specular_power: float = 55.0

    horizontal_grid_color: str = "#746b82"
    equatorial_grid_color: str = "#55718a"

    plane_color: str = "#c8c9c8"
    text_color: str = "#222222"
