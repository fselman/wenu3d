import numpy as np
import pytest

from wenu3d.platforms import CardinalLinesDecoration


def test_cardinal_lines_and_inscriptions_have_expected_geometry() -> None:
    decoration = CardinalLinesDecoration(
        name="directions",
        center=(0.0, 0.0, 0.25),
        east=(2.0, 0.0, 0.0),
        north=(0.2, 3.0, 0.0),
        length=0.1,
    )

    assert tuple(decoration.lines) == ("E", "W", "N", "S")
    assert tuple(decoration.inscriptions) == ("E", "W", "N", "S")
    assert len(decoration.objects) == 8
    np.testing.assert_allclose(decoration.lines["E"].segment.end, [0.1, 0.0, 0.25])
    np.testing.assert_allclose(decoration.lines["N"].segment.end, [0.0, 0.1, 0.25])
    assert decoration.inscriptions["S"].annotation.text == "S"


@pytest.mark.parametrize("length", [0.0, -1.0, np.nan, np.inf])
def test_cardinal_lines_reject_invalid_length(length) -> None:
    with pytest.raises(ValueError, match="length"):
        CardinalLinesDecoration(
            name="directions",
            center=(0.0, 0.0, 0.0),
            east=(1.0, 0.0, 0.0),
            north=(0.0, 1.0, 0.0),
            length=length,
        )
