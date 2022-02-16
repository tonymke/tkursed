import sys

from tkursed import BPP, Sprite, TkursedRenderer


def main() -> int:
    canvas_width = 800
    canvas_height = 600
    square_width = square_height = 50

    TkursedRenderer(
        lambda renderer, draw_fn: draw_fn(),
        [Sprite(
            b"\xFF" * (BPP // 8) * square_width * square_height,
            square_width,
            square_height,
            canvas_width // 2 - square_width // 2,
            canvas_height // 2 - square_height // 2,
        )],
        width=800,
        height=600,
    ).run()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
