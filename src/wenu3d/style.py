from dataclasses import dataclass


@dataclass
class SceneStyle:
    background: str = "#f7f6f2"

    # Main translucent volume.
    sphere_back_color: str = "#b5cae2"
    sphere_front_color: str = "#e0eaf5"

    # Two outer shells strengthen the limb and glass edge.
    sphere_outer_color: str = "#7094c1"
    sphere_rim_color: str = "#496f9f"

    sphere_back_opacity: float = 0.18
    sphere_front_opacity: float = 0.055
    sphere_outer_opacity: float = 0.080
    sphere_rim_opacity: float = 0.055

    sphere_specular: float = 0.58
    sphere_specular_power: float = 105.0

    horizontal_grid_color: str = "#577fb7"
    equatorial_grid_color: str = "#75638f"

    plane_color: str = "#c8c9c8"
    text_color: str = "#222222"
