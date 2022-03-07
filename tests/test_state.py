import os
from typing import Any, Callable, TypeVar

import PIL.Image
import pytest
from pytest_lazyfixture import lazy_fixture

from tkursed import _state

T = TypeVar("T")


@pytest.fixture(scope="session")
def sample_image_path() -> str | bytes:
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "red_square_50x50.bmp",
    )


@pytest.fixture(scope="session")
def sample_pil_image(sample_image_path: str | bytes) -> PIL.Image.Image:
    img = PIL.Image.open(sample_image_path)
    img.load()
    return img


@pytest.fixture
def sample_image(sample_pil_image: PIL.Image.Image) -> _state.Image:
    return _state.Image(sample_pil_image)


@pytest.fixture
def sample_image_sprite(sample_image) -> _state.Sprite:
    return _state.Sprite(sample_image)


@pytest.fixture
def sample_image_positioned_sprite(sample_image) -> _state.Sprite:
    return _state.PositionedSprite(sample_image)


def mutate_instance_attrs(
    klasslike: T | Callable[..., T],
    attr_overrides: list[tuple[str, Any]],
) -> T:
    if callable(klasslike):
        result = klasslike()
    else:
        result = klasslike

    for k, v in attr_overrides:
        if callable(v):
            v = v()
        setattr(result, k, v)

    return result


@pytest.mark.parametrize(
    "state_klasslike, attr_overrides",
    [
        (lambda: _state.Dimensions(1, 1), [("width", 0)]),
        (lambda: _state.Dimensions(1, 1), [("height", -1)]),
        (lazy_fixture("sample_image_sprite"), [("active_key", "fail"), ("images", {})]),
        (lazy_fixture("sample_image_positioned_sprite"), []),
        (_state.Canvas, [("background_color", (-1, 0, 0))]),
        (_state.State, [("tick_rate_ms", -1)]),
    ],
)
def test_validation(
    state_klasslike: _state._BaseState | Callable[..., _state._BaseState],
    attr_overrides: list[tuple[str, Any]],
):
    unit = mutate_instance_attrs(state_klasslike, attr_overrides)
    assert unit.validate().keys() == {k for k, _ in attr_overrides}
