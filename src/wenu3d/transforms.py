from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


Vector3 = tuple[float, float, float]


def _vector3(value: Sequence[float], *, field_name: str) -> Vector3:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain three finite components.")
    return tuple(float(component) for component in vector)


def _cartesian_values(value, *, field_name: str) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if values.ndim == 0 or values.shape[-1] != 3:
        raise ValueError(f"{field_name} must end with three components.")
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{field_name} must contain only finite values.")
    return values


@dataclass(frozen=True)
class LocalCartoonTransform:
    """Renderer-neutral translation and uniform scale for finite geometry."""

    translation: Sequence[float] = (0.0, 0.0, 0.0)
    scale: float = 1.0

    def __post_init__(self) -> None:
        translation = _vector3(self.translation, field_name="translation")
        scale = float(self.scale)
        if not np.isfinite(scale) or scale <= 0.0:
            raise ValueError("scale must be finite and greater than zero.")
        object.__setattr__(self, "translation", translation)
        object.__setattr__(self, "scale", scale)

    @classmethod
    def identity(cls) -> LocalCartoonTransform:
        return cls()

    def apply_points(self, points) -> np.ndarray:
        """Transform one point or an array whose final axis is Cartesian."""
        values = _cartesian_values(points, field_name="points")
        return self.scale * values + np.asarray(self.translation)

    def apply_vectors(self, vectors) -> np.ndarray:
        """Scale free vectors without applying translation."""
        values = _cartesian_values(vectors, field_name="vectors")
        return self.scale * values

    def apply_directions(self, directions) -> np.ndarray:
        """Return direction vectors unchanged by translation or uniform scale."""
        values = _cartesian_values(directions, field_name="directions")
        return values.copy()

    def apply_length(self, length: float) -> float:
        value = float(length)
        if not np.isfinite(value) or value < 0.0:
            raise ValueError("length must be finite and non-negative.")
        return self.scale * value

    @property
    def inverse(self) -> LocalCartoonTransform:
        inverse_scale = 1.0 / self.scale
        translation = -inverse_scale * np.asarray(self.translation)
        return LocalCartoonTransform(
            translation=translation,
            scale=inverse_scale,
        )

    def then(
        self,
        following: LocalCartoonTransform,
    ) -> LocalCartoonTransform:
        """Compose this transform followed by ``following``."""
        if not isinstance(following, LocalCartoonTransform):
            raise TypeError("following must be a LocalCartoonTransform.")
        translation = (
            following.scale * np.asarray(self.translation)
            + np.asarray(following.translation)
        )
        return LocalCartoonTransform(
            translation=translation,
            scale=following.scale * self.scale,
        )

    @property
    def matrix(self) -> np.ndarray:
        """Return the homogeneous 4×4 matrix equivalent of this transform."""
        matrix = np.eye(4, dtype=float)
        matrix[:3, :3] *= self.scale
        matrix[:3, 3] = self.translation
        return matrix
