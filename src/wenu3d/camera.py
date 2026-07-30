from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite, sqrt


Vector3 = tuple[float, float, float]


def _vector3(name: str, value: Sequence[float]) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{name} must contain exactly three values.")
    result = tuple(float(component) for component in value)
    if not all(isfinite(component) for component in result):
        raise ValueError(f"{name} must contain only finite values.")
    return result


def _length(vector: Vector3) -> float:
    return sqrt(sum(component * component for component in vector))


@dataclass(frozen=True)
class CameraState:
    """Serializable parameters that reproduce a Wenu3D camera view."""

    position: Vector3
    focal_point: Vector3
    view_up: Vector3
    view_angle: float = 30.0
    parallel_projection: bool = False
    parallel_scale: float = 1.0

    def __post_init__(self) -> None:
        position = _vector3("position", self.position)
        focal_point = _vector3("focal_point", self.focal_point)
        view_up = _vector3("view_up", self.view_up)
        view_angle = float(self.view_angle)
        parallel_scale = float(self.parallel_scale)

        direction = tuple(
            focal - camera
            for camera, focal in zip(position, focal_point)
        )
        if _length(direction) == 0.0:
            raise ValueError(
                "Camera position and focal_point must be different."
            )
        if _length(view_up) == 0.0:
            raise ValueError("Camera view_up must be nonzero.")
        if not isfinite(view_angle) or not 0.0 < view_angle < 180.0:
            raise ValueError(
                "Camera view_angle must be finite and between 0 and 180."
            )
        if not isfinite(parallel_scale) or parallel_scale <= 0.0:
            raise ValueError(
                "Camera parallel_scale must be finite and positive."
            )

        object.__setattr__(self, "position", position)
        object.__setattr__(self, "focal_point", focal_point)
        object.__setattr__(self, "view_up", view_up)
        object.__setattr__(self, "view_angle", view_angle)
        object.__setattr__(
            self,
            "parallel_projection",
            bool(self.parallel_projection),
        )
        object.__setattr__(self, "parallel_scale", parallel_scale)
