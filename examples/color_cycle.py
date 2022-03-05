import itertools
import sys
import tkinter

import tkursed


def create_reducer():
    color_cycle = itertools.cycle(
        [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
        ]
    )
    last = 0

    def reducer(tick: int, state: tkursed.State) -> tkursed.State | None:
        nonlocal color_cycle, last
        if tick - last > 16 or tick == 1:
            last = tick
            state.canvas.background_color = next(color_cycle)
            return state

        return None

    return reducer


class ExampleWindow(tkinter.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("A tcl/tkursed 2D renderer")
        self.resizable(False, False)

        self.tkursed = tkursed.Tkursed(self, reducer=create_reducer())
        self.tkursed.pack(fill=tkinter.NONE, expand=False, anchor=tkinter.CENTER)


def main() -> int:
    ExampleWindow().mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
