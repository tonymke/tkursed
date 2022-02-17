import math
import os
import sys
import time
from functools import partial, reduce
from itertools import cycle
from typing import Callable, Generator, Iterator, TypeVar

from PIL import Image

from tkursed import Sprite, TkursedRenderer

T = TypeVar("T")


def float_range(
    start: float, end: float, inc: float = 1.0
) -> Generator[float, None, None]:
    if inc == 0:
        raise ValueError("inc cannot be zero", inc)

    if (end > start and inc < 0.0) or (start > end and inc > 0):
        raise ValueError("inc is wrong sign for bounds", inc)

    i = start
    while i < end:
        yield i
        i += inc


class cached_iter(Iterator[T]):
    n_ms: int

    _buf: T
    _iter: Iterator[T]
    _last_time: float = 0.0

    def __init__(self, ttl_ms, iterable: Iterator[T]):
        if ttl_ms < 0:
            raise ValueError("n_ms must be >= 0", ttl_ms)

        self._iter = iterable
        self.n_ms = ttl_ms

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        now = time.time() * 1000
        if now - self._last_time > self.n_ms:
            self._buf = next(self._iter)
            self._last_time = now

        return self._buf


def sinusoidal_fn(
    x_pos: float,
    amplitude: float = 1.0,
    period_mod: float = 1.0,
    horiz_shift: float = 0.0,
    vert_shift: float = 0.0,
) -> float:
    """Feed x coords receive y coords that make pretty nerd picture.
    Give more numbers for different pretty nerd picture.

    https://en.wikipedia.org/wiki/Periodic_function
    y = A*sin(Bx+C)+D
    A: amplitude
    B: period mod (wave period is (2pi)/B)
    C: horiz shift
    D: vert shift
    """
    """
    30 = 2p/B
    30B = 2p
    2p/30
    """
    return amplitude * math.sin(period_mod * x_pos + horiz_shift) + vert_shift


def sinusoidal_period_length_to_mod(period_length: float):
    try:
        return (2 * math.pi) / period_length
    except ZeroDivisionError as ex:
        raise ValueError("period_length cannot be zero") from ex


def main() -> int:
    canvas_width = 800
    canvas_height = 600
    sprite_image = Image.open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "images", "cripes.bmp"
        ),
    )
    sprite_width = sprite_image.width
    square_height = sprite_image.height

    # Read image, convert to RGBA, extract pixeldata and convert pixeldata to bytes
    sprite_image = reduce(
        lambda acc, v: acc + bytes(v),
        sprite_image.convert("RGBA").getdata(),
        bytearray(),
    )

    sprite = Sprite(
        sprite_image,
        sprite_width,
        square_height,
        canvas_width // 2 - sprite_width // 2,
        canvas_height // 2 - square_height // 2,
    )

    def create_callback() -> Callable[[TkursedRenderer, Callable[[], None]], None]:
        periodic_fn = partial(
            sinusoidal_fn,
            amplitude=100.0,
            period_mod=sinusoidal_period_length_to_mod(80),
            horiz_shift=0.0,
            vert_shift=canvas_height / 2.0 - sprite.height / 2.0,
        )
        coord_gen = (
            (int(x), int(y))
            for x, y in cached_iter(
                1000 // 60,
                cycle(
                    (x, periodic_fn(x))
                    for x in float_range(-sprite.width, canvas_width+sprite_width)
                ),
            )
        )

        last_point = (-1, -1)

        def callback(_: TkursedRenderer, draw_fn: Callable[[], None]):
            nonlocal last_point
            sprite.position_x, sprite.position_y = next_point = next(coord_gen)
            if last_point != next_point:
                last_point = next_point
                draw_fn()

        return callback

    TkursedRenderer(
        create_callback(),
        [sprite],
        width=canvas_width,
        height=canvas_height,
    ).run()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
