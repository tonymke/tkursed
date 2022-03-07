import math
import os
import sys
import tkinter
from functools import lru_cache

import PIL.Image

import tkursed


class SquareExample(tkursed.SimpleTkursedWindow):
    def __init__(self):
        super().__init__()

        img = tkursed.Image(
            PIL.Image.open(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "images",
                    "cripes.bmp",
                )
            )
        )
        self.sprite = tkursed.PositionedSprite(
            coordinates=update_coords(
                None, self.tkursed.tkursed_state.canvas.dimensions, img.dimensions
            ),
            images=img,
        )

    def handle_tick(self, event: tkinter.Event) -> None:
        if self.tkursed.tick == 1:
            self.tkursed.tkursed_state.canvas.sprites.append(self.sprite)

        update_coords(
            self.sprite.coordinates,
            self.tkursed.tkursed_state.canvas.dimensions,
            self.sprite.active.dimensions,
        )
        self.tkursed.is_dirty = True


def main() -> int:
    SquareExample().mainloop()
    return 0


def update_coords(
    coords: tkursed.Coordinates | None,
    canvas_dim: tkursed.Dimensions,
    sprite_dim: tkursed.Dimensions,
) -> tkursed.Coordinates:
    if coords is None:
        coords = tkursed.Coordinates(1 - sprite_dim.width, 0)
    elif coords.x > canvas_dim.width:
        coords.x = 1 - sprite_dim.width
    else:
        coords.x += 1

    coords.y = int(
        sinusoidal_fn(
            x_pos=float(coords.x),
            amplitude=canvas_dim.height / 10,
            period_mod=sinusoidal_period_length_to_mod(canvas_dim.width / 12),
            horiz_shift=0.0,
            vert_shift=canvas_dim.height / 2.0 - sprite_dim.height / 2.0,
        )
    )
    return coords


@lru_cache(maxsize=4096)
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


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
