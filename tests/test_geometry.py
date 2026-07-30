import numpy as np
import pytest

from wenu3d.geometry import unit


def test_unit_normalizes_vector() -> None:
    result = unit([3.0, 0.0, 4.0])

    np.testing.assert_allclose(result, [0.6, 0.0, 0.8])
    assert np.linalg.norm(result) == pytest.approx(1.0)


def test_unit_returns_float_array() -> None:
    result = unit([0, 2, 0])

    assert result.dtype.kind == "f"


def test_unit_rejects_zero_vector() -> None:
    with pytest.raises(ValueError, match="zero vector"):
        unit([0.0, 0.0, 0.0])


@pytest.mark.parametrize(
    "vector",
    [
        [],
        [np.nan, 0.0, 1.0],
        [np.inf, 0.0, 1.0],
    ],
)
def test_unit_rejects_empty_or_nonfinite_vector(
    vector: list[float],
) -> None:
    with pytest.raises(ValueError, match="finite"):
        unit(vector)
