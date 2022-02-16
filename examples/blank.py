import sys

from tkursed import TkursedRenderer


def main() -> int:
    TkursedRenderer(lambda renderer, draw_fn: draw_fn()).run()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
