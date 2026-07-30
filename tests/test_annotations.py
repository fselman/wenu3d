import numpy as np
import pytest

from wenu3d import Annotation, AnnotationStyle


def test_annotation_normalizes_renderer_neutral_values() -> None:
    annotation = Annotation(
        text="  Zenith  ",
        anchor=np.array([0, 0, 1]),
        offset=(0.1, -0.2, 0.3),
        associated_with="  horizontal.zenith  ",
    )

    assert annotation.text == "Zenith"
    assert annotation.anchor == (0.0, 0.0, 1.0)
    assert annotation.offset == (0.1, -0.2, 0.3)
    assert annotation.position == (0.1, -0.2, 1.3)
    assert annotation.associated_with == "horizontal.zenith"
    assert annotation.visible is True
    assert annotation.style == AnnotationStyle()


@pytest.mark.parametrize("text", ["", "   ", None])
def test_annotation_rejects_invalid_text(text) -> None:
    with pytest.raises(ValueError, match="text"):
        Annotation(text=text, anchor=(0, 0, 1))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("anchor", (0, 1)),
        ("anchor", (0, 1, np.inf)),
        ("offset", (0, 1)),
        ("offset", (0, np.nan, 1)),
    ],
)
def test_annotation_rejects_invalid_vectors(
    field_name: str,
    value,
) -> None:
    arguments = {
        "text": "Zenith",
        "anchor": (0, 0, 1),
        field_name: value,
    }

    with pytest.raises(ValueError, match=field_name):
        Annotation(**arguments)


@pytest.mark.parametrize("font_size", [0, -1, 1.5])
def test_annotation_style_rejects_invalid_font_size(font_size) -> None:
    with pytest.raises(ValueError, match="font_size"):
        AnnotationStyle(font_size=font_size)


def test_annotation_rejects_invalid_style_and_association() -> None:
    with pytest.raises(TypeError, match="style"):
        Annotation(text="Zenith", anchor=(0, 0, 1), style={})

    with pytest.raises(ValueError, match="associated_with"):
        Annotation(
            text="Zenith",
            anchor=(0, 0, 1),
            associated_with=" ",
        )

    with pytest.raises(TypeError, match="visible"):
        Annotation(text="Zenith", anchor=(0, 0, 1), visible=1)
