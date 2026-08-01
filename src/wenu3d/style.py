from dataclasses import dataclass


@dataclass
class SceneStyle:
    background: str = "#f7f6f2"

    # Dynamic glass-sphere material.
    sphere_center_color: str = "#dce8f5"
    sphere_rim_color: str = "#456b98"
    sphere_highlight_color: str = "#ffffff"

    # The centre remains nearly transparent. Opacity increases toward the limb.
    sphere_center_opacity: float = 0.030
    sphere_rim_opacity: float = 0.46
    sphere_limb_power: float = 0.80

    # Broad asymmetric illumination provides a three-dimensional depth cue.
    sphere_directional_strength: float = 0.18

    # Two specular reflections.
    sphere_specular_strength: float = 1.00
    sphere_specular_power: float = 42.0
    sphere_secondary_specular_strength: float = 0.48
    sphere_secondary_specular_power: float = 22.0

    horizontal_grid_color: str = "#577fb7"
    equatorial_grid_color: str = "#75638f"

    plane_color: str = "#c8c9c8"
    text_color: str = "#222222"
