import itertools
import sys
import tkinter

import tkursed


class ExampleWindow(tkinter.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("A tcl/tkursed 2D renderer")

        self.tkursed = tkursed.Tkursed(self)
        self.tkursed.pack(
            fill=tkinter.BOTH,
            expand=True,
            anchor=tkinter.CENTER,
        )

        self.color_cycle = itertools.cycle(
            [
                (255, 0, 0),
                # (255, 0, 0),
                # (0, 255, 0),
                # (0, 0, 255),
            ]
        )
        self.last = 0
        self.bind(tkursed.EVENT_SEQUENCE_TICK, self.handle_tick)

    def handle_tick(self, event: tkinter.Event) -> None:
        if self.tkursed.tick - self.last > 16 or self.tkursed.tick == 1:
            self.last = self.tkursed.tick
            self.tkursed.tkursed_state.canvas.background_color = next(self.color_cycle)
            self.tkursed.is_dirty = True


def main() -> int:
    ExampleWindow().mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
