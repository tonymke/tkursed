import os
from typing import Any, Callable, TypeVar

import PIL.Image
import pytest
from pytest_lazyfixture import lazy_fixture

import tkursed

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
def sample_image(sample_pil_image: PIL.Image.Image) -> tkursed.Image:
    return tkursed.Image(sample_pil_image)


@pytest.fixture
def sample_image_sprite(sample_image) -> tkursed.Sprite:
    return tkursed.Sprite(sample_image)


@pytest.fixture
def sample_image_positioned_sprite(sample_image) -> tkursed.Sprite:
    return tkursed.PositionedSprite(sample_image, tkursed.Coordinates(0, 0))


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
    "constructor, args",
    [
        (tkursed.Image, lazy_fixture("sample_image_path")),
        (tkursed.Image, lazy_fixture("sample_pil_image")),
        (
            tkursed.Image.from_rgba_pixeldata,
            [bytes((255, 0, 0, 255)) * 50 * 50, tkursed.Dimensions(50, 50)],
        ),
    ],
)
def test_image_construction(
    constructor: Callable[..., tkursed.Image], args: Any | list[Any]
):
    if not isinstance(args, list):
        args = [args]
    assert bytes(constructor(*args).pixeldata) == bytes((255, 0, 0, 255)) * 50 * 50


@pytest.mark.parametrize(
    "input, result_truthiness",
    [
        [(0, 1, 2), False],
        [(-1, 1, 2), True],
        [(256, 1, 2), True],
        [(0, -1, 2), True],
        [(0, 256, 2), True],
        [(0, 0, 256), True],
        [(0, 0, 256), True],
    ],
)
def test_rgbpixel_validation(input: tkursed.RGBPixel, result_truthiness: bool):
    assert bool(tkursed.validate_RGBPixel(input)) is result_truthiness


def test_sprite_construction(sample_image: tkursed.Image):
    unit = tkursed.Sprite(sample_image, name="a_name")
    assert unit.active is sample_image
    assert unit.name == "a_name"

    unit = tkursed.Sprite({"foo": sample_image}, active_key="foo")
    assert sample_image is unit.images["foo"]

    with pytest.raises(ValueError):
        unit = tkursed.Sprite({"foo": sample_image}, active_key="bar")
        assert sample_image is unit.images["foo"]


@pytest.mark.parametrize(
    "state_klasslike, attr_overrides",
    [
        (lambda: tkursed.Dimensions(1, 1), [("width", 0)]),
        (lambda: tkursed.Dimensions(1, 1), [("height", -1)]),
        (lazy_fixture("sample_image_sprite"), [("active_key", "fail"), ("images", {})]),
        (lazy_fixture("sample_image_positioned_sprite"), []),
        (tkursed.Canvas, [("background_color", (-1, 0, 0))]),
        (tkursed.State, [("tick_rate_ms", -1)]),
    ],
)
def test_validation(
    state_klasslike: tkursed.BaseState | Callable[..., tkursed.BaseState],
    attr_overrides: list[tuple[str, Any]],
):
    unit = mutate_instance_attrs(state_klasslike, attr_overrides)
    assert unit.validate().keys() == {k for k, _ in attr_overrides}
