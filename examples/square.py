import itertools
import sys
import tkinter

import tkursed


class SquareExample(tkursed.SimpleTkursedWindow):
    def __init__(self) -> None:
        super().__init__()
        self.color_cycle = itertools.cycle(
            [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
            ]
        )
        self.last = 0

    def handle_tick(self, event: tkinter.Event) -> None:
        if self.tkursed.tick - self.last > 16 or self.tkursed.tick == 1:
            self.last = self.tkursed.tick
            self.tkursed.tkursed_state.canvas.background_color = next(self.color_cycle)
            self.tkursed.is_dirty = True


def main() -> int:
    SquareExample().mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
