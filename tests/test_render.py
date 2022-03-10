from typing import Final, Iterator, TypeVar

import pytest

import tkursed
from tkursed._consts import BPP

T = TypeVar("T")


DEFAULT_CANVAS_PIXEL: Final[tkursed.RGBPixel] = (0, 0, 0)
DEFAULT_CANVAS_PIXEL_RGBA = bytes((*DEFAULT_CANVAS_PIXEL, 255))

DEFAULT_SPRITE_PIXEL: Final[tkursed.RGBPixel] = (255, 255, 255)
DEFAULT_SPRITE_PIXEL_RGBA: Final = bytes((*DEFAULT_SPRITE_PIXEL, 255))


@pytest.fixture
def state() -> tkursed.State:
    state = tkursed.State()
    state.canvas.dimensions = tkursed.Dimensions(5, 5)
    sprite_dim = tkursed.Dimensions(3, 3)
    state.canvas.sprites.append(
        tkursed.PositionedSprite(
            tkursed.Image.from_rgba_pixeldata(
                bytes((*DEFAULT_SPRITE_PIXEL, 255) * sprite_dim.area), sprite_dim
            ),
            tkursed.Coordinates(0, 0),
        )
    )
    return state


def render_state_to_pixeldata_rows(
    state: tkursed.State, renderer: tkursed.Renderer | None = None
) -> Iterator[bytes]:
    if not renderer:
        renderer = tkursed.Renderer()
    renderer.render(state, __is_headless=True)
    buf = bytes(renderer)
    step_size = state.canvas.dimensions.width * BPP // 8
    for i in range(0, len(buf), step_size):
        yield buf[i : i + step_size]


def test_background_render(state: tkursed.State) -> None:
    state.canvas.background_color = (1, 2, 3)
    state.canvas.sprites = []

    unit = tkursed.Renderer()
    unit.render(state, __is_headless=True)

    assert bytes(unit) == bytes((1, 2, 3, 255) * state.canvas.dimensions.area)


def test_sprite_render(state: tkursed.State) -> None:
    sprite_img = state.canvas.sprites[0].active
    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * state.canvas.dimensions.width
    expected_sprite_row = (
        DEFAULT_SPRITE_PIXEL_RGBA * sprite_img.dimensions.width
        + DEFAULT_CANVAS_PIXEL_RGBA
        * (state.canvas.dimensions.width - sprite_img.dimensions.width)
    )
    for i, row in enumerate(render_state_to_pixeldata_rows(state)):
        if i < sprite_img.dimensions.height:
            assert row == expected_sprite_row
        else:
            assert row == expected_bg_row


def test_sprite_frameswap(state: tkursed.State) -> None:
    frame_2_pixel = bytes((2, 2, 2, 255))
    frame_2_dim = tkursed.Dimensions(4, 4)

    sprite = state.canvas.sprites[0]

    sprite.images["1"] = state.canvas.sprites[0].active
    sprite.images["2"] = tkursed.Image.from_rgba_pixeldata(
        frame_2_pixel * frame_2_dim.area,
        frame_2_dim,
    )

    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * state.canvas.dimensions.width

    for frame_key, frame_pixel in (
        ("1", DEFAULT_SPRITE_PIXEL_RGBA),
        ("2", frame_2_pixel),
    ):
        sprite.active_key = frame_key
        image_width = sprite.active.dimensions.width
        expected_frame_row = frame_pixel * image_width + DEFAULT_CANVAS_PIXEL_RGBA * (
            state.canvas.dimensions.width - image_width
        )
        for i, row in enumerate(render_state_to_pixeldata_rows(state)):
            if i < sprite.active.dimensions.height:
                assert row == expected_frame_row
            else:
                assert row == expected_bg_row


def test_sprite_cropping_x_left(state: tkursed.State) -> None:
    sprite = state.canvas.sprites[0]
    sprite.coordinates.x = -1

    canvas_width = state.canvas.dimensions.width
    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * canvas_width
    sprite_effective_width = sprite.active.dimensions.width - abs(sprite.coordinates.x)
    expected_sprite_row = (
        DEFAULT_SPRITE_PIXEL_RGBA * sprite_effective_width
        + DEFAULT_CANVAS_PIXEL_RGBA * (canvas_width - sprite_effective_width)
    )

    for i, row in enumerate(render_state_to_pixeldata_rows(state)):
        if i < sprite.active.dimensions.height:
            assert row == expected_sprite_row
        else:
            assert row == expected_bg_row


def test_sprite_cropping_x_right(state: tkursed.State) -> None:
    canvas_width = state.canvas.dimensions.width

    sprite = state.canvas.sprites[0]
    sprite.coordinates.x = canvas_width - sprite.active.dimensions.width + 1
    sprite_effective_width = canvas_width - sprite.coordinates.x

    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * canvas_width
    expected_sprite_row = (
        DEFAULT_CANVAS_PIXEL_RGBA * (canvas_width - sprite_effective_width)
        + DEFAULT_SPRITE_PIXEL_RGBA * sprite_effective_width
    )

    for i, row in enumerate(render_state_to_pixeldata_rows(state)):
        if i < sprite.active.dimensions.height:
            assert row == expected_sprite_row
        else:
            assert row == expected_bg_row


def test_sprite_cropping_y_up(state: tkursed.State) -> None:
    sprite = state.canvas.sprites[0]
    sprite.coordinates.y = -1
    sprite_dim = sprite.active.dimensions

    canvas_dim = state.canvas.dimensions
    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * canvas_dim.width
    sprite_effective_height = sprite_dim.height - abs(sprite.coordinates.y)
    expected_sprite_row = (
        DEFAULT_SPRITE_PIXEL_RGBA * sprite_dim.width
        + DEFAULT_CANVAS_PIXEL_RGBA * (canvas_dim.width - sprite_dim.width)
    )

    for i, row in enumerate(render_state_to_pixeldata_rows(state)):
        if i < sprite_effective_height:
            assert row == expected_sprite_row
        else:
            assert row == expected_bg_row


def test_sprite_cropping_y_down(state: tkursed.State) -> None:
    canvas_dim = state.canvas.dimensions

    sprite = state.canvas.sprites[0]
    sprite.coordinates.y = canvas_dim.height - sprite.active.dimensions.height + 1
    sprite_dim = sprite.active.dimensions

    expected_bg_row = DEFAULT_CANVAS_PIXEL_RGBA * canvas_dim.width
    expected_sprite_row = (
        DEFAULT_SPRITE_PIXEL_RGBA * sprite_dim.width
        + DEFAULT_CANVAS_PIXEL_RGBA * (canvas_dim.width - sprite_dim.width)
    )

    for i, row in enumerate(render_state_to_pixeldata_rows(state)):
        if i >= sprite.coordinates.y:
            assert row == expected_sprite_row
        else:
            assert row == expected_bg_row


def test_sprite_off_canvas(state: tkursed.State) -> None:
    state.canvas.sprites[0].coordinates = tkursed.Coordinates(6, 6)

    state.canvas.sprites = []

    unit = tkursed.Renderer()
    unit.render(state, __is_headless=True)

    assert bytes(unit) == DEFAULT_CANVAS_PIXEL_RGBA * state.canvas.dimensions.area
