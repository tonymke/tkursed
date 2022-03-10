from typing import Iterator, Sequence, TypeVar

import tkursed

T = TypeVar("T")


def split_sequence_by_step(seq: Sequence[T], step_size=1) -> Iterator[Sequence[T]]:
    if not seq:
        raise ValueError("falsey seq")

    if step_size <= 0:
        raise ValueError("nonpositive step_size")

    for i in range(0, len(seq), step_size):
        yield seq[i : i + step_size]


def test_background_render() -> None:
    unit = tkursed.Renderer()
    unit.render(
        tkursed.State(
            canvas=tkursed.Canvas(
                background_color=(1, 2, 3), dimensions=tkursed.Dimensions(10, 10)
            )
        ),
        __is_headless=True,
    )
    assert bytes(unit) == bytes((1, 2, 3, 255) * 10 * 10)


def test_sprite_render() -> None:
    bg_color = (1, 1, 1)
    bg_pixel = bytes((*bg_color, 255))
    canvas_dim = tkursed.Dimensions(5, 5)
    sprite_pixel = bytes((2, 2, 2, 255))
    sprite_dim = tkursed.Dimensions(3, 3)

    sprite = tkursed.PositionedSprite(
        tkursed.Sprite(
            tkursed.Image.from_rgba_pixeldata(
                bytes(sprite_pixel) * sprite_dim.area,
                sprite_dim,
            )
        ),
        tkursed.Coordinates(0, 0),
    )

    unit = tkursed.Renderer()
    unit.render(
        tkursed.State(
            canvas=tkursed.Canvas(
                background_color=bg_color, dimensions=canvas_dim, sprites=[sprite]
            ),
        ),
        __is_headless=True,
    )
    frame_buffer = bytes(unit)
    assert len(frame_buffer) == canvas_dim.area_rgba_bytes
    for i, row in enumerate(
        split_sequence_by_step(frame_buffer, canvas_dim.width * len(bg_pixel))
    ):
        if i < sprite.active.dimensions.height:
            assert row == sprite_pixel * sprite.active.dimensions.width + bg_pixel * (
                canvas_dim.width - sprite.active.dimensions.width
            )
        else:
            assert row == bg_pixel * canvas_dim.width


def test_sprite_frameswap() -> None:
    bg_color = (0, 0, 0)
    bg_pixel = bytes((*bg_color, 255))
    canvas_dim = tkursed.Dimensions(5, 5)
    sprite_1_pixel = bytes((1, 1, 1, 255))
    sprite_2_pixel = bytes((2, 2, 2, 255))

    sprite_1_dim = tkursed.Dimensions(3, 3)
    sprite_2_dim = tkursed.Dimensions(4, 4)

    sprite = tkursed.PositionedSprite(
        {
            "1": tkursed.Image.from_rgba_pixeldata(
                bytes(sprite_1_pixel) * sprite_1_dim.area,
                sprite_1_dim,
            ),
            "2": tkursed.Image.from_rgba_pixeldata(
                bytes(sprite_2_pixel) * sprite_2_dim.area,
                sprite_2_dim,
            ),
        },
        tkursed.Coordinates(0, 0),
        active_key="1",
    )

    unit = tkursed.Renderer()
    sprite_iter = (
        ("1", sprite_1_pixel, sprite_1_dim),
        ("2", sprite_2_pixel, sprite_2_dim),
    )
    for frame_key, sprite_pixel, sprite_dim in sprite_iter:
        sprite.active_key = frame_key
        unit.render(
            tkursed.State(
                canvas=tkursed.Canvas(
                    background_color=bg_color, dimensions=canvas_dim, sprites=[sprite]
                ),
            ),
            __is_headless=True,
        )
        frame_buffer = bytes(unit)

        for i, row in enumerate(
            split_sequence_by_step(frame_buffer, canvas_dim.width * len(bg_pixel))
        ):
            if i < sprite_dim.height:
                assert row == sprite_pixel * sprite_dim.width + bg_pixel * (
                    canvas_dim.width - sprite_dim.width
                )
            else:
                assert row == bg_pixel * canvas_dim.width
