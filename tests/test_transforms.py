import numpy as np
import pytest

from wenu3d.transforms import LocalCartoonTransform


def test_identity_preserves_points_vectors_directions_and_length() -> None:
    transform = LocalCartoonTransform.identity()
    point = np.array([1.0, -2.0, 3.0])

    np.testing.assert_allclose(transform.apply_points(point), point)
    np.testing.assert_allclose(transform.apply_vectors(point), point)
    np.testing.assert_allclose(transform.apply_directions(point), point)
    assert transform.apply_length(2.5) == 2.5


def test_transform_applies_uniform_scale_then_translation_to_points() -> None:
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=2.0,
    )
    points = np.array([[0.0, 0.0, 0.0], [1.0, -1.0, 2.0]])

    np.testing.assert_allclose(
        transform.apply_points(points),
        [[1.0, 2.0, 3.0], [3.0, 0.0, 7.0]],
    )


def test_vectors_lengths_and_directions_use_correct_affine_semantics() -> None:
    transform = LocalCartoonTransform(
        translation=(10.0, 20.0, 30.0),
        scale=0.25,
    )

    np.testing.assert_allclose(
        transform.apply_vectors([4.0, 8.0, -12.0]),
        [1.0, 2.0, -3.0],
    )
    np.testing.assert_allclose(
        transform.apply_directions([0.0, 0.0, 1.0]),
        [0.0, 0.0, 1.0],
    )
    assert transform.apply_length(8.0) == 2.0


def test_inverse_round_trip_preserves_batched_points() -> None:
    transform = LocalCartoonTransform(
        translation=(2.0, -4.0, 1.5),
        scale=3.0,
    )
    points = np.array([[1.0, 2.0, 3.0], [-5.0, 8.0, 0.0]])

    np.testing.assert_allclose(
        transform.inverse.apply_points(transform.apply_points(points)),
        points,
        atol=1e-12,
    )


def test_composition_matches_sequential_application() -> None:
    first = LocalCartoonTransform(translation=(1.0, 0.0, 0.0), scale=2.0)
    second = LocalCartoonTransform(translation=(0.0, 3.0, 0.0), scale=0.5)
    point = np.array([2.0, 4.0, 6.0])

    combined = first.then(second)

    np.testing.assert_allclose(
        combined.apply_points(point),
        second.apply_points(first.apply_points(point)),
    )
    assert combined.scale == 1.0
    np.testing.assert_allclose(combined.translation, [0.5, 3.0, 0.0])


def test_homogeneous_matrix_matches_point_transformation() -> None:
    transform = LocalCartoonTransform(
        translation=(1.0, 2.0, 3.0),
        scale=2.0,
    )
    point = np.array([4.0, 5.0, 6.0, 1.0])

    np.testing.assert_allclose(
        transform.matrix @ point,
        [9.0, 12.0, 15.0, 1.0],
    )


@pytest.mark.parametrize(
    "translation",
    [(1.0, 2.0), (1.0, np.nan, 3.0), (1.0, np.inf, 3.0)],
)
def test_transform_rejects_invalid_translation(translation) -> None:
    with pytest.raises(ValueError, match="translation"):
        LocalCartoonTransform(translation=translation)


@pytest.mark.parametrize("scale", [0.0, -1.0, np.nan, np.inf])
def test_transform_rejects_invalid_scale(scale) -> None:
    with pytest.raises(ValueError, match="scale"):
        LocalCartoonTransform(scale=scale)


@pytest.mark.parametrize(
    "points",
    [(1.0, 2.0), (1.0, np.nan, 3.0), [[1.0, 2.0], [3.0, 4.0]]],
)
def test_transform_rejects_invalid_cartesian_queries(points) -> None:
    transform = LocalCartoonTransform()
    with pytest.raises(ValueError):
        transform.apply_points(points)


@pytest.mark.parametrize("length", [-1.0, np.nan, np.inf])
def test_transform_rejects_invalid_length(length) -> None:
    with pytest.raises(ValueError, match="length"):
        LocalCartoonTransform().apply_length(length)


def test_composition_requires_transform() -> None:
    with pytest.raises(TypeError, match="LocalCartoonTransform"):
        LocalCartoonTransform().then(object())
